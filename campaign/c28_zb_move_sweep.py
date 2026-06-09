"""Large-move SIZING sweep -- count how many large moves actually HAPPENED, by (size x horizon), to see
where the largest-size / highest-frequency cluster is and whether it's worth building a detector for.

For non-overlapping H-minute windows (not crossing the daily UTC book-reset), compute the MAX FAVORABLE
EXCURSION (best-case capturable move = max |mid - window_start_mid| within the window) and count windows
whose excursion >= T ticks. Reports events/day per (T, H) across a few months (to span regimes).

THIS IS SIZING ONLY -- it counts moves that occurred (a perfect-exit upper bound), NOT predictability,
capturability, or edge. A large, frequent cluster says "a target population exists, worth a detector";
it does NOT say the move is forecastable (the c22 reverse-analysis already found big moves had ~no
feature precursor). Run: .venv-mbo python campaign/c28_zb_move_sweep.py
"""
from __future__ import annotations

import sys

import numpy as np

from options_lab.zb_mbo.labeler import bbo_timeline
from options_lab.zb_mbo.loader import load_events, month_path
from options_lab.zb_mbo.stream import TICK

MONTHS = ["2024-06", "2025-03", "2025-09"]   # span regimes; ~5-day (6M-event) slice each
MAXEV = 6_000_000
HORIZONS_MIN = [1, 2, 5, 10, 30]
THRESH = [2, 3, 4, 5, 8, 10, 15, 20]
NS_MIN = 60_000_000_000
NS_DAY = 86_400_000_000_000


def sweep_month(month: str):
    a = load_events(month_path(month))[:MAXEV]
    tl = bbo_timeline(a)
    ts = tl["ts"].astype(np.int64)
    mid = (tl["bid"] + tl["ask"]) / 2.0
    fin = np.isfinite(mid) & (tl["bid"] > 0) & (tl["ask"] > 0)
    ts, mid = ts[fin], mid[fin]
    days = max(int(np.unique(ts // NS_DAY).size), 1)
    counts = {}
    for H in HORIZONS_MIN:
        w = H * NS_MIN
        exc = []
        for s in np.arange(ts[0], ts[-1] - w, w):
            if (s // NS_DAY) != ((s + w) // NS_DAY):
                continue  # skip windows crossing the daily UTC book-reset (avoids reset artifact)
            i0 = np.searchsorted(ts, s, "left")
            i1 = np.searchsorted(ts, s + w, "right")
            if i1 - i0 >= 2:
                seg = mid[i0:i1]
                sm = seg[0]
                exc.append(max(seg.max() - sm, sm - seg.min()) / TICK)
        exc = np.asarray(exc)
        counts[(H, "nwin")] = len(exc)
        for T in THRESH:
            counts[(H, T)] = int((exc >= T).sum())
    return counts, days


def main():
    agg, nwin, total_days = {}, {}, 0
    for m in MONTHS:
        c, d = sweep_month(m)
        total_days += d
        for H in HORIZONS_MIN:
            nwin[H] = nwin.get(H, 0) + c[(H, "nwin")]
            for T in THRESH:
                agg[(H, T)] = agg.get((H, T), 0) + c[(H, T)]
        print(f"{m}: {d} days")
    print(f"\n=== large-move sizing: max favorable excursion >= T ticks within H min "
          f"({total_days} days across {MONTHS}) ===")
    print("events/day | " + "  ".join(f"H={H:>2}m" for H in HORIZONS_MIN))
    for T in THRESH:
        print(f"  >= {T:2d}t    | " + "  ".join(f"{agg[(H, T)] / total_days:6.1f}" for H in HORIZONS_MIN))
    print("windows/day| " + "  ".join(f"{nwin[H] / total_days:6.1f}" for H in HORIZONS_MIN))
    print("[$/tick=31.25; SIZING ONLY -- moves that happened (perfect-exit upper bound), NOT predictability]")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        MONTHS = sys.argv[1:]
    main()
