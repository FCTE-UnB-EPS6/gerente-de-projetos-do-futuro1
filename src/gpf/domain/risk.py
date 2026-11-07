"""Registro de riscos (PMBOK: domínio de riscos · PRINCE2: prática de risco · PM4R: matriz de riscos)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "baixo"
    MEDIUM = "medio"
    HIGH = "alto"
    CRITICAL = "critico"


@dataclass(frozen=True, slots=True)
class Risk:
    """Um risco avaliado por probabilidade e impacto, ambos na escala de 1 a 5."""

    code: str
    description: str
    probability: int
    impact: int
    owner: str
    response: str = ""

    def __post_init__(self) -> None:
        for name, value in (("probability", self.probability), ("impact", self.impact)):
            if not 1 <= value <= 5:
                raise ValueError(f"{name} deve estar entre 1 e 5 (recebido: {value})")
        if not self.code.strip():
            raise ValueError("code não pode ser vazio")

    @property
    def score(self) -> int:
        return self.probability * self.impact

    @property
    def level(self) -> RiskLevel:
        if self.score >= 20:
            return RiskLevel.CRITICAL
        if self.score >= 12:
            return RiskLevel.HIGH
        if self.score >= 5:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


@dataclass(slots=True)
class RiskRegister:
    risks: dict[str, Risk] = field(default_factory=dict)

    def add(self, risk: Risk) -> None:
        if risk.code in self.risks:
            raise ValueError(f"risco {risk.code} já registrado")
        self.risks[risk.code] = risk

    def ranked(self) -> list[Risk]:
        """Riscos ordenados do maior para o menor score."""
        return sorted(self.risks.values(), key=lambda r: r.score, reverse=True)

    def above(self, level: RiskLevel) -> list[Risk]:
        order = list(RiskLevel)
        return [r for r in self.ranked() if order.index(r.level) >= order.index(level)]
