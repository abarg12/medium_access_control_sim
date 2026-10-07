"""Default simulation parameters (Table 1 of the project description).

All durations are expressed in slots unless the name ends in a unit suffix.
"""

# --- Timing ---
SLOT_DURATION_S = 10e-6
SLOTS_PER_SEC = round(1 / SLOT_DURATION_S)
SIM_TIME_S = 10
SIM_TIME_SLOTS = SIM_TIME_S * SLOTS_PER_SEC

# --- Frames ---
DATA_FRAME_BYTES = 1500
DATA_FRAME_BITS = DATA_FRAME_BYTES * 8
CHANNEL_RATE_BPS = 12e6
DATA_SLOTS = round(DATA_FRAME_BITS / CHANNEL_RATE_BPS / SLOT_DURATION_S)  # 100
ACK_SLOTS = 2
RTS_SLOTS = 2
CTS_SLOTS = 2

# --- Interframe spaces ---
SIFS_SLOTS = 1
DIFS_SLOTS = 3

# --- Backoff ---
CW0 = 8
CW_MAX = 1024

# --- Part I: two stations ---
PART1_ARRIVAL_RATES = [100, 200, 300, 500, 800, 1000]  # lambda, frames/sec

# --- Part II: dense DCF ---
DENSE_N = [2, 5, 10, 20, 40]
AGGREGATE_LOADS = [300, 800]  # Lambda, frames/sec; per-station rate is Lambda / N

# --- Part III: OFDMA (extra credit) ---
OFDMA_RUS = [1, 2, 4, 8]  # K
OFDMA_COMPARISON_N = 20
# Fixed scheduling overhead per OFDMA transmission opportunity: a trigger frame
# (same size as the other control frames) followed by SIFS. Document this
# choice in the report.
OFDMA_OVERHEAD_SLOTS = RTS_SLOTS + SIFS_SLOTS

# --- Reporting ---
# A curve is marked saturated at the first offered load where throughput falls
# below this fraction of the offered load.
SATURATION_FRACTION = 0.95

# --- Reproducibility ---
DEFAULT_SEED = 0
NUM_RUNS = 5  # independent runs to average per data point
