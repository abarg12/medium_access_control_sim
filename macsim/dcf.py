"""DCF simulator: CSMA/CA with optional RTS/CTS (Parts I and II).

Every node (the stations plus the AP) tracks the medium as it senses it, so
the same code handles a single collision domain and hidden terminals. A frame
is decoded by a listener only if nothing else the listener can hear, and no
transmission of its own, overlaps it.

Modeling choices:
- A sender that gets no CTS/ACK detects the failure SIFS + ACK after its frame
  ends, then applies binary exponential backoff.
- A node that sensed a frame it could not decode defers SIFS + ACK after the
  medium goes idle (EIFS), so bystanders and colliding stations resume their
  DIFS at the same instant.
- A transmission attempt is counted when a station starts a DATA frame (basic
  access) or an RTS frame (RTS/CTS). It is a collision if no ACK follows.
"""

import math
from collections import deque
from dataclasses import dataclass
from enum import Enum

import numpy as np

from . import config
from .events import Event, EventQueue, EventType
from .metrics import Results
from .station import Station
from .traffic import poisson_arrivals

RESPONSE_SLOTS = config.SIFS_SLOTS + config.ACK_SLOTS  # also covers CTS (same size)


class Topology(Enum):
    SINGLE_DOMAIN = "single_domain"  # every station senses every other station
    HIDDEN_TERMINALS = "hidden_terminals"  # stations sense only the AP


@dataclass(eq=False)
class _Tx:
    src: int
    dst: int
    kind: str  # "DATA", "RTS", "CTS", or "ACK"
    start: int
    end: int
    nav_end: int  # end of the exchange this frame reserves the medium for


