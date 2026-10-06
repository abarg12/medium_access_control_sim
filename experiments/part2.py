"""Part II: dense DCF in a single collision domain.

Produces required plots 3-6: network throughput, collision probability,
mean/95th-percentile delay, and Jain's fairness index versus N, for each
aggregate load.

Run with: python -m experiments.part2
"""

import matplotlib.pyplot as plt

from macsim import config, plotting
from macsim.dcf import simulate_dcf

from .common import averaged, series, write_csv

METRICS = ["throughput_mbps", "collision_probability", "mean_delay_ms", "p95_delay_ms", "jain_fairness"]


def run() -> list[dict]:
    rows = []
    for load in config.AGGREGATE_LOADS:
        for n in config.DENSE_N:
            m = averaged(simulate_dcf, num_stations=n, arrival_rate=load / n)
            rows.append({"load": load, "N": n} | {key: m[key] for key in METRICS})
    return rows


def plot_vs_n(ax, rows: list[dict], key: str, ylabel: str) -> None:
    for load in config.AGGREGATE_LOADS:
        label = rf"$\Lambda$ = {load} frames/sec"
        ax.plot(config.DENSE_N, series(rows, key, load=load), label=label, **plotting.LOAD_STYLES[load])
    ax.set_xlabel("Number of stations $N$")
    ax.set_xticks(config.DENSE_N)
    ax.set_ylabel(ylabel)
    ax.legend()


def main() -> None:
    plotting.apply_style()
    rows = run()
    write_csv("part2", rows)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    plot_vs_n(ax, rows, "throughput_mbps", r"$T_\mathrm{network}$ (Mbps)")
    ax.set_ylim(bottom=0)
    plotting.save(fig, "part2_throughput")

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    plot_vs_n(ax, rows, "collision_probability", r"$P_\mathrm{collision}$")
    ax.set_ylim(bottom=0)
    plotting.save(fig, "part2_collision")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    plot_vs_n(axes[0], rows, "mean_delay_ms", "Mean packet delay (ms)")
    plot_vs_n(axes[1], rows, "p95_delay_ms", "95th-percentile packet delay (ms)")
    axes[0].set_yscale("log")
    axes[1].tick_params(labelleft=True)
    plotting.save(fig, "part2_delay")

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    plot_vs_n(ax, rows, "jain_fairness", "Jain's fairness index $J$")
    ax.set_ylim(0, 1.05)
    plotting.save(fig, "part2_fairness")


if __name__ == "__main__":
    main()
