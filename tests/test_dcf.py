"""Deterministic DCF verification cases (Appendix 2).

Each test fixes arrivals and backoff values and checks the simulator against
a hand-built event timeline. Times are in slots: DIFS = 3, SIFS = 1,
DATA = 100, RTS = CTS = ACK = 2.
"""

from macsim.dcf import Topology, simulate_dcf


def run(arrivals, backoffs, **kwargs):
    return simulate_dcf(len(arrivals), 0, arrivals=arrivals, backoffs=backoffs, sim_time_slots=1000, **kwargs)


def test_single_success_from_a():
    # DIFS 0-3, backoff 3-7, DATA 7-107, SIFS, ACK 108-110
    r = run([[0], []], [[4], []])
    assert r.successes == [1, 0]
    assert r.attempts == [1, 0]
    assert r.collisions == [0, 0]
    assert r.delays == [[110], []]


def test_single_success_from_b():
    # arrival 10, DIFS 10-13, backoff 0, DATA 13-113, SIFS, ACK 114-116
    r = run([[], [10]], [[], [0]])
    assert r.successes == [0, 1]
    assert r.delays == [[], [106]]


def test_collision_between_a_and_b():
    # Both transmit at 6 and collide; DATA ends 106, no ACK by 109. CW doubles.
    # A (backoff 1): DIFS 109-112, DATA 113-213, ACK 214-216.
    # B (backoff 6): counts 112 -> 113, freezes with 5 left;
    #                DIFS 216-219, backoff to 224, DATA 224-324, ACK 325-327.
    r = run([[0], [0]], [[3, 1], [3, 6]])
    assert r.attempts == [2, 2]
    assert r.collisions == [1, 1]
    assert r.successes == [1, 1]
    assert r.delays == [[216], [327]]


def test_rts_collision_hidden_terminals():
    # RTS from A at 5-7 and from B at 6-8 overlap at the AP; neither gets a CTS.
    # A (no CTS at 10, backoff 0): RTS 13-15, CTS 16-18, DATA 19-119, ACK 120-122.
    # B (no CTS at 11, backoff 20): counts 14 -> 16, freezes with 18 left on the
    #   CTS, NAV until 122; DIFS 122-125, backoff to 143, RTS 143-145,
    #   CTS 146-148, DATA 149-249, ACK 250-252.
    r = run([[0], [0]], [[2, 0], [3, 20]], topology=Topology.HIDDEN_TERMINALS, rts_cts=True)
    assert r.attempts == [2, 2]
    assert r.collisions == [1, 1]
    assert r.successes == [1, 1]
    assert r.delays == [[122], [252]]


def test_hidden_terminals_collide_mid_frame():
    # Without RTS/CTS, B cannot sense A's DATA (5-105) and transmits at 50.
    r = run([[0], [40]], [[2], [7]], topology=Topology.HIDDEN_TERMINALS)
    assert r.collisions[0] >= 1 and r.collisions[1] >= 1


def test_three_stations_collide_freeze_resume():
    """Backoffs 2, 2, 5: stations 1 and 2 collide; station 3 freezes, then resumes."""
    # 1 and 2 transmit at 5 and collide (DATA 5-105, no ACK by 108).
    # 3 counts 3 -> 5 and freezes with 3 left.
    # 1 (new backoff 0): DIFS 108-111, DATA 111-211, ACK 212-214.
    # 3: DIFS 214-217, backoff to 220, DATA 220-320, ACK 321-323.
    # 2 (new backoff 9): counts 217 -> 220, freezes with 6 left;
    #    DIFS 323-326, backoff to 332, DATA 332-432, ACK 433-435.
    r = run([[0], [0], [0]], [[2, 0], [2, 9], [5]], trace=True)
    assert r.attempts == [2, 2, 1]
    assert r.collisions == [1, 1, 0]
    assert r.delays == [[214], [435], [323]]
    data_starts = [(t, node) for t, node, what in r.trace if what == "DATA start"]
    assert data_starts == [(5, "STA0"), (5, "STA1"), (111, "STA0"), (220, "STA2"), (332, "STA1")]
