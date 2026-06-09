"""Pre-registered selective-taker trigger detectors on the causal trade-snapshot stream.

Families (spec section 2; thresholds are the <=3 economically-spaced, pre-registered, FROZEN levels
in grid.json, calibrated on TRAIN feature distributions only):
  A vacuum  -- aggressed-side top-3 depth below `thresh` x its trailing-window median (book was thin);
               take in the aggression direction.
  B sweep   -- |signed trade| at/above `thresh` x trailing-window median |signed trade| (outsized aggression).
  C event   -- trade timestamp inside a scheduled event window.

All features are trailing / causal (review B3): the rolling baselines use `.shift(1)` so the current
trade is never in its own baseline, and a future trade can never change an earlier episode's t_signal.
A refractory window collapses one price move into a single episode (so episode counts are the unit of
independent evidence for the census).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# side: +1 = take long (aggressor was buying / lifting asks), -1 = take short (aggressor hitting bids).
EP_DTYPE = np.dtype([("ts", "i8"), ("side", "i1"), ("family", "U1"), ("value", "f8")])


def _dedupe(ts, side, value, family, refractory_ns) -> np.ndarray:
    out = []
    last = -(1 << 62)
    for t, s, v in zip(ts, side, value):
        if int(t) - last >= refractory_ns:
            out.append((int(t), int(s), family, float(v)))
            last = int(t)
    return np.array(out, dtype=EP_DTYPE) if out else np.empty(0, dtype=EP_DTYPE)


def _trailing_median(x, window) -> np.ndarray:
    return pd.Series(np.asarray(x, float)).rolling(window).median().shift(1).to_numpy()


def detect_vacuum(snaps, thresh, window, refractory_ns) -> np.ndarray:
    if len(snaps) < window + 1:
        return np.empty(0, dtype=EP_DTYPE)
    sgn = np.sign(snaps["trade_signed"]).astype(int)
    hit_depth = np.where(sgn < 0, snaps["bid3"], snaps["ask3"])  # depth on the side being hit
    base = _trailing_median(hit_depth, window)
    fire = (sgn != 0) & np.isfinite(base) & (base > 0) & (hit_depth < thresh * base)
    idx = np.flatnonzero(fire)
    value = hit_depth[idx] / np.where(base[idx] == 0, np.nan, base[idx])
    return _dedupe(snaps["ts"][idx], sgn[idx], value, "A", refractory_ns)


def detect_sweep(snaps, thresh, window, refractory_ns) -> np.ndarray:
    if len(snaps) < window + 1:
        return np.empty(0, dtype=EP_DTYPE)
    sgn = np.sign(snaps["trade_signed"]).astype(int)
    size = np.abs(snaps["trade_signed"]).astype(float)
    base = _trailing_median(size, window)
    fire = (sgn != 0) & np.isfinite(base) & (base > 0) & (size >= thresh * base)
    idx = np.flatnonzero(fire)
    return _dedupe(snaps["ts"][idx], sgn[idx], size[idx] / base[idx], "B", refractory_ns)


def detect_event(snaps, windows_ns, refractory_ns) -> np.ndarray:
    if len(snaps) == 0 or len(windows_ns) == 0:
        return np.empty(0, dtype=EP_DTYPE)
    ts = snaps["ts"]
    sgn = np.sign(snaps["trade_signed"]).astype(int)
    inwin = np.zeros(len(ts), dtype=bool)
    for a, b in windows_ns:
        inwin |= (ts >= a) & (ts < b)
    idx = np.flatnonzero(inwin & (sgn != 0))
    return _dedupe(ts[idx], sgn[idx], np.ones(len(idx)), "C", refractory_ns)
