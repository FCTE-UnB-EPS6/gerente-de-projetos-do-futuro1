"""Agente determinístico de referência: monitora riscos e estágios fora da tolerância.

Serve de modelo para agentes baseados em LLM, que devem seguir o mesmo contrato.
"""

from __future__ import annotations

from gpf.agents.base import Agent, AgentProposal
from gpf.domain.project import Project
from gpf.domain.risk import RiskLevel


class RiskMonitorAgent(Agent):
    name = "monitor-de-riscos"

    def analyze(self, project: Project) -> list[AgentProposal]:
        proposals: list[AgentProposal] = []
        for risk in project.risks.above(RiskLevel.HIGH):
            if not risk.response:
                proposals.append(
                    AgentProposal(
                        agent=self.name,
                        summary=f"Definir resposta para o risco {risk.code} ({risk.level})",
                        rationale=f"Score {risk.score} sem plano de resposta. Responsável: {risk.owner}.",
                    )
                )
        for stage in project.stages_in_exception:
            proposals.append(
                AgentProposal(
                    agent=self.name,
                    summary=f"Emitir relatório de exceção para o estágio '{stage.name}'",
                    rationale=(
                        f"Desvio de {stage.deviation_pct:.1f}% acima da tolerância de "
                        f"{stage.tolerance_pct:.0f}%."
                    ),
                )
            )
        return proposals
