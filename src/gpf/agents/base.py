"""Contrato dos agentes: eles propõem, o humano aprova (human-in-the-loop)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum

from gpf.domain.project import Project


class ProposalStatus(StrEnum):
    PENDING = "pendente"
    APPROVED = "aprovada"
    REJECTED = "rejeitada"


@dataclass(slots=True)
class AgentProposal:
    agent: str
    summary: str
    rationale: str
    status: ProposalStatus = ProposalStatus.PENDING
    reviewer: str | None = None

    def approve(self, reviewer: str) -> None:
        self._decide(reviewer, ProposalStatus.APPROVED)

    def reject(self, reviewer: str) -> None:
        self._decide(reviewer, ProposalStatus.REJECTED)

    def _decide(self, reviewer: str, status: ProposalStatus) -> None:
        if self.status is not ProposalStatus.PENDING:
            raise ValueError("proposta já decidida")
        if not reviewer.strip():
            raise ValueError("decisão exige um revisor humano identificado")
        self.status = status
        self.reviewer = reviewer


class Agent(ABC):
    """Agentes analisam um projeto e devolvem propostas. Nunca alteram o projeto diretamente."""

    name: str

    @abstractmethod
    def analyze(self, project: Project) -> list[AgentProposal]: ...
