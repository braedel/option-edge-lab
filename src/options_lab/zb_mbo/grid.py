"""FROZEN pre-registered trigger grid (spec section 2; review G3 / B4).

Committing this file IS the pre-registration. The thresholds were calibrated on TRAIN feature
*distributions* only (the 2024-06 calibration peek read depth/size percentiles, never forward
outcomes), then frozen here. `n_trials()` feeds the Deflated Sharpe Ratio and INCLUDES the prior
project's 10 ZB micro-signal null baselines (multiple testing is cumulative across the program).
Every campaign script asserts `grid_hash()` matches the value recorded in its run report; if the grid
ever changes, the hash changes and the change is a conscious, logged re-registration.
"""
from __future__ import annotations

import hashlib
import json

WINDOW = 100                      # trailing-median lookback (trades) for vacuum/sweep baselines
REFRACTORY_NS = 1_000_000_000     # 1 s: collapse one price move into one episode

VACUUM_THRESHOLDS = (0.50, 0.33, 0.25)   # aggressed-side top-3 depth / trailing median (thin-book tail)
SWEEP_THRESHOLDS = (3.0, 5.0, 8.0)       # |signed trade| / trailing median (outsized aggression)
HORIZONS_NS = (1_000_000_000, 5_000_000_000, 30_000_000_000)     # 1 s / 5 s / 30 s taker holds
LATENCIES_NS = (500_000, 1_000_000, 1_500_000)                   # 0.5 / 1.0 / 1.5 ms (production range)
LATENCY_SWEEP_NS = (100_000, 250_000, 500_000, 1_000_000, 1_500_000, 3_000_000, 5_000_000)  # sensitivity

PRIOR_NULL_BASELINES = 10         # prior project's ZB micro-signal baselines (all net-negative after $4)

FROZEN_GRID = {
    "families": {
        "A_vacuum": {"thresholds": list(VACUUM_THRESHOLDS), "window": WINDOW},
        "B_sweep": {"thresholds": list(SWEEP_THRESHOLDS), "window": WINDOW},
        # "C_event" is added once the UTC-resolved event calendar (zb_events.csv, review G4) is built.
    },
    "horizons_ns": list(HORIZONS_NS),
    "latencies_ns": list(LATENCIES_NS),
    "refractory_ns": REFRACTORY_NS,
}


def n_cells() -> int:
    """Stage-1 grid cells = (sum of thresholds across families) x horizons x latencies."""
    thr = sum(len(f["thresholds"]) for f in FROZEN_GRID["families"].values())
    return thr * len(HORIZONS_NS) * len(LATENCIES_NS)


def n_trials(include_prior: bool = True) -> int:
    """Honest trial count for the Deflated Sharpe (review B4): grid cells + the 10 prior null baselines."""
    return n_cells() + (PRIOR_NULL_BASELINES if include_prior else 0)


def grid_hash() -> str:
    return hashlib.sha256(json.dumps(FROZEN_GRID, sort_keys=True).encode()).hexdigest()[:16]
