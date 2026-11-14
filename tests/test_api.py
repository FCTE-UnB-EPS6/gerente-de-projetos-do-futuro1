import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from gpf.api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_assess_risk() -> None:
    payload = {"code": "R1", "description": "x", "probability": 4, "impact": 5, "owner": "ana"}
    response = client.post("/risks/assess", json=payload)
    assert response.status_code == 200
    assert response.json()["level"] == "critico"


def test_assess_risk_validates_scale() -> None:
    payload = {"code": "R1", "description": "x", "probability": 9, "impact": 5, "owner": "ana"}
    assert client.post("/risks/assess", json=payload).status_code == 422


# --- /ml/predict -----------------------------------------------------------------

from gpf.api import ml_routes  # noqa: E402
from gpf.domain import ProjectMetrics, RiskDriver, RiskPrediction  # noqa: E402

METRICS_PAYLOAD = {
    "project_name": "PRJ-01",
    "technical_complexity": 9,
    "scope_changes": 7,
    "team_turnover_pct": 22.0,
    "spi": 0.84,
    "cpi": 0.88,
    "technical_debt_hours": 140.0,
    "risk_narrative": "vulnerabilidades críticas no pipeline",
}


class FakeModel:
    def predict(self, metrics: ProjectMetrics) -> RiskPrediction:
        return RiskPrediction(0.9, 20.0, 0.5, False, (RiskDriver("spi", 0.5),))


@pytest.fixture
def fake_model():  # type: ignore[no-untyped-def]
    app.dependency_overrides[ml_routes.get_risk_model] = FakeModel
    yield
    app.dependency_overrides.clear()


@pytest.mark.usefixtures("fake_model")
def test_predict_returns_pending_proposals() -> None:
    body = client.post("/ml/predict", json=METRICS_PAYLOAD).json()
    assert body["overrun_probability"] == 0.9
    assert body["drivers"][0]["feature"] == "spi"
    assert [p["status"] for p in body["proposals"]] == ["pendente", "pendente"]


@pytest.mark.usefixtures("fake_model")
def test_predict_requires_token_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GPF_API_TOKEN", "segredo-de-teste")
    assert client.post("/ml/predict", json=METRICS_PAYLOAD).status_code == 401
    headers = {"Authorization": "Bearer segredo-de-teste"}
    assert client.post("/ml/predict", json=METRICS_PAYLOAD, headers=headers).status_code == 200


@pytest.mark.usefixtures("fake_model")
def test_predict_validates_metrics() -> None:
    payload = {**METRICS_PAYLOAD, "spi": 0}
    assert client.post("/ml/predict", json=payload).status_code == 422


def test_predict_without_model_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GPF_MODEL_PATH", raising=False)
    ml_routes._load_from_env.cache_clear()
    response = client.post("/ml/predict", json=METRICS_PAYLOAD)
    assert response.status_code == 503
    assert "GPF_MODEL_PATH" in response.json()["detail"]


def test_predict_with_real_model_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    pytest.importorskip("sklearn")
    from gpf.ml import RiskPredictor, generate_history, save_model

    predictor = RiskPredictor(engine="sklearn")
    predictor.fit(generate_history(120))
    path = tmp_path / "m.joblib"
    monkeypatch.setenv("GPF_MODEL_PATH", str(path))
    monkeypatch.setenv("GPF_MODEL_SHA256", save_model(predictor, path))
    ml_routes._load_from_env.cache_clear()
    try:
        assert client.post("/ml/predict", json=METRICS_PAYLOAD).status_code == 200
    finally:
        ml_routes._load_from_env.cache_clear()
