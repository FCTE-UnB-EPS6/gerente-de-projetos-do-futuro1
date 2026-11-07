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
