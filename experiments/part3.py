"""Part III (extra credit): DCF versus OFDMA with K = 1, 2, 4, 8 at N = 20.

Produces required plots 7-9: network throughput, 95th-percentile delay, and
Jain's fairness index versus aggregate load.

Run with: python -m experiments.part3
"""

import matplotlib.pyplot as plt

from macsim import config, plotting
from macsim.dcf import simulate_dcf
from macsim.ofdma import simulate_ofdma

from .common import averaged, series, write_csv

METRICS = ["throughput_mbps", "collision_probability", "mean_delay_ms", "p95_delay_ms", "jain_fairness"]
METHODS = ["DCF"] + [f"OFDMA K={k}" for k in config.OFDMA_RUS]


def run(n: int = config.OFDMA_COMPARISON_N) -> list[dict]:
    rows = []
    for load in config.AGGREGATE_LOADS:
        runs = {"DCF": averaged(simulate_dcf, num_stations=n, arrival_rate=load / n)}
        for k in config.OFDMA_RUS:
            runs[f"OFDMA K={k}"] = averaged(simulate_ofdma, num_stations=n, arrival_rate=load / n, num_rus=k)
        for method, m in runs.items():
            rows.append({"method": method, "N": n, "load": load} | {key: m[key] for key in METRICS})
    return rows


def plot(rows: list[dict], key: str, ylabel: str, name: str, log: bool = False) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    for method in METHODS:
        ax.plot(config.AGGREGATE_LOADS, series(rows, key, method=method), label=method, **plotting.STYLES[method])
    ax.set_xlabel(r"Aggregate load $\Lambda$ (frames/sec)")
    ax.set_xticks(config.AGGREGATE_LOADS)
    ax.set_ylabel(ylabel)
    if log:
        ax.set_yscale("log")
    ax.legend(fontsize=11)
    plotting.save(fig, name)


def main() -> None:
    plotting.apply_style()
    rows = run()
    write_csv("part3", rows)
    n = config.OFDMA_COMPARISON_N
    plot(rows, "throughput_mbps", rf"$T_\mathrm{{network}}$ (Mbps), $N$ = {n}", "part3_throughput")
    plot(rows, "p95_delay_ms", rf"95th-percentile packet delay (ms), $N$ = {n}", "part3_p95_delay", log=True)
    plot(rows, "jain_fairness", rf"Jain's fairness index $J$, $N$ = {n}", "part3_fairness")


if __name__ == "__main__":
    main()
