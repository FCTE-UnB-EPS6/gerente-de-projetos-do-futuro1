"""Projeto, fases do ciclo de vida e estágios de gerenciamento (PRINCE2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum

from gpf.domain.risk import RiskRegister


class ProjectPhase(StrEnum):
    """Fases do ciclo de vida, em ordem."""

    INITIATING = "iniciacao"
    PLANNING = "planejamento"
    EXECUTING = "execucao"
    MONITORING = "monitoramento"
    CLOSING = "encerramento"


_TRANSITIONS: dict[ProjectPhase, set[ProjectPhase]] = {
    ProjectPhase.INITIATING: {ProjectPhase.PLANNING, ProjectPhase.CLOSING},
    ProjectPhase.PLANNING: {ProjectPhase.EXECUTING, ProjectPhase.CLOSING},
    ProjectPhase.EXECUTING: {ProjectPhase.MONITORING, ProjectPhase.CLOSING},
    ProjectPhase.MONITORING: {ProjectPhase.EXECUTING, ProjectPhase.PLANNING, ProjectPhase.CLOSING},
    ProjectPhase.CLOSING: set(),
}


@dataclass(slots=True)
class Stage:
    """Estágio de gerenciamento (PRINCE2), com orçamento e tolerância."""

    name: str
    budget: float
    spent: float = 0.0
    tolerance_pct: float = 10.0

    def __post_init__(self) -> None:
        if self.budget <= 0:
            raise ValueError("budget deve ser positivo")

    @property
    def deviation_pct(self) -> float:
        return (self.spent - self.budget) / self.budget * 100

    @property
    def exceeds_tolerance(self) -> bool:
        """Gestão por exceção: estourar a tolerância escala a decisão para o nível acima."""
        return self.deviation_pct > self.tolerance_pct


@dataclass(slots=True)
class Project:
    name: str
    sponsor: str
    start: date
    expected_benefits: list[str] = field(default_factory=list)
    phase: ProjectPhase = ProjectPhase.INITIATING
    stages: list[Stage] = field(default_factory=list)
    risks: RiskRegister = field(default_factory=RiskRegister)

    def advance_to(self, target: ProjectPhase) -> None:
        if target not in _TRANSITIONS[self.phase]:
            raise ValueError(f"transição inválida: {self.phase} → {target}")
        if target is ProjectPhase.PLANNING and not self.expected_benefits:
            raise ValueError("business case sem benefícios esperados: justificativa não demonstrada")
        self.phase = target

    @property
    def stages_in_exception(self) -> list[Stage]:
        return [s for s in self.stages if s.exceeds_tolerance]
