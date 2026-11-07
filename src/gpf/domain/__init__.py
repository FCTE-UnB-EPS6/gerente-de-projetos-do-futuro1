"""Domínio puro de gerência de projetos (sem dependências de framework)."""

from gpf.domain.project import Project, ProjectPhase, Stage
from gpf.domain.risk import Risk, RiskLevel, RiskRegister

__all__ = ["Project", "ProjectPhase", "Risk", "RiskLevel", "RiskRegister", "Stage"]