class _DcfSim:
    def __init__(self, num_stations, topology, rts_cts, rng, arrivals, backoffs, sim_time_slots, trace):
        n = num_stations
        self.ap = n
        self.rts_cts = rts_cts
        self.rng = rng
        self.sim_time_slots = sim_time_slots
        self.trace = [] if trace else None
        self.stations = [Station(i) for i in range(n)]
        for st, preset in zip(self.stations, backoffs or []):
            st.preset_backoffs = deque(preset)

        # listeners[x]: nodes that sense a transmission from x
        if topology is Topology.SINGLE_DOMAIN:
            self.listeners = [[j for j in range(n + 1) if j != i] for i in range(n + 1)]
        else:
            self.listeners = [[self.ap] for _ in range(n)] + [list(range(n))]

        self.busy = [0] * (n + 1)  # transmissions currently sensed
        self.transmitting = [False] * (n + 1)
        self.rx = [None] * (n + 1)  # frame being received cleanly, if any
        self.dirty = [False] * (n + 1)  # sensed something undecodable this busy period
        self.defer = [0] * (n + 1)  # NAV / EIFS: medium treated as busy until this slot

        self.events = EventQueue()
        for i, times in enumerate(arrivals):
            for arrival in times:
                self.events.push(Event(math.ceil(arrival), EventType.FRAME_ARRIVAL, i, float(arrival)))

    def run(self) -> Results:
        handlers = {
            EventType.TX_END: lambda ev: self._end_tx(ev.time, ev.data),
            EventType.RESPONSE_DEADLINE: lambda ev: self._response_deadline(ev.time, ev.node),
            EventType.TX_START: lambda ev: self._start_tx(ev.data),
            EventType.BACKOFF_EXPIRED: lambda ev: self._backoff_expired(ev.time, ev.node, ev.data),
            EventType.FRAME_ARRIVAL: lambda ev: self._frame_arrival(ev.time, ev.node, ev.data),
        }
        while self.events:
            event = self.events.pop()
            if event.time >= self.sim_time_slots:
                break
            handlers[event.type](event)
        return Results(
            sim_time_slots=self.sim_time_slots,
            successes=[st.successes for st in self.stations],
            attempts=[st.attempts for st in self.stations],
            collisions=[st.collisions for st in self.stations],
            delays=[st.delays for st in self.stations],
            trace=self.trace or [],
        )

    def _log(self, time, node, what) -> None:
        if self.trace is not None:
            self.trace.append((time, "AP" if node == self.ap else f"STA{node}", what))

    # --- Contention ---

    def _frame_arrival(self, t, i, arrival) -> None:
        st = self.stations[i]
        st.queue.append(arrival)
        if not st.active:
            st.active = True
            st.draw_backoff(self.rng)
            self._try_resume(i, t)

    def _try_resume(self, i, t) -> None:
        """Start DIFS + backoff countdown if station i is contending and senses an idle medium."""
        st = self.stations[i]
        if not st.active or st.phase is not None or st.counting or self.busy[i] or self.transmitting[i]:
            return
        st.expiry = max(t, self.defer[i]) + config.DIFS_SLOTS + st.backoff
        st.counting = True
        st.token += 1
        self.events.push(Event(st.expiry, EventType.BACKOFF_EXPIRED, i, st.token))

    def _freeze(self, i, t) -> None:
        """The medium became busy at t. A countdown expiring at t still transmits."""
        st = self.stations[i]
        if st.counting and st.expiry > t:
            st.backoff = min(st.backoff, st.expiry - t)
            st.counting = False
            st.token += 1

    def _backoff_expired(self, t, i, token) -> None:
        st = self.stations[i]
        if not st.counting or token != st.token:
            return
        st.counting = False
        st.attempts += 1
        if self.rts_cts:
            st.phase = "RTS"
            end = t + config.RTS_SLOTS
            nav_end = end + RESPONSE_SLOTS + config.SIFS_SLOTS + config.DATA_SLOTS + RESPONSE_SLOTS
            self._start_tx(_Tx(i, self.ap, "RTS", t, end, nav_end))
        else:
            self._start_data(i, t)

    def _start_data(self, i, t) -> None:
        self.stations[i].phase = "DATA"
        end = t + config.DATA_SLOTS
        self._start_tx(_Tx(i, self.ap, "DATA", t, end, end + RESPONSE_SLOTS))

    # --- Medium ---

    def _start_tx(self, tx) -> None:
        src, t = tx.src, tx.start
        if self.busy[src]:
            self.dirty[src] = True
        self.rx[src] = None
        self.transmitting[src] = True
        for j in self.listeners[src]:
            if self.transmitting[j] or self.busy[j]:
                self.dirty[j] = True
                self.rx[j] = None
            else:
                self.rx[j] = tx
            self.busy[j] += 1
            if j != self.ap:
                self._freeze(j, t)
        self.events.push(Event(tx.end, EventType.TX_END, src, tx))
        self._log(t, src, f"{tx.kind} start")

    def _end_tx(self, t, tx) -> None:
        src = tx.src
        self.transmitting[src] = False
        if src != self.ap:
            self.events.push(Event(t + RESPONSE_SLOTS, EventType.RESPONSE_DEADLINE, src))
        self._medium_idle(src, t)
        for j in self.listeners[src]:
            if self.rx[j] is tx:
                self.rx[j] = None
                self._deliver(j, tx, t)
            self.busy[j] -= 1
            self._medium_idle(j, t)
            if j != self.ap:
                self._try_resume(j, t)

    def _medium_idle(self, j, t) -> None:
        if not self.busy[j] and not self.transmitting[j] and self.dirty[j]:
            self.dirty[j] = False
            self.defer[j] = max(self.defer[j], t + RESPONSE_SLOTS)

    def _deliver(self, j, tx, t) -> None:
        """Node j decoded tx, which ended at t."""
        if j == self.ap:
            start = t + config.SIFS_SLOTS
            if tx.kind == "RTS":
                reply = _Tx(self.ap, tx.src, "CTS", start, start + config.CTS_SLOTS, tx.nav_end)
            else:
                reply = _Tx(self.ap, tx.src, "ACK", start, start + config.ACK_SLOTS, tx.nav_end)
            self.events.push(Event(start, EventType.TX_START, self.ap, reply))
        elif tx.dst == j:
            self.stations[j].got_response = True
        else:
            self.defer[j] = max(self.defer[j], tx.nav_end)  # NAV

    def _response_deadline(self, t, i) -> None:
        st = self.stations[i]
        if st.got_response:
            st.got_response = False
            if st.phase == "RTS":
                start = t + config.SIFS_SLOTS
                st.phase = "DATA"
                end = start + config.DATA_SLOTS
                data = _Tx(i, self.ap, "DATA", start, end, end + RESPONSE_SLOTS)
                self.events.push(Event(start, EventType.TX_START, i, data))
                return
            st.on_success(t)
            self._log(t, i, "ACK received")
            st.active = bool(st.queue)
            if st.active:
                st.draw_backoff(self.rng)
        else:
            self._log(t, i, f"no {'CTS' if st.phase == 'RTS' else 'ACK'}: collision")
            st.on_collision(self.rng)
        st.phase = None
        self._try_resume(i, t)


def simulate_dcf(
    num_stations: int,
    arrival_rate: float,
    topology: Topology = Topology.SINGLE_DOMAIN,
    rts_cts: bool = False,
    seed: int | None = None,
    arrivals: list | None = None,
    backoffs: list | None = None,
    sim_time_slots: int = config.SIM_TIME_SLOTS,
    trace: bool = False,
) -> Results:
    """Run one DCF simulation.

    arrival_rate is the per-station rate in frames/sec. `arrivals` (per-station
    arrival times in slots) and `backoffs` (per-station backoff values, used
    in order before random draws) override the random draws so deterministic
    verification cases can be compared against a hand-built timeline.
    """
    rng = np.random.default_rng(seed)
    if arrivals is None:
        arrivals = [poisson_arrivals(arrival_rate, sim_time_slots, rng) for _ in range(num_stations)]
    return _DcfSim(num_stations, topology, rts_cts, rng, arrivals, backoffs, sim_time_slots, trace).run()
