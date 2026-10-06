"""Performance metrics (Section 4.3)."""

from dataclasses import dataclass, field

import numpy as np

from . import config


@dataclass
class Results:
    """Raw per-station counters from one simulation run."""

    sim_time_slots: int
    successes: list[int] = field(default_factory=list)
    attempts: list[int] = field(default_factory=list)
    collisions: list[int] = field(default_factory=list)
    delays: list[list[float]] = field(default_factory=list)  # slots, per station
    trace: list[tuple] = field(default_factory=list)  # (slot, node, event), if requested


def station_throughputs_mbps(results: Results) -> list[float]:
    """T_i for each station, in Mbps."""
    sim_time_s = results.sim_time_slots * config.SLOT_DURATION_S
    return [n * config.DATA_FRAME_BITS / sim_time_s / 1e6 for n in results.successes]


def network_throughput_mbps(results: Results) -> float:
    """T_network = sum of T_i (Eq. 2)."""
    return sum(station_throughputs_mbps(results))


def collision_probability(results: Results) -> float:
    """Collided attempts / total transmission attempts (Eq. 3)."""
    attempts = sum(results.attempts)
    return sum(results.collisions) / attempts if attempts else 0.0


def _all_delays_ms(results: Results) -> np.ndarray:
    delays = np.concatenate([np.asarray(d, dtype=float) for d in results.delays])
    return delays * config.SLOT_DURATION_S * 1e3


def mean_delay_ms(results: Results) -> float:
    delays = _all_delays_ms(results)
    return float(delays.mean()) if delays.size else float("nan")


def p95_delay_ms(results: Results) -> float:
    delays = _all_delays_ms(results)
    return float(np.percentile(delays, 95)) if delays.size else float("nan")


def jain_fairness(throughputs: list[float]) -> float:
    """J = (sum T_i)^2 / (N * sum T_i^2) (Eq. 5)."""
    t = np.asarray(throughputs, dtype=float)
    sum_sq = float((t**2).sum())
    return float(t.sum() ** 2 / (t.size * sum_sq)) if sum_sq else float("nan")


def summarize(results: Results) -> dict:
    """All metrics for one run."""
    throughputs = station_throughputs_mbps(results)
    return {
        "station_throughputs_mbps": throughputs,
        "throughput_mbps": sum(throughputs),
        "collision_probability": collision_probability(results),
        "mean_delay_ms": mean_delay_ms(results),
        "p95_delay_ms": p95_delay_ms(results),
        "jain_fairness": jain_fairness(throughputs),
    }
