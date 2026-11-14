"""Agente de risco preditivo: transforma a saída dos modelos de ML em propostas para o humano.

Não depende de scikit-learn: recebe qualquer objeto que cumpra o protocolo `RiskModel`.
"""

from __future__ import annotations

from typing import Protocol

from gpf.agents.base import Agent, AgentProposal
from gpf.domain.metrics import ProjectMetrics, RiskPrediction
from gpf.domain.project import Project


class RiskModel(Protocol):
    def predict(self, metrics: ProjectMetrics) -> RiskPrediction: ...


class PredictiveRiskAgent(Agent):
    name = "risco-preditivo"

    def __init__(self, model: RiskModel, threshold: float = 0.5, contingency_floor_pct: float = 5.0) -> None:
        if not 0 < threshold < 1:
            raise ValueError("threshold deve estar entre 0 e 1")
        self.model = model
        self.threshold = threshold
        self.contingency_floor_pct = contingency_floor_pct

    def analyze(self, project: Project) -> list[AgentProposal]:
        if project.metrics is None:
            return []
        return self.proposals_for(self.model.predict(project.metrics), project.name)

    def proposals_for(self, prediction: RiskPrediction, project_name: str) -> list[AgentProposal]:
        drivers = ", ".join(f"{d.feature} ({d.weight:.0%})" for d in prediction.drivers) or "n/d"
        proposals: list[AgentProposal] = []
        if prediction.overrun_probability >= self.threshold:
            proposals.append(
                AgentProposal(
                    agent=self.name,
                    summary=(
                        f"Escalar '{project_name}': {prediction.overrun_probability:.0%} de probabilidade "
                        "de estouro crítico de prazo/custo no próximo ciclo"
                    ),
                    rationale=f"Limiar de alerta: {self.threshold:.0%}. Principais fatores: {drivers}.",
                )
            )
        if prediction.contingency_pct >= self.contingency_floor_pct:
            proposals.append(
                AgentProposal(
                    agent=self.name,
                    summary=(
                        f"Ajustar a reserva de contingência para {prediction.contingency_pct:.1f}% "
                        "do orçamento"
                    ),
                    rationale=(
                        "Estimativa do Random Forest a partir do desvio real de projetos históricos "
                        "semelhantes, no lugar de um percentual fixo."
                    ),
                )
            )
        if prediction.is_anomaly:
            proposals.append(
                AgentProposal(
                    agent=self.name,
                    summary=f"Auditar '{project_name}': perfil atípico em relação à base histórica",
                    rationale=(
                        "O DBSCAN não encontrou projetos semelhantes; a predição tem menor confiança "
                        "e o caso pede análise humana."
                    ),
                )
            )
        return proposals
