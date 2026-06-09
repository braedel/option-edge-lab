"""Quant step 1: VALIDATE the spike-pinning pipeline on the authoritative FOMC dates (known-truth control)
BEFORE applying it to pin NFP/CPI. On each Fed FOMC decision date, confirm a 14:00 ET volatility spike is
detectable in the ZB data. Uses TRADE-price range (cheap; full L3 book not needed for validation).

Dates: federalreserve.gov FOMC calendar (fetched, authoritative), 2023-01..2025-09 (22 meetings; excludes
2025-10/12 which are burned/sealed/out-of-span). DST-correct ET->UTC via zoneinfo.
Reports per-date post-14:00-ET 5-min move (ticks) vs same-day pre-event baseline. Run after confirming.
"""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import numpy as np

from options_lab.zb_mbo.codes import TRADE, action
from options_lab.zb_mbo.loader import load_events, month_path
from options_lab.zb_mbo.stream import TICK

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
MIN = 60_000_000_000

FOMC = [  # second (decision/statement) day, statement at 14:00 ET; source: federalreserve.gov
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17",
]


def utc_ns(date_str: str, hh: int, mm: int) -> int:
    d = dt.date.fromisoformat(date_str)
    t = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC)
    return int(t.timestamp() * 1e9)


def rng_t(px) -> float:
    return float((px.max() - px.min()) / TICK) if len(px) else 0.0


def main():
    bymonth = {}
    for ds in FOMC:
        bymonth.setdefault(ds[:7], []).append(ds)
    results = []
    for mk, dates in sorted(bymonth.items()):
        a = load_events(month_path(mk))
        ts, px = a["exch_ts"], a["px"]
        istrade = action(a["ev"]).astype(np.int64) == TRADE
        for ds in dates:
            t14 = utc_ns(ds, 14, 0)
            post = istrade & (ts >= t14) & (ts < t14 + 5 * MIN)            # 14:00-14:05 ET
            post_rng = rng_t(px[post])
            base = []                                                       # twelve 5-min ranges in the prior hour
            for k in range(12):
                lo, hi = t14 - (60 - 5 * k) * MIN, t14 - (55 - 5 * k) * MIN
                w = istrade & (ts >= lo) & (ts < hi)
                if w.sum():
                    base.append(rng_t(px[w]))
            bm = float(np.median(base)) if base else float("nan")
            results.append((ds, post_rng, bm, post_rng / bm if bm else float("nan"), int(post.sum())))
        del a
    print("FOMC date   | post5min_rng(t) | base5min(t) | ratio | n_trd")
    for ds, pr, bm, rt, n in results:
        print(f"  {ds} | {pr:9.1f}      | {bm:7.2f}     | {rt:5.1f} | {n}")
    prs = np.array([r[1] for r in results])
    clear = sum(1 for r in results if r[1] >= 5 and np.isfinite(r[3]) and r[3] >= 3)
    print(f"\nFOMC 14:00 ET 5-min move (ticks): median={np.median(prs):.1f} mean={prs.mean():.1f} "
          f"min={prs.min():.1f} max={prs.max():.1f}")
    print(f"clear spikes (>=5t AND >=3x baseline): {clear}/{len(results)}")
    print("[validation: do the known-truth FOMC dates show the 14:00 ET spike? confirms the pinning pipeline]")


if __name__ == "__main__":
    main()
