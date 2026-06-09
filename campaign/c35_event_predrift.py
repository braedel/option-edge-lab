"""PRE-announcement drift test -- the mirror image of c34, and latency-immune by construction (you enter
and EXIT before the colo spike). In equities the pre-FOMC drift (Lucca-Moench) is a documented anomaly:
prices drift systematically in the 24h before the decision. This tests the ZB analog: is there a SYSTEMATIC
(unconditional) directional move into NFP/FOMC/CPI that you could harvest with a scheduled entry?

Tradeable form: enter at t - W_pre, EXIT at t - 60s (flat before the release, never touching the spike).
raw = signed price move over that window (positive = ZB rallied into the event). A nonzero, sign-stable
mean that beats the ~1.13t cost = a slow, scheduled, latency-immune edge (always-long or always-short into
the event by type). No direction-conditioning, so the null is simply mean=0; LOO guards against one-event
drivers. Run on local mirror (ZB_DATA_ROOT). Reads frozen calendar.
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
MIN = 60 * SEC
PRE_WINDOWS = [30, 60, 120, 240]    # minutes before the event to enter
EXIT_LEAD = 60                      # exit this many SECONDS before t (stay clear of the spike)
NPROC = 10
CAL = Path("data/zb_macro_events.csv")
FEE_T = 4.0 / 31.25


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
        t0 = e["t"]
        exit_px = px_at(tts, tpx, t0 - EXIT_LEAD * SEC)
        if not np.isfinite(exit_px):
            continue
        for w in PRE_WINDOWS:
            entry = px_at(tts, tpx, t0 - w * MIN)
            if not np.isfinite(entry):
                continue
            raw = (exit_px - entry) / TICK                  # + = rallied into the event
            out.append((w, e["type"], e["contaminated"], float(raw)))
    return mk, out


def stat(vals):
    v = np.array(vals, float)
    if len(v) < 5:
        return f"n={len(v)} (few)"
    se = v.std(ddof=1) / np.sqrt(len(v))
    return (f"n={len(v):3d} mean={v.mean():+6.2f}t med={np.median(v):+6.2f}t %up={np.mean(v > 0):.2f} "
            f"t={v.mean() / se:+5.2f} net|dir|={abs(v.mean()) - FEE_T:+.2f}t")


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

    print("\n=== PRE-announcement drift (enter t-W, exit t-60s; +=rallied in; net|dir| vs 1.13t cost) ===")
    for w in PRE_WINDOWS:
        sub = [(r[1], r[2], r[3]) for r in rows if r[0] == w]
        print(f"\n-- enter t-{w}min, exit t-60s --")
        for typ in ("FOMC", "NFP", "CPI"):
            print(f"   {typ:5s}: {stat([c for (t, _, c) in sub if t == typ])}")
        print(f"   CPI(clean): {stat([c for (t, ct, c) in sub if t == 'CPI' and not ct])}")
        print(f"   POOL all : {stat([c for (t, ct, c) in sub if t in ('FOMC', 'NFP') or (t == 'CPI' and not ct)])}")

    # LOO on the by-type cell with the largest |mean| at the 60min window (the most plausible scheduled bet)
    w = 60
    best, bestv = None, 0.0
    for typ in ("FOMC", "NFP", "CPI"):
        v = np.array([r[3] for r in rows if r[0] == w and r[1] == typ], float)
        if len(v) >= 5 and abs(v.mean()) > abs(bestv):
            best, bestv = typ, v.mean()
    if best:
        v = np.array([r[3] for r in rows if r[0] == w and r[1] == best], float)
        loo = [np.delete(v, i).mean() for i in range(len(v))]
        print(f"\nLOO (best by |mean| @t-{w}min = {best}, mean={v.mean():+.2f}t): "
              f"range=[{min(loo):+.2f},{max(loo):+.2f}]  sign-stable={'YES' if min(loo) * max(loo) > 0 else 'NO -- FRAGILE'}")
    print("\n[A sign-stable mean that beats cost = a scheduled, latency-immune pre-event edge. "
          "Combine with c34 post-drift for a multi-leg announcement strategy if both survive.]")


if __name__ == "__main__":
    main()
