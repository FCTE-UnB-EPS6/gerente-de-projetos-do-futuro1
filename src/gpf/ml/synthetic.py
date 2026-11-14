"""Base histórica sintética para treinar e demonstrar os modelos sem dados reais.

Reproduz a regra latente do notebook de referência (EVM, volatilidade de escopo,
rotatividade e dívida técnica). Substitua por dados reais do PMO, Jira ou GitHub
assim que existirem (veja `gpf.ml.dataset.load_csv`).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from gpf.domain.metrics import ProjectMetrics

RISK_NARRATIVES: tuple[str, ...] = (
    "Atraso na homologação de segurança e vulnerabilidades críticas no pipeline CI/CD.",
    "Alta rotatividade da equipe técnica e perda de conhecimento de arquitetura.",
    "Mudanças frequentes de escopo solicitadas pelo cliente sem aditivo de prazo.",
    "Dependência de API de fornecedor terceiro sem SLA garantido.",
    "Subdimensionamento de infraestrutura GPU para inferência dos modelos de IA.",
    "Cronograma estável, requisitos bem definidos e entregas dentro da meta.",
    "Equipe experiente, cobertura de testes automatizados acima de 85%.",
    "Baixa complexidade técnica e fornecedores homologados sem gargalos.",
)


@dataclass(frozen=True, slots=True)
class History:
    """Projetos encerrados com seus desfechos."""

    metrics: list[ProjectMetrics]
    overrun: NDArray[np.int_]
    budget_deviation_pct: NDArray[np.float64]


def generate_history(n_projects: int = 400, seed: int = 42) -> History:
    if n_projects < 20:
        raise ValueError("n_projects deve ser pelo menos 20")
    rng = np.random.default_rng(seed)
    complexity = rng.integers(1, 11, n_projects)
    scope = rng.poisson(4, n_projects)
    turnover = rng.uniform(0, 35, n_projects)
    spi = np.clip(rng.normal(0.95, 0.12, n_projects), 0.3, 1.6)
    cpi = np.clip(rng.normal(0.96, 0.11, n_projects), 0.3, 1.6)
    debt = rng.gamma(2.0, 40.0, n_projects)
    narrative_idx = rng.integers(0, len(RISK_NARRATIVES), n_projects)

    latent = (
        0.35 * complexity
        + 0.45 * scope
        + 0.08 * turnover
        - 4.5 * spi
        - 3.8 * cpi
        + 0.015 * debt
        + 0.9 * (narrative_idx < 5)  # narrativas negativas pesam no desfecho
        + rng.normal(0, 0.8, n_projects)
    )
    overrun = (latent > np.percentile(latent, 65)).astype(np.int_)
    deviation = np.maximum(0.0, latent * 4.2 + rng.normal(2, 3, n_projects)).astype(np.float64)

    metrics = [
        ProjectMetrics(
            technical_complexity=int(complexity[i]),
            scope_changes=int(scope[i]),
            team_turnover_pct=float(turnover[i]),
            spi=float(spi[i]),
            cpi=float(cpi[i]),
            technical_debt_hours=float(debt[i]),
            risk_narrative=RISK_NARRATIVES[int(narrative_idx[i])],
        )
        for i in range(n_projects)
    ]
    return History(metrics=metrics, overrun=overrun, budget_deviation_pct=deviation)
