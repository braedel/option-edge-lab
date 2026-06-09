"""Stage-1 event edge test: post-announcement CONTINUATION, MID-BASED (no spread yet) -- the cheap gate
before the decisive widened-spread test (Stage 2).

Per the quant protocol (causal, no look-ahead):
  - direction = sign of the initial reaction over [t_event, t_event + reaction_delay] (price reveals the
    surprise direction; we do NOT use the release number);
  - ENTER at t_event + reaction_delay + latency (uniform, schedule-relative -- never keyed to the spike);
  - continuation = signed forward move from entry over horizon H, in the reaction direction;
  - entry is strictly AFTER the direction window (no overlap -> no conditioning leak).
Mid proxy = trade price (Stage 1 is mid-based; Stage 2 will charge the actual widened touch).

Cells (<=12, pre-registered): reaction_delay in {1,5,30}s x H in {120,600}s. The 1s delay is the COLO-decay
probe (if the edge lives only at ~1s it's the speed game we can't play at 0.5-1.5ms).
Reports per event-type (FOMC/NFP/CPI) and pooled-08:30: mean continuation (ticks), %continued, t-stat, n;
leave-one-out (does dropping ANY single event flip the pooled sign?); the delay-decay curve.
KILL (Stage 1): pooled mean continuation < ~2t OR %continued ~50% (no direction) OR LOO-fragile -> stop
before modeling spread. PASS -> Stage 2 (widened spread + fill-rate).
Reads data/zb_macro_events.csv (frozen). Months are fanned across a process pool (independent files).
"""
from __future__ import annotations

import os

# cap BLAS/OpenMP threads per worker BEFORE numpy import so a pool of workers does not oversubscribe cores
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
LAT = 1_000_000  # 1 ms
DELAYS = [1, 5, 30]      # reaction-delay seconds (1s = colo-decay probe)
HORIZONS = [120, 600]    # hold seconds (2 min, 10 min)
NPROC = 10               # one per physical core; ~1.5 GB/worker, single shared network share
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
    """Worker: load one month, return [(delay, H, type, contaminated, cont_ticks), ...] for its events."""
    mk, events = arg
    a = load_events(month_path(mk))
    istr = action(a["ev"]).astype(np.int64) == TRADE
    tts, tpx = a["exch_ts"][istr], a["px"][istr]
    out = []
    for e in events:
        t0 = e["t"]
        p0 = px_at(tts, tpx, t0)
        for d in DELAYS:
            pr = px_at(tts, tpx, t0 + d * SEC)
            if not np.isfinite(pr):
                continue
            direction = np.sign(pr - p0)
            if direction == 0:
                continue
            entry = px_at(tts, tpx, t0 + d * SEC + LAT)
            for h in HORIZONS:
                exit_px = px_at(tts, tpx, t0 + d * SEC + LAT + h * SEC)
                if not (np.isfinite(entry) and np.isfinite(exit_px)):
                    continue
                out.append((d, h, e["type"], e["contaminated"], float((exit_px - entry) / TICK * direction)))
    return mk, out


def stats(vals):
    v = np.array(vals, float)
    if len(v) < 5:
        return f"n={len(v)} (too few)"
    se = v.std(ddof=1) / np.sqrt(len(v))
    return f"n={len(v):3d} mean={v.mean():+5.2f}t med={np.median(v):+5.2f}t %cont={np.mean(v > 0):4.2f} t={v.mean() / se:+5.2f}"


def main():
    evs = load_calendar()
    bymonth = defaultdict(list)
    for e in evs:
        bymonth[e["date"][:7]].append(e)
    items = sorted(bymonth.items())
    nproc = min(NPROC, len(items))
    print(f"loading {len(items)} months across {nproc} workers...", flush=True)
    data = {(d, h): [] for d in DELAYS for h in HORIZONS}
    with mp.Pool(nproc) as pool:
        for mk, res in pool.imap_unordered(process_month, items):
            for (d, h, typ, ct, cont) in res:
                data[(d, h)].append((typ, ct, cont))
            print(f"  done {mk} ({len(res)} obs)", flush=True)

    print("\n=== Stage-1 event continuation (MID-BASED, no spread) ===")
    for d in DELAYS:
        for h in HORIZONS:
            rows = data[(d, h)]
            print(f"\n-- reaction_delay={d}s  hold={h}s --")
            for typ in ("FOMC", "NFP", "CPI"):
                vals = [c for (t, _, c) in rows if t == typ]
                print(f"   {typ:5s}: {stats(vals)}")
            cpi_clean = [c for (t, ct, c) in rows if t == "CPI" and not ct]
            pooled = [c for (t, ct, c) in rows if t == "NFP" or (t == "CPI" and not ct)]
            print(f"   CPI(clean): {stats(cpi_clean)}")
            print(f"   POOL 08:30: {stats(pooled)}")

    hl = [c for (t, ct, c) in data[(5, 600)] if t in ("FOMC", "NFP") or (t == "CPI" and not ct)]
    if len(hl) >= 5:
        v = np.array(hl, float)
        loo = [np.delete(v, i).mean() for i in range(len(v))]
        print(f"\nLOO (delay5/hold600, ALL types pooled): mean={v.mean():+.2f}t  "
              f"LOO range=[{min(loo):+.2f},{max(loo):+.2f}]  sign-stable={'YES' if min(loo) * max(loo) > 0 else 'NO -- FRAGILE'}")
    print("\n[Stage-1 mid-based; KILL if pooled mean <~2t or %cont ~0.5 or LOO sign-flips. PASS -> widened-spread Stage 2]")


if __name__ == "__main__":
    main()
