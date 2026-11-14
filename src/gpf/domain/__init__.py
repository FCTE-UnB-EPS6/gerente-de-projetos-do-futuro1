"""Domínio puro de gerência de projetos (sem dependências de framework)."""

from gpf.domain.metrics import FEATURE_NAMES, ProjectMetrics, RiskDriver, RiskPrediction
from gpf.domain.project import Project, ProjectPhase, Stage
from gpf.domain.risk import Risk, RiskLevel, RiskRegister

__all__ = [
    "FEATURE_NAMES",
    "Project",
    "ProjectMetrics",
    "ProjectPhase",
    "Risk",
    "RiskDriver",
    "RiskLevel",
    "RiskPrediction",
    "RiskRegister",
    "Stage",
]
