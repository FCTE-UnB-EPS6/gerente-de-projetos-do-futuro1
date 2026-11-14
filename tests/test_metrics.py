import pytest

from gpf.domain import FEATURE_NAMES, ProjectMetrics, RiskPrediction


def make_metrics(**kwargs: object) -> ProjectMetrics:
    defaults: dict[str, object] = {
        "technical_complexity": 5,
        "scope_changes": 2,
        "team_turnover_pct": 10.0,
        "spi": 1.0,
        "cpi": 1.0,
        "technical_debt_hours": 40.0,
    }
    defaults.update(kwargs)
    return ProjectMetrics(**defaults)  # type: ignore[arg-type]


def test_vector_follows_feature_order() -> None:
    vector = make_metrics().as_vector()
    assert len(vector) == len(FEATURE_NAMES)
    assert vector[0] == 5.0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("technical_complexity", 11, "technical_complexity"),
        ("scope_changes", -1, "scope_changes"),
        ("team_turnover_pct", 120.0, "team_turnover_pct"),
        ("spi", 0.0, "spi e cpi"),
        ("technical_debt_hours", -5.0, "technical_debt_hours"),
    ],
)
def test_metrics_validation(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        make_metrics(**{field: value})


def test_prediction_validation() -> None:
    with pytest.raises(ValueError, match="overrun_probability"):
        RiskPrediction(1.5, 0.0, 0.0, False)
    with pytest.raises(ValueError, match="contingency_pct"):
        RiskPrediction(0.5, -1.0, 0.0, False)
