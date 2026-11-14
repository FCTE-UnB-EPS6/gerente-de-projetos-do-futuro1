"""Índice semântico de risco: quão perto a narrativa de risco está de um "risco âncora" crítico.

Dois motores:
- `tfidf` (padrão): TF-IDF de n-gramas de caracteres. Leve, sem GPU, roda em qualquer servidor.
- `transformer`: Sentence-Transformers multilíngue (extra opcional `nlp`). Captura sinônimos
  e paráfrases, mas baixa um modelo de ~470 MB e pede mais memória.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray
from sklearn.feature_extraction.text import TfidfVectorizer

CRITICAL_ANCHOR = (
    "Falha grave de segurança, atraso crítico, estouro de orçamento, vulnerabilidade, "
    "perda de escopo e dependência de fornecedor sem SLA."
)
TRANSFORMER_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

Backend = Literal["tfidf", "transformer"]


def _cosine(matrix: NDArray[np.float64], anchor: NDArray[np.float64]) -> NDArray[np.float64]:
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(anchor)
    with np.errstate(divide="ignore", invalid="ignore"):
        sims = np.where(norms > 0, matrix @ anchor / norms, 0.0)
    return np.asarray(sims, dtype=np.float64)


class SemanticScorer:
    def __init__(self, backend: Backend = "tfidf", anchor: str = CRITICAL_ANCHOR) -> None:
        self.backend = backend
        self.anchor = anchor
        self._vectorizer: TfidfVectorizer | None = None
        self._encoder: Any = None  # carregado sob demanda; não vai para o arquivo do modelo

    def fit(self, texts: Sequence[str]) -> SemanticScorer:
        if self.backend == "tfidf":
            self._vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True)
            self._vectorizer.fit([*texts, self.anchor])
        return self

    def score(self, texts: Sequence[str]) -> NDArray[np.float64]:
        if not texts:
            return np.zeros(0, dtype=np.float64)
        if self.backend == "transformer":
            encoder = self._load_encoder()
            vectors = np.asarray(encoder.encode([*texts, self.anchor]), dtype=np.float64)
        else:
            if self._vectorizer is None:
                raise RuntimeError("SemanticScorer não treinado: chame fit() antes")
            vectors = np.asarray(
                self._vectorizer.transform([*texts, self.anchor]).toarray(), dtype=np.float64
            )
        sims = _cosine(vectors[:-1], vectors[-1])
        empty = np.array([not t.strip() for t in texts])
        sims[empty] = 0.0
        return sims

    def _load_encoder(self) -> Any:
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - depende do extra opcional
                raise RuntimeError('instale o extra opcional: pip install "gpf[nlp]"') from exc
            self._encoder = SentenceTransformer(TRANSFORMER_MODEL)  # pragma: no cover
        return self._encoder

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        state["_encoder"] = None
        return state
