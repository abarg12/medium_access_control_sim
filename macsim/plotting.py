"""Shared matplotlib style so the same protocol looks the same in every figure."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from . import config  # noqa: E402

FIGURES_DIR = Path(__file__).resolve().parent.parent / "figures"

# Plot kwargs per series; distinct markers and line styles for grayscale.
STYLES = {
    "DCF": dict(color="C0", linestyle="-", marker="o"),
    "DCF + RTS/CTS": dict(color="C1", linestyle="--", marker="s"),
    "OFDMA K=1": dict(color="C2", linestyle=":", marker="^"),
    "OFDMA K=2": dict(color="C3", linestyle="-.", marker="v"),
    "OFDMA K=4": dict(color="C4", linestyle="--", marker="D"),
    "OFDMA K=8": dict(color="C5", linestyle=":", marker="x"),
}

# Dense-DCF figures plot one line per aggregate load.
LOAD_STYLES = {
    300: dict(color="C0", linestyle="-", marker="o"),
    800: dict(color="C1", linestyle="--", marker="s"),
}

# Part I figures that compare the two stations use one fixed color per station.
STATION_STYLES = {
    "Station A": dict(color="navy", linestyle="-", marker="o"),
    "Station B": dict(color="crimson", linestyle="--", marker="s"),
}

def apply_style() -> None:
    """Set global rcParams (line width, marker size, font sizes, grid)."""
    plt.rcParams.update(
        {
            "lines.linewidth": 2,
            "lines.markersize": 8,
            "font.size": 16,
            "legend.fontsize": 13,
            "axes.grid": True,
            "figure.autolayout": True,
            "savefig.dpi": 200,
        }
    )


def saturation_index(throughput, offered) -> int | None:
    """Index of the first point where throughput < SATURATION_FRACTION * offered load."""
    for k, (t, o) in enumerate(zip(throughput, offered)):
        if t < config.SATURATION_FRACTION * o:
            return k
    return None


def mark_saturation(ax, x, curves: dict, offered, styles: dict = STYLES) -> None:
    """Label where each throughput curve saturates relative to the offered load.

    `curves` maps a series label to its throughput values. A label takes the
    color of its curve, or dark gray when several curves saturate at the same x.
    """
    points = {}
    for label, y in curves.items():
        k = saturation_index(y, offered)
        if k is not None:
            points.setdefault(x[k], []).append(label)
    for xs, labels in points.items():
        alone = len(labels) == 1 and len(curves) > 1
        color = styles[labels[0]]["color"] if alone else "0.2"
        ax.axvline(xs, color=color, linestyle=":", linewidth=1.5)
        ax.text(
            xs, 0.97, "saturated", color=color, fontsize=12, rotation=90,
            ha="right", va="top", transform=ax.get_xaxis_transform(),
        )


def save(fig, name: str) -> None:
    """Save a figure into FIGURES_DIR."""
    FIGURES_DIR.mkdir(exist_ok=True)
    fig.savefig(FIGURES_DIR / f"{name}.png")
    plt.close(fig)
