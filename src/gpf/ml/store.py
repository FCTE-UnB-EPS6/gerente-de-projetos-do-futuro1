"""Gravação e carga do modelo treinado, com verificação de integridade por SHA-256.

O formato joblib usa pickle: carregar um arquivo adulterado executa código arbitrário.
Por isso `load_model` confere o SHA-256 ANTES de desserializar, e a produção só aceita
o hash fixado em `GPF_MODEL_SHA256`.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import tempfile
from pathlib import Path

import joblib

from gpf.ml.predictor import RiskPredictor


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_model(predictor: RiskPredictor, path: Path) -> str:
    """Grava de forma atômica, cria `<arquivo>.sha256` e devolve o hash."""
    if predictor.report is None:
        raise ValueError("só é possível gravar um modelo treinado")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        joblib.dump(predictor, tmp, compress=3)
        os.chmod(tmp, 0o640)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    checksum = sha256_of(path)
    path.with_name(path.name + ".sha256").write_text(f"{checksum}  {path.name}\n", encoding="utf-8")
    return checksum


def load_model(path: Path, expected_sha256: str) -> RiskPredictor:
    if not expected_sha256:
        raise ValueError("informe o SHA-256 esperado do modelo (GPF_MODEL_SHA256)")
    actual = sha256_of(path)
    if not hmac.compare_digest(actual, expected_sha256.strip().lower()):
        raise ValueError("SHA-256 do modelo não confere: arquivo recusado")
    model = joblib.load(path)
    if not isinstance(model, RiskPredictor):
        raise TypeError("o arquivo não contém um RiskPredictor")
    return model
