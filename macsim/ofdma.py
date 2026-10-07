"""Simplified Wi-Fi 6 uplink OFDMA with round-robin scheduling (Part III).

Each transmission opportunity lasts
    overhead + K * DATA_SLOTS + SIFS + ACK
slots: the AP announces the schedule, the selected stations send one frame
each in parallel at rate R / K, and the AP acknowledges them together.
"""

import math

import numpy as np

from . import config
from .metrics import Results
from .station import Station
from .traffic import poisson_arrivals


def schedule_round_robin(nonempty: list[bool], next_station: int, num_rus: int) -> list[int]:
    """Select up to num_rus stations with nonempty queues, starting at next_station."""
    n = len(nonempty)
    order = ((next_station + k) % n for k in range(n))
    return [i for i in order if nonempty[i]][:num_rus]


def simulate_ofdma(
    num_stations: int,
    arrival_rate: float,
    num_rus: int,
    seed: int | None = None,
    arrivals: list | None = None,
    sim_time_slots: int = config.SIM_TIME_SLOTS,
    overhead_slots: int = config.OFDMA_OVERHEAD_SLOTS,
) -> Results:
    """Run one OFDMA simulation. arrival_rate is the per-station rate in frames/sec."""
    rng = np.random.default_rng(seed)
    if arrivals is None:
        arrivals = [poisson_arrivals(arrival_rate, sim_time_slots, rng) for _ in range(num_stations)]
    pending = sorted((float(a), i) for i, times in enumerate(arrivals) for a in times)
    stations = [Station(i) for i in range(num_stations)]
    duration = overhead_slots + num_rus * config.DATA_SLOTS + config.SIFS_SLOTS + config.ACK_SLOTS

    t = 0
    next_station = 0
    p = 0  # index of the next arrival not yet queued
    while True:
        while p < len(pending) and pending[p][0] <= t:
            arrival, i = pending[p]
            stations[i].queue.append(arrival)
            p += 1
        nonempty = [bool(st.queue) for st in stations]
        if not any(nonempty):
            if p == len(pending):
                break
            t = math.ceil(pending[p][0])  # idle: jump to the next arrival
            continue
        end = t + duration
        if end > sim_time_slots:
            break
        chosen = schedule_round_robin(nonempty, next_station, num_rus)
        for i in chosen:
            stations[i].attempts += 1
            stations[i].on_success(end)
        next_station = (chosen[-1] + 1) % num_stations
        t = end

    return Results(
        sim_time_slots=sim_time_slots,
        successes=[st.successes for st in stations],
        attempts=[st.attempts for st in stations],
        collisions=[0] * num_stations,
        delays=[st.delays for st in stations],
        backoffs=[st.backoff_draws for st in stations],
    )
