"""`gpf-train`: treina os modelos de risco e grava o arquivo para a API.

Exemplos:
    gpf-train --synthetic 400 --out models/gpf-risk.joblib
    gpf-train --csv dados/historico.csv --out models/gpf-risk.joblib
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from gpf.ml.dataset import load_csv
from gpf.ml.predictor import RiskPredictor
from gpf.ml.store import save_model
from gpf.ml.synthetic import generate_history


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gpf-train", description="Treina os modelos de risco do GPF.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--csv", type=Path, help="base histórica real (veja gpf.ml.dataset)")
    source.add_argument("--synthetic", type=int, metavar="N", help="gera N projetos sintéticos")
    parser.add_argument("--out", type=Path, required=True, help="arquivo .joblib de saída")
    parser.add_argument("--engine", choices=["auto", "xgboost", "sklearn"], default="auto")
    parser.add_argument("--semantic", choices=["tfidf", "transformer"], default="tfidf")
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    history = load_csv(args.csv) if args.csv else generate_history(args.synthetic, seed=args.seed)
    predictor = RiskPredictor(engine=args.engine, semantic_backend=args.semantic, seed=args.seed)
    report = predictor.fit(history)
    checksum = save_model(predictor, args.out)
    print(json.dumps({"model": str(args.out), "sha256": checksum, **asdict(report)}, indent=2))
    print(f"\nDefina na produção: GPF_MODEL_SHA256={checksum}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
