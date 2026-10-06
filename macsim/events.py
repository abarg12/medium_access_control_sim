"""Event queue: the core of the event-driven simulator.

Simulation time advances directly to the next scheduled event rather than
stepping through every slot.
"""

import heapq
from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class EventType(IntEnum):
    """Event kinds. Events at the same time are processed in increasing value order,
    so the medium state is up to date before any transmission starts in a slot."""

    TX_END = 0
    RESPONSE_DEADLINE = 1  # a station's ACK/CTS should have arrived by now
    TX_START = 2  # SIFS-separated transmission (CTS, DATA after CTS, ACK)
    BACKOFF_EXPIRED = 3
    FRAME_ARRIVAL = 4


@dataclass
class Event:
    time: int  # slot index
    type: EventType
    node: int | None = None
    data: Any = None


class EventQueue:
    """Priority queue of events ordered by time, then type, then insertion order."""

    def __init__(self) -> None:
        self._heap: list = []
        self._seq = 0

    def push(self, event: Event) -> None:
        heapq.heappush(self._heap, (event.time, event.type, self._seq, event))
        self._seq += 1

    def pop(self) -> Event:
        return heapq.heappop(self._heap)[-1]

    def __len__(self) -> int:
        return len(self._heap)
