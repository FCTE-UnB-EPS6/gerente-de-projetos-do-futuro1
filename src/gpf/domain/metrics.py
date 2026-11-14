"""Métricas de monitoramento e predição de risco (PMBOK: desempenho · EVM: SPI/CPI).

Objetos de valor puros. O cálculo preditivo vive em `gpf.ml`; aqui ficam só os dados
e as regras de validação que qualquer modelo precisa respeitar.
"""

from __future__ import annotations

from dataclasses import dataclass, field

FEATURE_NAMES: tuple[str, ...] = (
    "technical_complexity",
    "scope_changes",
    "team_turnover_pct",
    "spi",
    "cpi",
    "technical_debt_hours",
)


@dataclass(frozen=True, slots=True)
class ProjectMetrics:
    """Retrato quantitativo de um projeto num ciclo de acompanhamento."""

    technical_complexity: int
    scope_changes: int
    team_turnover_pct: float
    spi: float
    cpi: float
    technical_debt_hours: float
    risk_narrative: str = ""

    def __post_init__(self) -> None:
        if not 1 <= self.technical_complexity <= 10:
            raise ValueError("technical_complexity deve estar entre 1 e 10")
        if self.scope_changes < 0:
            raise ValueError("scope_changes não pode ser negativo")
        if not 0 <= self.team_turnover_pct <= 100:
            raise ValueError("team_turnover_pct deve estar entre 0 e 100")
        if self.spi <= 0 or self.cpi <= 0:
            raise ValueError("spi e cpi devem ser positivos")
        if self.technical_debt_hours < 0:
            raise ValueError("technical_debt_hours não pode ser negativo")

    def as_vector(self) -> tuple[float, ...]:
        """Valores numéricos na ordem de `FEATURE_NAMES`."""
        return tuple(float(getattr(self, name)) for name in FEATURE_NAMES)


@dataclass(frozen=True, slots=True)
class RiskDriver:
    """Fator que mais pesa na predição (explicabilidade para o comitê)."""

    feature: str
    weight: float


@dataclass(frozen=True, slots=True)
class RiskPrediction:
    """Saída de um modelo preditivo de risco."""

    overrun_probability: float
    contingency_pct: float
    semantic_index: float
    is_anomaly: bool
    drivers: tuple[RiskDriver, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.overrun_probability <= 1.0:
            raise ValueError("overrun_probability deve estar entre 0 e 1")
        if self.contingency_pct < 0:
            raise ValueError("contingency_pct não pode ser negativo")
