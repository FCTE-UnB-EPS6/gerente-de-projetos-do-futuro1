import csv
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from gpf.domain import ProjectMetrics
from gpf.ml import RiskPredictor, generate_history, load_model, save_model
from gpf.ml.cli import main as train_main
from gpf.ml.dataset import REQUIRED_COLUMNS, load_csv
from gpf.ml.semantic import SemanticScorer

RISKY = ProjectMetrics(
    9,
    7,
    22.0,
    0.84,
    0.88,
    140.0,
    "Atraso na homologação de segurança e vulnerabilidades críticas no pipeline CI/CD.",
)
HEALTHY = ProjectMetrics(
    3, 1, 5.0, 1.02, 1.01, 15.0, "Cronograma estável, requisitos bem definidos e entregas dentro da meta."
)


@pytest.fixture(scope="module")
def predictor() -> RiskPredictor:
    model = RiskPredictor(engine="sklearn")
    model.fit(generate_history(400))
    return model


def test_training_report_is_useful(predictor: RiskPredictor) -> None:
    report = predictor.report
    assert report is not None
    assert report.engine == "sklearn-hist-gradient-boosting"
    assert report.roc_auc > 0.8
    assert 0.3 < report.overrun_rate < 0.4
    assert len(predictor.drivers) == 7


def test_predictions_separate_risky_from_healthy(predictor: RiskPredictor) -> None:
    risky, healthy = predictor.predict(RISKY), predictor.predict(HEALTHY)
    assert risky.overrun_probability > 0.7 > 0.3 > healthy.overrun_probability
    assert risky.contingency_pct > healthy.contingency_pct
    assert risky.semantic_index > healthy.semantic_index
    assert len(risky.drivers) == 3


def test_extreme_project_is_anomalous(predictor: RiskPredictor) -> None:
    extreme = ProjectMetrics(10, 40, 95.0, 0.3, 0.3, 2000.0, "")
    assert predictor.predict(extreme).is_anomaly
    assert not predictor.predict(HEALTHY).is_anomaly


def test_untrained_predictor_refuses() -> None:
    with pytest.raises(RuntimeError, match="não treinado"):
        RiskPredictor(engine="sklearn").predict(HEALTHY)
    with pytest.raises(RuntimeError, match="não treinado"):
        SemanticScorer().score(["texto"])


def test_semantic_scorer_handles_empty_text() -> None:
    scorer = SemanticScorer().fit(["falha grave de segurança"])
    assert scorer.score([]).size == 0
    assert scorer.score([""])[0] == 0.0


def test_history_requires_both_classes() -> None:
    history = generate_history(40)
    history.overrun[:] = 0
    with pytest.raises(ValueError, match="com e sem"):
        RiskPredictor(engine="sklearn").fit(history)
    with pytest.raises(ValueError, match="pelo menos 20"):
        generate_history(5)


def test_save_and_load_checks_integrity(predictor: RiskPredictor, tmp_path: Path) -> None:
    path = tmp_path / "modelo.joblib"
    checksum = save_model(predictor, path)
    assert (tmp_path / "modelo.joblib.sha256").read_text().startswith(checksum)
    loaded = load_model(path, checksum.upper())
    assert loaded.predict(RISKY).overrun_probability == pytest.approx(
        predictor.predict(RISKY).overrun_probability
    )
    with pytest.raises(ValueError, match="não confere"):
        load_model(path, "0" * 64)
    with pytest.raises(ValueError, match="GPF_MODEL_SHA256"):
        load_model(path, "")
    with pytest.raises(ValueError, match="treinado"):
        save_model(RiskPredictor(), tmp_path / "x.joblib")


def test_load_rejects_foreign_object(tmp_path: Path) -> None:
    import joblib

    from gpf.ml.store import sha256_of

    path = tmp_path / "outro.joblib"
    joblib.dump({"not": "a model"}, path)
    with pytest.raises(TypeError, match="RiskPredictor"):
        load_model(path, sha256_of(path))


def write_csv(path: Path, rows: int, overrun: str = "1") -> None:
    history = generate_history(max(rows, 20))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[*REQUIRED_COLUMNS, "risk_narrative"])
        writer.writeheader()
        for i in range(rows):
            m = history.metrics[i]
            writer.writerow(
                {
                    "technical_complexity": m.technical_complexity,
                    "scope_changes": m.scope_changes,
                    "team_turnover_pct": m.team_turnover_pct,
                    "spi": m.spi,
                    "cpi": m.cpi,
                    "technical_debt_hours": m.technical_debt_hours,
                    "overrun": int(history.overrun[i]) if overrun == "1" else overrun,
                    "budget_deviation_pct": history.budget_deviation_pct[i],
                    "risk_narrative": m.risk_narrative,
                }
            )


def test_load_csv(tmp_path: Path) -> None:
    good = tmp_path / "ok.csv"
    write_csv(good, 60)
    assert len(load_csv(good).metrics) == 60

    small = tmp_path / "pequeno.csv"
    write_csv(small, 10)
    with pytest.raises(ValueError, match="pelo menos 20"):
        load_csv(small)

    bad = tmp_path / "ruim.csv"
    write_csv(bad, 25, overrun="7")
    with pytest.raises(ValueError, match="linha 2"):
        load_csv(bad)

    missing = tmp_path / "faltando.csv"
    missing.write_text("spi,cpi\n1,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="colunas ausentes"):
        load_csv(missing)


def test_cli_trains_from_synthetic_and_csv(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "m.joblib"
    assert train_main(["--synthetic", "120", "--engine", "sklearn", "--out", str(out)]) == 0
    assert "GPF_MODEL_SHA256=" in capsys.readouterr().out
    data = tmp_path / "h.csv"
    write_csv(data, 120)
    assert train_main(["--csv", str(data), "--engine", "sklearn", "--out", str(out)]) == 0


def test_xgboost_engine_requires_extra() -> None:
    try:
        import xgboost  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError, match="XGBoost não instalado"):
            RiskPredictor(engine="xgboost").fit(generate_history(60))
    else:  # pragma: no cover - ambiente com o extra instalado
        assert RiskPredictor(engine="xgboost").fit(generate_history(60)).engine == "xgboost"
