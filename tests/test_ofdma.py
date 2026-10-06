"""Deterministic OFDMA verification cases (Appendix 2)."""

from macsim import config
from macsim.ofdma import schedule_round_robin, simulate_ofdma


def test_round_robin_skips_empty_queues():
    nonempty = [False, True, False, True, True, True]
    assert schedule_round_robin(nonempty, 0, 4) == [1, 3, 4, 5]
    assert schedule_round_robin(nonempty, 4, 4) == [4, 5, 1, 3]
    assert schedule_round_robin(nonempty, 0, 8) == [1, 3, 4, 5]


def test_five_backlogged_stations_four_rus():
    """Exactly four stations go in the first opportunity; the fifth leads the next."""
    assert schedule_round_robin([True] * 5, 0, 4) == [0, 1, 2, 3]
    assert schedule_round_robin([True] * 5, 4, 4) == [4, 0, 1, 2]

    # One frame each at t = 0. An opportunity lasts overhead + 4 * DATA + SIFS + ACK.
    opportunity = config.OFDMA_OVERHEAD_SLOTS + 4 * config.DATA_SLOTS + config.SIFS_SLOTS + config.ACK_SLOTS
    r = simulate_ofdma(5, 0, 4, arrivals=[[0]] * 5, sim_time_slots=2000)
    assert r.successes == [1] * 5
    assert r.collisions == [0] * 5
    assert r.delays == [[opportunity]] * 4 + [[2 * opportunity]]
