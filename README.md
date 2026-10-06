# medium_access_control_sim

Event-driven simulator for Wi-Fi medium access control, written for ECE 478/578 Project 1. It covers CSMA/CA, CSMA/CA with RTS/CTS, dense DCF, and a simplified Wi-Fi 6 uplink OFDMA scheduler.

## Layout

```
macsim/            simulator package
  config.py        default parameters (Table 1)
  events.py        event queue
  traffic.py       Poisson arrival generation
  station.py       per-station state
  dcf.py           CSMA/CA, with optional RTS/CTS and hidden terminals
  ofdma.py         round-robin OFDMA scheduler
  metrics.py       throughput, collision probability, delay, Jain's index
  plotting.py      shared figure style
experiments/       one script per project part; each writes its plots to figures/
tests/             deterministic verification cases
figures/           generated plots
results/           generated CSV tables behind the plots
```

## Modeling assumptions

- All times are integer slots. A frame that arrives mid-slot becomes available at the next slot boundary; delay is measured from the true arrival time.
- A station always draws a backoff for a new head-of-line frame, even on an idle channel.
- A transmission attempt is a DATA start (basic access) or an RTS start (RTS/CTS). It counts as a collision if no ACK follows.
- A sender detects a missing CTS/ACK `SIFS + ACK` after its frame ends. Stations that sensed an undecodable frame wait the same time (EIFS) before starting DIFS.
- A frame is decoded only if nothing else the receiver can hear, and no transmission of its own, overlaps it. A hidden station that is sending its own RTS while the AP sends a CTS therefore misses the NAV.
- An OFDMA opportunity lasts `overhead + K * 100 + SIFS + ACK` slots, where the overhead is a 2-slot trigger frame plus SIFS (`OFDMA_OVERHEAD_SLOTS`). OFDMA has no contention, so the AP starts an opportunity as soon as any station has a frame.
- Each data point is the average of `NUM_RUNS` (5) independent seeds.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```
python -m experiments.part1   # two-station CSMA/CA and RTS/CTS
python -m experiments.part2   # dense DCF
python -m experiments.part3   # DCF versus OFDMA
pytest                        # verification cases
```
