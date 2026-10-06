"""Part I: two-station CSMA/CA with and without RTS/CTS.

Produces required plots 1 and 2: per-station throughput and collision
probability versus lambda, for both topologies.

Run with: python -m experiments.part1
"""

import matplotlib.pyplot as plt

from macsim import config, plotting
from macsim.dcf import Topology, simulate_dcf

from .common import averaged, series, write_csv

TOPOLOGIES = {
    Topology.SINGLE_DOMAIN: "Single collision domain",
    Topology.HIDDEN_TERMINALS: "Hidden terminals",
}
PROTOCOLS = {"DCF": False, "DCF + RTS/CTS": True}


def run() -> list[dict]:
    rows = []
    for topology in TOPOLOGIES:
        for protocol, rts_cts in PROTOCOLS.items():
            for rate in config.PART1_ARRIVAL_RATES:
                m = averaged(simulate_dcf, num_stations=2, arrival_rate=rate, topology=topology, rts_cts=rts_cts)
                rows.append(
                    {
                        "topology": topology.value,
                        "protocol": protocol,
                        "lambda": rate,
                        "throughput_A_mbps": m["station_throughputs_mbps"][0],
                        "throughput_B_mbps": m["station_throughputs_mbps"][1],
                        "collision_probability": m["collision_probability"],
                    }
                )
    return rows


def plot(rows: list[dict], key: str, ylabel: str, name: str) -> None:
    """One panel per topology, one line per protocol."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for ax, (topology, title) in zip(axes, TOPOLOGIES.items()):
        for protocol in PROTOCOLS:
            y = series(rows, key, topology=topology.value, protocol=protocol)
            ax.plot(config.PART1_ARRIVAL_RATES, y, label=protocol, **plotting.STYLES[protocol])
        ax.set_title(title)
        ax.set_xlabel(r"$\lambda$ (frames/sec)")
        ax.legend()
    axes[0].set_ylabel(ylabel)
    axes[0].set_ylim(bottom=0)
    plotting.save(fig, name)


def main() -> None:
    plotting.apply_style()
    rows = run()
    write_csv("part1", rows)
    plot(rows, "throughput_A_mbps", "Throughput of A (Mbps)", "part1_throughput_A")
    plot(rows, "throughput_B_mbps", "Throughput of B (Mbps)", "part1_throughput_B")
    plot(rows, "collision_probability", "Collision probability", "part1_collision")


if __name__ == "__main__":
    main()
