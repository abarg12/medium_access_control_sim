"""Per-station state (Section 4.2)."""

from collections import deque
from dataclasses import dataclass, field

from . import config


@dataclass
class Station:
    id: int
    queue: deque = field(default_factory=deque)  # arrival times of buffered frames
    cw: int = config.CW0
    backoff: int | None = None  # None until a value is drawn for the head-of-line frame
    retries: int = 0  # consecutive collisions for the current frame
    attempts: int = 0
    collisions: int = 0
    successes: int = 0
    delays: list = field(default_factory=list)  # t_ACK - t_arrival per delivered frame, in slots
    backoff_draws: list = field(default_factory=list)  # every backoff value drawn, in slots

    # Backoff values used before falling back to random draws (deterministic tests).
    preset_backoffs: deque = field(default_factory=deque)

    # DCF bookkeeping
    active: bool = False  # a head-of-line frame is being served
    phase: str | None = None  # None while contending, else "RTS" or "DATA"
    counting: bool = False  # backoff countdown is running
    expiry: int = 0  # slot at which the running countdown reaches zero
    token: int = 0  # invalidates stale BACKOFF_EXPIRED events
    got_response: bool = False  # CTS/ACK addressed to this station was decoded

    def draw_backoff(self, rng) -> None:
        """Pick a backoff uniformly from {0, ..., CW - 1}."""
        if self.preset_backoffs:
            self.backoff = self.preset_backoffs.popleft()
        else:
            self.backoff = int(rng.integers(0, self.cw))
        self.backoff_draws.append(self.backoff)

    def on_collision(self, rng) -> None:
        """Binary exponential backoff: CW = min(2^k * CW0, CW_MAX)."""
        self.collisions += 1
        self.retries += 1
        self.cw = min(2**self.retries * config.CW0, config.CW_MAX)
        self.draw_backoff(rng)

    def on_success(self, ack_time: int) -> None:
        """Record delay, dequeue the frame, and reset CW."""
        self.delays.append(ack_time - self.queue.popleft())
        self.successes += 1
        self.retries = 0
        self.cw = config.CW0
        self.backoff = None
