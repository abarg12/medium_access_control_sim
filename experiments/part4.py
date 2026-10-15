"""Extra: DCF versus OFDMA as the number of stations N grows (Section 7).

For N = 5, 10, 20, 40 and each aggregate load, compares DCF with OFDMA
K = 2, 4, 8. Produces four figures (one panel per aggregate load):
network throughput, collision probability, 95th-percentile delay, and
Jain's fairness index, each versus N.

Run with: python -m experiments.part4
"""

import matplotlib.pyplot as plt

from macsim import config, plotting
from macsim.dcf import simulate_dcf
from macsim.ofdma import simulate_ofdma

from .common import averaged, series, write_csv

COMPARE_N = [5, 10, 20, 40]
OFDMA_KS = [2, 4, 8]
METHODS = ["DCF"] + [f"OFDMA K={k}" for k in OFDMA_KS]
METRICS = ["throughput_mbps", "collision_probability", "mean_delay_ms", "p95_delay_ms", "jain_fairness"]


def run() -> list[dict]:
    rows = []
    for load in config.AGGREGATE_LOADS:
        for n in COMPARE_N:
            runs = {"DCF": averaged(simulate_dcf, num_stations=n, arrival_rate=load / n)}
            for k in OFDMA_KS:
                runs[f"OFDMA K={k}"] = averaged(simulate_ofdma, num_stations=n, arrival_rate=load / n, num_rus=k)
            for method, m in runs.items():
                rows.append({"method": method, "N": n, "load": load} | {key: m[key] for key in METRICS})
    return rows


def plot(rows: list[dict], key: str, ylabel: str, name: str, log: bool = False, ylim: tuple | None = None) -> None:
    """One panel per aggregate load, one line per access method."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, load in zip(axes, config.AGGREGATE_LOADS):
        for method in METHODS:
            ax.plot(COMPARE_N, series(rows, key, method=method, load=load), label=method, **plotting.STYLES[method])
        ax.set_title(rf"$\Lambda$ = {load} frames/sec")
        ax.set_xlabel("Number of stations $N$")
        ax.set_xticks(COMPARE_N)
        ax.legend(fontsize=11)
    axes[0].set_ylabel(ylabel)
    if log:
        axes[0].set_yscale("log")
    if ylim is not None:
        axes[0].set_ylim(*ylim)
    plotting.save(fig, name)


def main() -> None:
    plotting.apply_style()
    rows = run()
    write_csv("part4", rows)
    plot(rows, "throughput_mbps", r"$T_\mathrm{network}$ (Mbps)", "part4_throughput", ylim=(0, None))
    plot(rows, "collision_probability", r"$P_\mathrm{collision}$", "part4_collision", ylim=(0, None))
    plot(rows, "p95_delay_ms", "95th-percentile packet delay (ms)", "part4_p95_delay", log=True)
    plot(rows, "jain_fairness", "Jain's fairness index $J$", "part4_fairness")


if __name__ == "__main__":
    main()