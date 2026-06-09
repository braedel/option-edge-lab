"""Characterize the pre-CPI rally's DECAY: is it a clean regime-trend (2023-only -> not forward-reliable) or
noisy across tiny yearly samples? Dumps the per-CPI-event pre-drift time series (t-30/60/120min, exit 08:29
ET) for every CPI event (clean + contaminated), ordered by date, and fits an OLS trend (drift vs time) on the
CLEAN events. A significant negative slope = genuine decay (document as a faded regime effect); a flat slope
with high scatter = noise (the +3.3t is just luck on 2023's draws). Either way it answers forward-reliability
WITHOUT spending the sealed OOS. Run on local mirror (ZB_DATA_ROOT).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import csv
import datetime as dt
import multiprocessing as mp
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from scipy import stats

from options_lab.zb_mbo.codes import TRADE, action
from options_lab.zb_mbo.loader import load_events, month_path
from options_lab.zb_mbo.stream import TICK

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
SEC = 1_000_000_000
MIN = 60 * SEC
NPROC = 10
CAL = Path("data/zb_macro_events.csv")


def hhmm_utc(d, hh, mm):
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC).timestamp() * 1e9)


def load_cpi():
    out = []
    for r in csv.DictReader(open(CAL)):
        if r["event"] == "CPI" and r["pinning"] != "NOT_FOUND" and len(r["date"]) == 10:
            out.append((r["date"], r["contaminated"] == "True"))
    return out


def px_at(tts, tpx, t):
    j = np.searchsorted(tts, t, "right") - 1
    return float(tpx[j]) if j >= 0 else np.nan


def process_month(arg):
    mk, cpis = arg
    a = load_events(month_path(mk))
    istr = action(a["ev"]).astype(np.int64) == TRADE
    tts, tpx = a["exch_ts"][istr], a["px"][istr]
    out = []
    for date_str, contam in cpis:
        d = dt.date.fromisoformat(date_str)
        exit_px = px_at(tts, tpx, hhmm_utc(d, 8, 29))
        row = {"date": date_str, "contam": contam}
        for lab, hh, mm in [(30, 8, 0), (60, 7, 30), (120, 6, 30)]:
            e = px_at(tts, tpx, hhmm_utc(d, hh, mm))
            row[lab] = (exit_px - e) / TICK if (np.isfinite(e) and np.isfinite(exit_px)) else np.nan
        out.append(row)
    return out


def main():
    cpi = load_cpi()
    bymonth = {}
    for date_str, contam in cpi:
        bymonth.setdefault(date_str[:7], []).append((date_str, contam))
    items = sorted(bymonth.items())
    nproc = min(NPROC, len(items))
    print(f"loading {len(items)} CPI months across {nproc} workers...", flush=True)
    rows = []
    with mp.Pool(nproc) as pool:
        for res in pool.imap_unordered(process_month, items):
            rows.extend(res)
    rows.sort(key=lambda r: r["date"])

    print("\n=== per-CPI-event pre-drift time series (t-60min, exit 08:29 ET) ===")
    print("date        clean?  d30      d60     d120")
    for r in rows:
        flag = "CONTAM" if r["contam"] else "clean "
        print(f"  {r['date']}  {flag}  {r[30]:+6.1f}t {r[60]:+6.1f}t {r[120]:+6.1f}t")

    clean = [r for r in rows if not r["contam"] and np.isfinite(r[60])]
    if len(clean) >= 4:
        d0 = dt.date.fromisoformat(clean[0]["date"])
        x = np.array([(dt.date.fromisoformat(r["date"]) - d0).days / 365.25 for r in clean])
        y = np.array([r[60] for r in clean])
        lr = stats.linregress(x, y)
        print(f"\nCLEAN events (n={len(clean)}): mean d60={y.mean():+.2f}t")
        print(f"OLS drift~years: slope={lr.slope:+.2f}t/yr (p={lr.pvalue:.3f}), intercept(2023 start)={lr.intercept:+.2f}t, "
              f"r2={lr.rvalue**2:.2f}")
        # implied current level at the most-recent clean event
        x_last = x.max()
        print(f"implied level at last clean event (~{clean[-1]['date']}): {lr.intercept + lr.slope * x_last:+.2f}t")
        # split-half: first half vs second half mean (robust to the linear assumption)
        h = len(y) // 2
        print(f"split-half: first {h} mean={y[:h].mean():+.2f}t  vs  last {len(y)-h} mean={y[h:].mean():+.2f}t")
    print("\n[Negative significant slope / collapsing split-half -> faded regime effect, not forward-reliable. "
          "Flat slope + high scatter -> the pooled +3.3t was 2023 luck. Either way: do not burn the seal on it.]")


if __name__ == "__main__":
    main()
