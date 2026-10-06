"""Shared matplotlib style so the same protocol looks the same in every figure."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

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


def apply_style() -> None:
    """Set global rcParams (line width, marker size, font sizes, grid)."""
    plt.rcParams.update(
        {
            "lines.linewidth": 2,
            "lines.markersize": 8,
            "font.size": 13,
            "axes.grid": True,
            "figure.autolayout": True,
            "savefig.dpi": 200,
        }
    )


def save(fig, name: str) -> None:
    """Save a figure into FIGURES_DIR."""
    FIGURES_DIR.mkdir(exist_ok=True)
    fig.savefig(FIGURES_DIR / f"{name}.png")
    plt.close(fig)
