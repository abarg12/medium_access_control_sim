"""Helpers shared by the experiment scripts."""

import csv
from pathlib import Path

import numpy as np

from macsim import config
from macsim.metrics import summarize

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def averaged(simulate, runs: int = config.NUM_RUNS, **kwargs) -> dict:
    """Run `simulate` with `runs` different seeds and average every metric."""
    rows = [summarize(simulate(seed=config.DEFAULT_SEED + r, **kwargs)) for r in range(runs)]
    return {key: np.mean([row[key] for row in rows], axis=0) for key in rows[0]}


def write_csv(name: str, rows: list[dict]) -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_DIR / f"{name}.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def series(rows: list[dict], key: str, **match) -> list:
    """Values of `key` from the rows whose fields equal `match`, in row order."""
    return [row[key] for row in rows if all(row[k] == v for k, v in match.items())]
