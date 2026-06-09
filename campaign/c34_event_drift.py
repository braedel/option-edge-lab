"""Announcement SLOW-DRIFT test -- the latency-immune announcement angle the continuation test didn't reach.

c32 showed post-release continuation ~0 at <=10 min (the directional move is in the colo-only spike). BUT the
pooled continuation GREW with horizon (+0.80t @2min -> +1.53t @10min), and post-FOMC/NFP drift is documented
to persist for HOURS. A slow multi-tick drift over 30 min-4 hr is fully tradeable at 0.5-1.5 ms latency
(no spike to catch). This extends c32 to long horizons.

Causal, same discipline as c32: direction = sign of move over [t, t+W_dir]; ENTER at t+W_dir+1ms (strictly
after the direction window); drift = signed move from entry over H. Mid proxy = trade price. Cost ~1.13t is
negligible vs a multi-tick drift IF one exists.
Cells: W_dir in {60,300}s x H in {30,60,120,240} min. Per event-type + pooled-08:30; PLACEBO (random
direction -> must be ~0); leave-one-out. Run on local mirror (ZB_DATA_ROOT). Reads frozen calendar.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import csv
import datetime as dt
import multiprocessing as mp
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from options_lab.zb_mbo.codes import TRADE, action
from options_lab.zb_mbo.loader import load_events, month_path
from options_lab.zb_mbo.stream import TICK

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
SEC = 1_000_000_000
LAT = 1_000_000
DIR_WINDOWS = [60, 300]                       # s to establish direction
HORIZONS = [1800, 3600, 7200, 14400]          # 30m, 60m, 120m, 240m
NPROC = 10
CAL = Path("data/zb_macro_events.csv")


def utc_ns(date_str, time_et):
    d = dt.date.fromisoformat(date_str)
    hh, mm = map(int, time_et.split(":"))
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC).timestamp() * 1e9)


def load_calendar():
    evs = []
    for r in csv.DictReader(open(CAL)):
        if r["pinning"] == "NOT_FOUND" or len(r["date"]) != 10:
            continue
        evs.append({"date": r["date"], "type": r["event"], "t": utc_ns(r["date"], r["time_et"]),
                    "contaminated": r["contaminated"] == "True"})
    return evs


def px_at(tts, tpx, t):
    j = np.searchsorted(tts, t, "right") - 1
    return float(tpx[j]) if j >= 0 else np.nan


def process_month(arg):
    mk, events = arg
    a = load_events(month_path(mk))
    istr = action(a["ev"]).astype(np.int64) == TRADE
    tts, tpx = a["exch_ts"][istr], a["px"][istr]
    out = []
    for e in events:
        t0 = e["t"]; p0 = px_at(tts, tpx, t0)
        for w in DIR_WINDOWS:
            pr = px_at(tts, tpx, t0 + w * SEC)
            if not np.isfinite(pr):
                continue
            d = np.sign(pr - p0)
            if d == 0:
                continue
            entry = px_at(tts, tpx, t0 + w * SEC + LAT)
            for h in HORIZONS:
                ex = px_at(tts, tpx, t0 + w * SEC + LAT + h * SEC)
                if not (np.isfinite(entry) and np.isfinite(ex)):
                    continue
                raw = (ex - entry) / TICK                       # signed price move (unconditioned)
                out.append((w, h, e["type"], e["contaminated"], float(raw), int(d)))
    return mk, out


def stat(vals):
    v = np.array(vals, float)
    if len(v) < 5:
        return f"n={len(v)} (few)"
    se = v.std(ddof=1) / np.sqrt(len(v))
    return f"n={len(v):3d} mean={v.mean():+6.2f}t med={np.median(v):+6.2f}t %cont={np.mean(v > 0):.2f} t={v.mean() / se:+5.2f}"


def main():
    evs = load_calendar()
    bymonth = defaultdict(list)
    for e in evs:
        bymonth[e["date"][:7]].append(e)
    items = sorted(bymonth.items())
    nproc = min(NPROC, len(items))
    print(f"loading {len(items)} months across {nproc} workers...", flush=True)
    rows = []
    with mp.Pool(nproc) as pool:
        for mk, res in pool.imap_unordered(process_month, items):
            rows.extend(res)
            print(f"  done {mk} ({len(res)} obs)", flush=True)

    # deterministic placebo signs (no Math.random dependence): hash each row index to +-1
    rng = np.random.default_rng(20260609)
    placebo_sign = rng.choice([-1, 1], size=len(rows))

    print("\n=== announcement slow-drift (MID-BASED; continuation = raw*dir) ===")
    for w in DIR_WINDOWS:
        for h in HORIZONS:
            sub = [(r[2], r[3], r[4] * r[5], placebo_sign[k] * r[4])
                   for k, r in enumerate(rows) if r[0] == w and r[1] == h]
            print(f"\n-- dir_window={w}s  hold={h // 60}min --")
            for typ in ("FOMC", "NFP", "CPI"):
                print(f"   {typ:5s}: {stat([c for (t, _, c, _) in sub if t == typ])}")
            print(f"   CPI(clean): {stat([c for (t, ct, c, _) in sub if t == 'CPI' and not ct])}")
            pool_real = [c for (t, ct, c, _) in sub if t in ('FOMC', 'NFP') or (t == 'CPI' and not ct)]
            pool_plac = [pc for (t, ct, c, pc) in sub if t in ('FOMC', 'NFP') or (t == 'CPI' and not ct)]
            print(f"   POOL all : {stat(pool_real)}")
            print(f"   PLACEBO  : {stat(pool_plac)}  <- must be ~0")

    # leave-one-out on the longest horizon, dir_window=300s, pooled
    hl = [(r[2], r[3], r[4] * r[5]) for r in rows if r[0] == 300 and r[1] == HORIZONS[-1]]
    pooled = [c for (t, ct, c) in hl if t in ('FOMC', 'NFP') or (t == 'CPI' and not ct)]
    if len(pooled) >= 5:
        v = np.array(pooled, float)
        loo = [np.delete(v, i).mean() for i in range(len(v))]
        print(f"\nLOO (dir300/{HORIZONS[-1]//60}min, pooled): mean={v.mean():+.2f}t  "
              f"range=[{min(loo):+.2f},{max(loo):+.2f}]  sign-stable={'YES' if min(loo) * max(loo) > 0 else 'NO -- FRAGILE'}")
    print("\n[Does a multi-tick drift emerge and GROW with horizon, beat placebo, and hold LOO? "
          "Then it is a slow, latency-immune announcement edge worth a sealed-OOS confirm.]")


if __name__ == "__main__":
    main()
