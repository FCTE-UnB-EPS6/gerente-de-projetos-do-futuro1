from datetime import date

import pytest

from gpf.agents import PredictiveRiskAgent, ProposalStatus
from gpf.domain import Project, ProjectMetrics, RiskDriver, RiskPrediction

METRICS = ProjectMetrics(9, 7, 22.0, 0.84, 0.88, 140.0, "vulnerabilidades críticas")


class FakeModel:
    def __init__(self, prediction: RiskPrediction) -> None:
        self.prediction = prediction

    def predict(self, metrics: ProjectMetrics) -> RiskPrediction:
        return self.prediction


def project(metrics: ProjectMetrics | None = METRICS) -> Project:
    return Project("Plataforma IA", "Reitoria", date(2026, 11, 14), ["benefício"], metrics=metrics)


def test_high_risk_anomalous_project_gets_three_pending_proposals() -> None:
    prediction = RiskPrediction(0.82, 18.4, 0.6, True, (RiskDriver("spi", 0.4), RiskDriver("cpi", 0.3)))
    proposals = PredictiveRiskAgent(FakeModel(prediction)).analyze(project())
    assert [p.summary.split()[0] for p in proposals] == ["Escalar", "Ajustar", "Auditar"]
    assert "82%" in proposals[0].summary
    assert "spi (40%)" in proposals[0].rationale
    assert "18.4%" in proposals[1].summary
    assert all(p.status is ProposalStatus.PENDING for p in proposals)


def test_healthy_project_gets_no_proposal() -> None:
    prediction = RiskPrediction(0.1, 2.0, 0.1, False)
    assert PredictiveRiskAgent(FakeModel(prediction)).analyze(project()) == []


def test_project_without_metrics_is_skipped() -> None:
    prediction = RiskPrediction(0.9, 30.0, 0.9, True)
    assert PredictiveRiskAgent(FakeModel(prediction)).analyze(project(None)) == []


def test_threshold_validation() -> None:
    with pytest.raises(ValueError, match="threshold"):
        PredictiveRiskAgent(FakeModel(RiskPrediction(0.1, 0, 0, False)), threshold=1.5)
