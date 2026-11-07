"""API HTTP do GPF."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from gpf import __version__
from gpf.domain.risk import Risk

app = FastAPI(
    title="Gerente de Projetos do Futuro",
    version=__version__,
    description="Gerência de projetos AI-First — PMBOK 8, PRINCE2 7 e PM4R.",
)


class RiskIn(BaseModel):
    code: str = Field(min_length=1)
    description: str
    probability: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    owner: str
    response: str = ""


class RiskOut(RiskIn):
    score: int
    level: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/risks/assess", response_model=RiskOut)
def assess_risk(payload: RiskIn) -> RiskOut:
    risk = Risk(**payload.model_dump())
    return RiskOut(**payload.model_dump(), score=risk.score, level=risk.level.value)
