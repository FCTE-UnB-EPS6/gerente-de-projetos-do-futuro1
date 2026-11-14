"""Rotas de risco preditivo (`/ml/*`).

Configuração por variáveis de ambiente:
- GPF_MODEL_PATH: caminho do arquivo gerado por `gpf-train`
- GPF_MODEL_SHA256: hash esperado do arquivo (obrigatório; protege contra modelo adulterado)
- GPF_API_TOKEN: se definido, as rotas exigem `Authorization: Bearer <token>`
- GPF_RISK_THRESHOLD: limiar de alerta do agente (padrão 0.5)
"""

from __future__ import annotations

import hmac
import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from gpf.agents.predictive_risk import PredictiveRiskAgent, RiskModel
from gpf.domain.metrics import ProjectMetrics

router = APIRouter(prefix="/ml", tags=["risco preditivo"])


def require_token(authorization: Annotated[str | None, Header()] = None) -> None:
    expected = os.environ.get("GPF_API_TOKEN", "")
    if not expected:
        return
    supplied = (authorization or "").removeprefix("Bearer ").strip()
    if not hmac.compare_digest(supplied.encode(), expected.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token inválido", {"WWW-Authenticate": "Bearer"})


@lru_cache(maxsize=1)
def _load_from_env() -> Any:
    path = os.environ.get("GPF_MODEL_PATH", "")
    if not path:
        raise RuntimeError("GPF_MODEL_PATH não definido")
    from gpf.ml.store import load_model  # import tardio: o extra `ml` é opcional

    return load_model(Path(path), os.environ.get("GPF_MODEL_SHA256", ""))


def get_risk_model() -> RiskModel:
    try:
        model: RiskModel = _load_from_env()
    except (RuntimeError, ValueError, TypeError, OSError, ImportError) as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"modelo indisponível: {exc}") from exc
    return model


class MetricsIn(BaseModel):
    project_name: str = Field(min_length=1, max_length=200)
    technical_complexity: int = Field(ge=1, le=10)
    scope_changes: int = Field(ge=0)
    team_turnover_pct: float = Field(ge=0, le=100)
    spi: float = Field(gt=0)
    cpi: float = Field(gt=0)
    technical_debt_hours: float = Field(ge=0)
    risk_narrative: str = Field(default="", max_length=5000)


class DriverOut(BaseModel):
    feature: str
    weight: float


class ProposalOut(BaseModel):
    agent: str
    summary: str
    rationale: str
    status: str


class PredictionOut(BaseModel):
    overrun_probability: float
    contingency_pct: float
    semantic_index: float
    is_anomaly: bool
    drivers: list[DriverOut]
    proposals: list[ProposalOut]


@router.post("/predict", response_model=PredictionOut, dependencies=[Depends(require_token)])
def predict(payload: MetricsIn, model: Annotated[RiskModel, Depends(get_risk_model)]) -> PredictionOut:
    metrics = ProjectMetrics(**payload.model_dump(exclude={"project_name"}))
    prediction = model.predict(metrics)
    agent = PredictiveRiskAgent(model, threshold=float(os.environ.get("GPF_RISK_THRESHOLD", "0.5")))
    proposals = agent.proposals_for(prediction, payload.project_name)
    return PredictionOut(
        overrun_probability=prediction.overrun_probability,
        contingency_pct=prediction.contingency_pct,
        semantic_index=prediction.semantic_index,
        is_anomaly=prediction.is_anomaly,
        drivers=[DriverOut(feature=d.feature, weight=d.weight) for d in prediction.drivers],
        proposals=[
            ProposalOut(agent=p.agent, summary=p.summary, rationale=p.rationale, status=p.status.value)
            for p in proposals
        ],
    )
