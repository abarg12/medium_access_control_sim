"""Unit tests for traffic generation and metric calculations."""

import numpy as np
import pytest

from macsim import config
from macsim.dcf import Topology, simulate_dcf
from macsim.metrics import (
    Results,
    collision_probability,
    jain_fairness,
    mean_delay_ms,
    network_throughput_mbps,
    station_throughputs_mbps,
)
from macsim.ofdma import simulate_ofdma
from macsim.traffic import poisson_arrivals


def test_poisson_mean_interarrival():
    arrivals = poisson_arrivals(100, config.SIM_TIME_SLOTS, np.random.default_rng(1))
    assert np.all(np.diff(arrivals) > 0)
    assert arrivals[-1] < config.SIM_TIME_SLOTS
    assert np.diff(arrivals).mean() == pytest.approx(1000, rel=0.1)  # slots


def test_jain_fairness_equal_shares_is_one():
    assert jain_fairness([2.0, 2.0, 2.0, 2.0]) == pytest.approx(1.0)
    assert jain_fairness([4.0, 0.0, 0.0, 0.0]) == pytest.approx(0.25)


def test_collision_probability():
    r = Results(sim_time_slots=1000, attempts=[6, 4], collisions=[1, 1])
    assert collision_probability(r) == pytest.approx(0.2)


@pytest.mark.parametrize("topology", list(Topology))
@pytest.mark.parametrize("rts_cts", [False, True])
def test_throughput_does_not_exceed_channel_capacity(topology, rts_cts):
    r = simulate_dcf(2, 1000, topology=topology, rts_cts=rts_cts, seed=0, sim_time_slots=100_000)
    assert 0 < network_throughput_mbps(r) < config.CHANNEL_RATE_BPS / 1e6
    assert all(a >= s + c for a, s, c in zip(r.attempts, r.successes, r.collisions))


def test_light_load_delivers_offered_traffic():
    r = simulate_dcf(5, 20, seed=0)
    offered_mbps = 5 * 20 * config.DATA_FRAME_BITS / 1e6
    assert network_throughput_mbps(r) == pytest.approx(offered_mbps, rel=0.1)


@pytest.mark.parametrize("topology", list(Topology))
@pytest.mark.parametrize("rts_cts", [False, True])
def test_unsaturated_stations_each_deliver_offered_load(topology, rts_cts):
    # lambda = 100 frames/sec * 12,000 bits = 1.2 Mbps per station, far below capacity.
    r = simulate_dcf(2, 100, topology=topology, rts_cts=rts_cts, seed=0)
    assert station_throughputs_mbps(r) == pytest.approx([1.2, 1.2], rel=0.1)


def test_saturated_stations_deliver_less_with_longer_delay():
    # lambda = 1000 frames/sec offers 12 Mbps per station: queues build up.
    light = simulate_dcf(2, 100, seed=0)
    heavy = simulate_dcf(2, 1000, seed=0)
    assert all(t < 0.6 * 12 for t in station_throughputs_mbps(heavy))
    assert mean_delay_ms(heavy) > 100 * mean_delay_ms(light)


def test_ofdma_throughput_does_not_exceed_channel_capacity():
    r = simulate_ofdma(20, 100, 4, seed=0, sim_time_slots=100_000)
    assert 0 < network_throughput_mbps(r) < config.CHANNEL_RATE_BPS / 1e6
