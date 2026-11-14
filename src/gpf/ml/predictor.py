"""Modelos preditivos de risco de projeto.

- Classificador de estouro crítico de prazo/custo: gradient boosting. Usa XGBoost quando o
  extra `xgboost` está instalado; senão, o `HistGradientBoostingClassifier` do scikit-learn,
  da mesma família de algoritmos, sem dependência extra.
- Regressor de desvio de orçamento (base para a reserva de contingência): Random Forest.
- Detector de anomalias: DBSCAN (veja `gpf.ml.anomaly`).
- Explicabilidade: importância por permutação, medida no conjunto de validação.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, roc_auc_score
from sklearn.model_selection import train_test_split

from gpf.domain.metrics import FEATURE_NAMES, ProjectMetrics, RiskDriver, RiskPrediction
from gpf.ml.anomaly import AnomalyDetector
from gpf.ml.semantic import Backend, SemanticScorer
from gpf.ml.synthetic import History

ALL_FEATURES: tuple[str, ...] = (*FEATURE_NAMES, "semantic_index")
Engine = Literal["auto", "xgboost", "sklearn"]


def _make_classifier(engine: Engine, seed: int) -> tuple[Any, str]:
    if engine in ("auto", "xgboost"):
        try:
            from xgboost import XGBClassifier
        except ImportError:
            if engine == "xgboost":
                raise RuntimeError('XGBoost não instalado: pip install "gpf[xgboost]"') from None
        else:  # pragma: no cover - depende do extra opcional
            clf = XGBClassifier(
                n_estimators=150,
                max_depth=4,
                learning_rate=0.05,
                subsample=0.8,
                random_state=seed,
                eval_metric="logloss",
            )
            return clf, "xgboost"
    clf = HistGradientBoostingClassifier(max_depth=4, learning_rate=0.05, max_iter=200, random_state=seed)
    return clf, "sklearn-hist-gradient-boosting"


@dataclass(slots=True)
class TrainingReport:
    engine: str
    n_projects: int
    overrun_rate: float
    roc_auc: float
    contingency_mae_pp: float
    n_anomalies_in_history: int
    trained_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"))


class RiskPredictor:
    """Treina e aplica os modelos. Implementa o protocolo `gpf.agents.RiskModel`."""

    def __init__(self, engine: Engine = "auto", semantic_backend: Backend = "tfidf", seed: int = 42) -> None:
        self.engine = engine
        self.seed = seed
        self.semantic = SemanticScorer(semantic_backend)
        self.anomaly = AnomalyDetector()
        self._classifier: Any = None
        self._regressor: RandomForestRegressor | None = None
        self.drivers: tuple[RiskDriver, ...] = ()
        self.report: TrainingReport | None = None

    def _matrix(self, metrics: Sequence[ProjectMetrics]) -> NDArray[np.float64]:
        base = np.asarray([m.as_vector() for m in metrics], dtype=np.float64)
        semantic = self.semantic.score([m.risk_narrative for m in metrics])
        return np.column_stack([base, semantic])

    def fit(self, history: History) -> TrainingReport:
        if len(set(history.overrun.tolist())) < 2:
            raise ValueError("a base precisa ter projetos com e sem estouro crítico")
        self.semantic.fit([m.risk_narrative for m in history.metrics])
        x = self._matrix(history.metrics)
        x_tr, x_te, yc_tr, yc_te, yr_tr, yr_te = train_test_split(
            x,
            history.overrun,
            history.budget_deviation_pct,
            test_size=0.25,
            random_state=self.seed,
            stratify=history.overrun,
        )
        self._classifier, engine_name = _make_classifier(self.engine, self.seed)
        self._classifier.fit(x_tr, yc_tr)
        self._regressor = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=self.seed)
        self._regressor.fit(x_tr, yr_tr)

        proba = self._classifier.predict_proba(x_te)[:, 1]
        importance = permutation_importance(
            self._classifier, x_te, yc_te, scoring="roc_auc", n_repeats=5, random_state=self.seed
        )
        weights = np.clip(importance.importances_mean, 0, None)
        total = float(weights.sum()) or 1.0
        ranked = sorted(zip(ALL_FEATURES, weights / total, strict=True), key=lambda p: p[1], reverse=True)
        self.drivers = tuple(RiskDriver(name, round(float(w), 4)) for name, w in ranked)

        n_anomalies = self.anomaly.fit(x)
        self.report = TrainingReport(
            engine=engine_name,
            n_projects=len(history.metrics),
            overrun_rate=round(float(history.overrun.mean()), 4),
            roc_auc=round(float(roc_auc_score(yc_te, proba)), 4),
            contingency_mae_pp=round(float(mean_absolute_error(yr_te, self._regressor.predict(x_te))), 3),
            n_anomalies_in_history=n_anomalies,
        )
        return self.report

    def predict(self, metrics: ProjectMetrics) -> RiskPrediction:
        if self._classifier is None or self._regressor is None:
            raise RuntimeError("RiskPredictor não treinado: chame fit() antes")
        x = self._matrix([metrics])
        return RiskPrediction(
            overrun_probability=float(np.clip(self._classifier.predict_proba(x)[0, 1], 0.0, 1.0)),
            contingency_pct=max(0.0, float(self._regressor.predict(x)[0])),
            semantic_index=float(x[0, -1]),
            is_anomaly=self.anomaly.is_anomaly(x[0]),
            drivers=self.drivers[:3],
        )
