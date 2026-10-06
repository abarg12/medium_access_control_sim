"""Poisson traffic generation (Appendix 1)."""

import numpy as np

from . import config


def poisson_arrivals(rate: float, sim_time_slots: int, rng: np.random.Generator) -> np.ndarray:
    """Return frame arrival times, in slots, for one station.

    Inter-arrival times are X = -(1/rate) * ln(1 - U) with U ~ Uniform(0, 1).
    Times are fractional; a frame becomes available at the next slot boundary.
    """
    horizon_s = sim_time_slots * config.SLOT_DURATION_S
    chunk = int(rate * horizon_s * 1.2) + 20
    times = np.empty(0)
    last = 0.0
    while last < horizon_s:
        inter_arrivals = -np.log(1 - rng.random(chunk)) / rate
        times = np.concatenate([times, last + np.cumsum(inter_arrivals)])
        last = times[-1]
    return times[times < horizon_s] / config.SLOT_DURATION_S
