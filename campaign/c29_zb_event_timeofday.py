"""Event 'feel' step: ET time-of-day large-move profile. Do large ZB moves concentrate at the scheduled
announcement times -- 08:30 ET (NFP/CPI/PPI/claims/retail) and 14:00 ET (FOMC) -- vs the rest of the day?

For sampled times (every 60s), compute the forward 15-min MAX EXCURSION (best-case capturable move) and
bucket by ET half-hour (DST-correct via zoneinfo). Reports mean excursion + frequency of >=5t / >=10t moves
per ET bucket. This is diluted (a given 08:30 bucket averages event AND non-event days), so even a modest
elevation at 08:30/14:00 signals a strong conditional event effect worth the exact-calendar test next.
SIZING/feel only -- moves that happened, not predictability. Run after c28.
"""
from __future__ import annotations

import datetime as dt
import sys
from zoneinfo import ZoneInfo

import numpy as np

from options_lab.zb_mbo.labeler import bbo_timeline
from options_lab.zb_mbo.loader import load_events, month_path
from options_lab.zb_mbo.stream import TICK

MONTHS = ["2024-06", "2025-03", "2025-09"]
MAXEV = 6_000_000
SAMPLE_S = 60
H_NS = 15 * 60_000_000_000      # 15-min forward window
NS_DAY = 86_400_000_000_000
ET = ZoneInfo("America/New_York")


def profile_month(month, acc):
    a = load_events(month_path(month))[:MAXEV]
    tl = bbo_timeline(a)
    ts = tl["ts"].astype(np.int64)
    mid = (tl["bid"] + tl["ask"]) / 2.0
    fin = np.isfinite(mid) & (tl["bid"] > 0) & (tl["ask"] > 0)
    ts, mid = ts[fin], mid[fin]
    grid = np.arange(ts[0], ts[-1] - H_NS, SAMPLE_S * 1_000_000_000)
    for s in grid:
        if (s // NS_DAY) != ((s + H_NS) // NS_DAY):
            continue
        i0 = np.searchsorted(ts, s, "left")
        i1 = np.searchsorted(ts, s + H_NS, "right")
        if i1 - i0 < 2:
            continue
        seg = mid[i0:i1]
        sm = seg[0]
        exc = max(seg.max() - sm, sm - seg.min()) / TICK
        et = dt.datetime.fromtimestamp(s / 1e9, ET)
        bucket = f"{et.hour:02d}:{'30' if et.minute >= 30 else '00'}"
        d = acc.setdefault(bucket, [0, 0.0, 0, 0])  # n, sum_exc, n_ge5, n_ge10
        d[0] += 1; d[1] += exc; d[2] += int(exc >= 5); d[3] += int(exc >= 10)


def main():
    acc = {}
    for m in MONTHS:
        profile_month(m, acc)
        print(f"{m}: done")
    rows = []
    for b, (n, se, g5, g10) in acc.items():
        rows.append((b, n, se / n, 100 * g5 / n, 100 * g10 / n))
    print(f"\n=== ET time-of-day 15-min max-excursion profile ({MONTHS}) ===")
    print("ET bucket | n_samp | mean_exc(t) | %>=5t | %>=10t")
    for b, n, me, p5, p10 in sorted(rows, key=lambda r: -r[2])[:12]:
        star = "  <-- 08:30 release" if b == "08:30" else ("  <-- 14:00 FOMC" if b == "14:00" else "")
        print(f"  {b}    | {n:6d} | {me:9.2f}   | {p5:5.1f} | {p10:5.1f}{star}")
    alln = sum(v[0] for v in acc.values())
    allexc = sum(v[1] for v in acc.values()) / alln
    allg5 = 100 * sum(v[2] for v in acc.values()) / alln
    print(f"  OVERALL  | {alln:6d} | {allexc:9.2f}   | {allg5:5.1f} |  (baseline)")
    for key in ("08:30", "14:00"):
        if key in acc:
            n, se, g5, g10 = acc[key]
            print(f"  >>> {key} ET: mean_exc={se/n:.2f}t  %>=5t={100*g5/n:.1f}  %>=10t={100*g10/n:.1f}  "
                  f"(vs baseline {allexc:.2f}t / {allg5:.1f}%)")
    print("[diluted by non-event days; SIZING only, not predictability]")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        MONTHS = sys.argv[1:]
    main()
