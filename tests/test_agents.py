from datetime import date

import pytest

from gpf.agents import AgentProposal, ProposalStatus, RiskMonitorAgent
from gpf.domain import Project, Risk, Stage


def test_risk_monitor_flags_unanswered_high_risks_and_exceptions() -> None:
    project = Project("Piloto", "Coordenação", date(2026, 11, 9), ["benefício"])
    project.risks.add(Risk("R1", "sem resposta", 4, 4, "ana"))
    project.risks.add(Risk("R2", "com resposta", 5, 5, "bia", response="mitigar"))
    project.risks.add(Risk("R3", "baixo", 1, 1, "caio"))
    project.stages.append(Stage("Estágio 1", budget=100, spent=130))

    proposals = RiskMonitorAgent().analyze(project)

    assert len(proposals) == 2
    assert "R1" in proposals[0].summary
    assert "exceção" in proposals[1].summary
    assert all(p.status is ProposalStatus.PENDING for p in proposals)


def test_proposal_requires_human_decision_once() -> None:
    proposal = AgentProposal("a", "s", "r")
    with pytest.raises(ValueError, match="revisor humano"):
        proposal.approve("  ")
    proposal.approve("prof")
    assert proposal.status is ProposalStatus.APPROVED
    assert proposal.reviewer == "prof"
    with pytest.raises(ValueError, match="já decidida"):
        proposal.reject("prof")


def test_reject() -> None:
    proposal = AgentProposal("a", "s", "r")
    proposal.reject("prof")
    assert proposal.status is ProposalStatus.REJECTED
