"""Detecção de anomalias com DBSCAN.

O DBSCAN não tem `predict`. Para um projeto novo, consideramos anomalia quando ele fica a
mais de `eps` (no espaço padronizado) de todas as amostras-núcleo dos agrupamentos da base.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    def __init__(self, eps: float = 2.1, min_samples: int = 8) -> None:
        self.eps = eps
        self.min_samples = min_samples
        self._scaler = StandardScaler()
        self._core: NDArray[np.float64] = np.empty((0, 0))

    def fit(self, x: NDArray[np.float64]) -> int:
        """Treina e devolve quantos projetos históricos ficaram fora de qualquer agrupamento."""
        scaled = self._scaler.fit_transform(x)
        model = DBSCAN(eps=self.eps, min_samples=self.min_samples).fit(scaled)
        self._core = np.asarray(scaled[model.core_sample_indices_], dtype=np.float64)
        return int((model.labels_ == -1).sum())

    def is_anomaly(self, row: NDArray[np.float64]) -> bool:
        if self._core.size == 0:
            return True  # sem agrupamento denso na base: tudo é atípico
        scaled = self._scaler.transform(row.reshape(1, -1))[0]
        distance = float(np.min(np.linalg.norm(self._core - scaled, axis=1)))
        return distance > self.eps
