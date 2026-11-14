"""Leitura de base histórica real em CSV (exportada do PMO, Jira, GitHub ou planilha)."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from gpf.domain.metrics import FEATURE_NAMES, ProjectMetrics
from gpf.ml.synthetic import History

REQUIRED_COLUMNS: tuple[str, ...] = (*FEATURE_NAMES, "overrun", "budget_deviation_pct")


def load_csv(path: Path) -> History:
    """Colunas obrigatórias: as de `FEATURE_NAMES`, `overrun` (0/1) e `budget_deviation_pct`.

    A coluna `risk_narrative` é opcional.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"colunas ausentes no CSV: {', '.join(missing)}")
        metrics: list[ProjectMetrics] = []
        overrun: list[int] = []
        deviation: list[float] = []
        for line, row in enumerate(reader, start=2):
            try:
                metrics.append(
                    ProjectMetrics(
                        technical_complexity=int(row["technical_complexity"]),
                        scope_changes=int(row["scope_changes"]),
                        team_turnover_pct=float(row["team_turnover_pct"]),
                        spi=float(row["spi"]),
                        cpi=float(row["cpi"]),
                        technical_debt_hours=float(row["technical_debt_hours"]),
                        risk_narrative=row.get("risk_narrative") or "",
                    )
                )
                flag = int(row["overrun"])
                if flag not in (0, 1):
                    raise ValueError("overrun deve ser 0 ou 1")
                overrun.append(flag)
                deviation.append(float(row["budget_deviation_pct"]))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"linha {line} inválida: {exc}") from exc
    if len(metrics) < 20:
        raise ValueError("a base precisa de pelo menos 20 projetos encerrados")
    return History(
        metrics=metrics,
        overrun=np.asarray(overrun, dtype=np.int_),
        budget_deviation_pct=np.asarray(deviation, dtype=np.float64),
    )
