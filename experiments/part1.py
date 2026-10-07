"""Part I: two-station CSMA/CA with and without RTS/CTS.

Produces required plots 1 and 2: per-station throughput and collision
probability versus lambda, for both topologies. Also produces a station A
versus station B throughput comparison and mean packet delay versus lambda.

Run with: python -m experiments.part1
"""

import matplotlib.pyplot as plt

from macsim import config, plotting
from macsim.dcf import Topology, simulate_dcf
from macsim.metrics import offered_load_mbps

from .common import averaged, series, write_csv

TOPOLOGIES = {
    Topology.SINGLE_DOMAIN: "Single collision domain",
    Topology.HIDDEN_TERMINALS: "Hidden terminals",
}
PROTOCOLS = {"DCF": False, "DCF + RTS/CTS": True}
STATIONS = ["A", "B"]
RATES = config.PART1_ARRIVAL_RATES
OFFERED = [offered_load_mbps(rate) for rate in RATES]  # per station


def run() -> list[dict]:
    rows = []
    for topology in TOPOLOGIES:
        for protocol, rts_cts in PROTOCOLS.items():
            for rate in RATES:
                m = averaged(simulate_dcf, num_stations=2, arrival_rate=rate, topology=topology, rts_cts=rts_cts)
                row = {"topology": topology.value, "protocol": protocol, "lambda": rate}
                for i, s in enumerate(STATIONS):
                    row[f"throughput_{s}_mbps"] = m["station_throughputs_mbps"][i]
                row["collision_probability"] = m["collision_probability"]
                for i, s in enumerate(STATIONS):
                    row[f"collision_probability_{s}"] = m["station_collision_probabilities"][i]
                for i, s in enumerate(STATIONS):
                    row[f"mean_backoff_{s}_slots"] = m["station_mean_backoffs"][i]
                row["mean_delay_ms"] = m["mean_delay_ms"]
                rows.append(row)
    return rows


def throughput_ylim(rows: list[dict]) -> float:
    """Common upper y limit for the throughput figures, with headroom for the saturation labels."""
    return 1.3 * max(row[f"throughput_{s}_mbps"] for row in rows for s in STATIONS)


def plot(rows: list[dict], key: str, ylabel: str, name: str, saturation: bool = False, log: bool = False) -> None:
    """One panel per topology, one line per protocol."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, (topology, title) in zip(axes, TOPOLOGIES.items()):
        curves = {p: series(rows, key, topology=topology.value, protocol=p) for p in PROTOCOLS}
        for protocol, y in curves.items():
            ax.plot(RATES, y, label=protocol, **plotting.STYLES[protocol])
        if saturation:
            plotting.mark_saturation(ax, RATES, curves, OFFERED)
        ax.set_title(title)
        ax.set_xlabel(r"$\lambda$ (frames/sec)")
        ax.legend(loc="lower right" if saturation else "best")
    axes[0].set_ylabel(ylabel)
    if log:
        axes[0].set_yscale("log")
    elif saturation:
        axes[0].set_ylim(0, throughput_ylim(rows))
    else:
        axes[0].set_ylim(bottom=0)
    plotting.save(fig, name)


def plot_stations(rows: list[dict], name: str) -> None:
    """One panel per protocol and topology, one line per station."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 9), sharex=True, sharey=True)
    for row_axes, protocol in zip(axes, PROTOCOLS):
        for ax, (topology, title) in zip(row_axes, TOPOLOGIES.items()):
            curves = {
                f"Station {s}": series(rows, f"throughput_{s}_mbps", topology=topology.value, protocol=protocol)
                for s in STATIONS
            }
            for label, y in curves.items():
                ax.plot(RATES, y, label=label, **plotting.STATION_STYLES[label])
            plotting.mark_saturation(ax, RATES, curves, OFFERED, plotting.STATION_STYLES)
            ax.set_title(f"{title}, {protocol}", fontsize=15)
            ax.legend(loc="lower right")
    for ax in axes[-1]:
        ax.set_xlabel(r"$\lambda$ (frames/sec)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Throughput (Mbps)")
    axes[0, 0].set_ylim(0, throughput_ylim(rows))
    plotting.save(fig, name)


def main() -> None:
    plotting.apply_style()
    rows = run()
    write_csv("part1", rows)
    plot(rows, "throughput_A_mbps", "Throughput of A (Mbps)", "part1_throughput_A", saturation=True)
    plot(rows, "throughput_B_mbps", "Throughput of B (Mbps)", "part1_throughput_B", saturation=True)
    plot_stations(rows, "part1_throughput_stations")
    plot(rows, "collision_probability", "Collision probability", "part1_collision")
    plot(rows, "mean_delay_ms", "Mean packet delay (ms)", "part1_delay", log=True)


if __name__ == "__main__":
    main()
