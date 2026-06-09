"""Vet the one real lead: NFP breakout (direction-agnostic, latency-immune, positive in all c38 cells).
Same scrutiny pre-CPI got: per-event P&L series, year-by-year stability (decay like pre-CPI?), broad-vs-
outlier (mean vs median, trimmed mean), implied annualized Sharpe + max drawdown, and an EXPLICIT power
statement (how many events to confirm t>2). IN-SAMPLE only -- does NOT spend the sealed OOS.

Bracket K=3t (fixed, mid of the c38 sweep), ref t-60s, breach within 10min, fill=breach+1t slip, hold H,
exit cross. Honest: if it's year-stable + broad + decent Sharpe -> a forward-paper candidate (the only way
past the power wall). If it decays or is outlier-driven -> another mirage. Run on local mirror (ZB_DATA_ROOT).
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

from options_lab.zb_mbo.codes import TRADE, action
from options_lab.zb_mbo.loader import load_events, month_path
from options_lab.zb_mbo.stream import TICK

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
SEC = 1_000_000_000
REF_LEAD = 60 * SEC
TRIGGER_WIN = 600 * SEC
K = 3
HOLDS = [120, 600, 1800]
SLIP_T = 1.0
EXIT_COST_T = 1.0 + 4.0 / 31.25
NPROC = 10
CAL = Path("data/zb_macro_events.csv")
DOLLAR = 31.25


def utc_ns(date_str, time_et):
    d = dt.date.fromisoformat(date_str)
    hh, mm = map(int, time_et.split(":"))
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC).timestamp() * 1e9)


def load_nfp():
    out = []
    for r in csv.DictReader(open(CAL)):
        if r["event"] == "NFP" and r["pinning"] != "NOT_FOUND" and len(r["date"]) == 10:
            out.append(r["date"])
    return out


def px_at(tts, tpx, t):
    j = np.searchsorted(tts, t, "right") - 1
    return float(tpx[j]) if j >= 0 else np.nan


def process_month(arg):
    mk, dates = arg
    a = load_events(month_path(mk))
    istr = action(a["ev"]).astype(np.int64) == TRADE
    tts, tpx = a["exch_ts"][istr], a["px"][istr]
    out = []
    for ds in dates:
        t0 = utc_ns(ds, "08:30")
        ref = px_at(tts, tpx, t0 - REF_LEAD)
        if not np.isfinite(ref):
            continue
        lo = np.searchsorted(tts, t0, "left"); hi = np.searchsorted(tts, t0 + TRIGGER_WIN, "right")
        seg_ts, seg_px = tts[lo:hi], tpx[lo:hi]
        up, dn = ref + K * TICK, ref - K * TICK
        hu = np.flatnonzero(seg_px >= up - 1e-9); hd = np.flatnonzero(seg_px <= dn + 1e-9)
        iu = hu[0] if hu.size else None; idn = hd[0] if hd.size else None
        if iu is None and idn is None:
            continue
        side, j = (1, iu) if (idn is None or (iu is not None and iu <= idn)) else (-1, idn)
        fill_t = seg_ts[j]; entry = seg_px[j] + side * SLIP_T * TICK
        nets = {}
        for H in HOLDS:
            ex = px_at(tts, tpx, fill_t + H * SEC)
            nets[H] = ((ex - entry) / TICK * side - EXIT_COST_T) if np.isfinite(ex) else np.nan
        out.append((ds, nets))
    return out


def main():
    nfp = load_nfp()
    bymonth = {}
    for ds in nfp:
        bymonth.setdefault(ds[:7], []).append(ds)
    items = sorted(bymonth.items())
    nproc = min(NPROC, len(items))
    print(f"loading {len(items)} NFP months across {nproc} workers (K={K}t bracket)...", flush=True)
    rows = []
    with mp.Pool(nproc) as pool:
        for res in pool.imap_unordered(process_month, items):
            rows.extend(res)
    rows.sort(key=lambda r: r[0])

    for H in HOLDS:
        v = np.array([r[1][H] for r in rows if np.isfinite(r[1].get(H, np.nan))])
        if len(v) < 5:
            continue
        se = v.std(ddof=1) / np.sqrt(len(v))
        sharpe = v.mean() / v.std(ddof=1) * np.sqrt(11)              # ~11 NFP/yr
        eq = np.cumsum(v); dd = float((np.maximum.accumulate(eq) - eq).max())
        trim = np.sort(v)[1:-1]
        n_needed = int((2 * v.std(ddof=1) / max(abs(v.mean()), 1e-9)) ** 2)
        print(f"\n== NFP breakout K={K}t hold={H//60}min ==")
        print(f"  n={len(v)} mean={v.mean():+.2f}t med={np.median(v):+.2f}t trimmed_mean={trim.mean():+.2f}t "
              f"%pos={np.mean(v>0):.2f} t={v.mean()/se:+.2f}")
        print(f"  ~${v.mean()*DOLLAR:+.0f}/event  annualized Sharpe~{sharpe:+.2f} (11/yr)  maxDD={dd:.1f}t (${dd*DOLLAR:.0f})")
        print(f"  POWER: to reach t=2 vs this variance need ~{n_needed} events (~{n_needed/11:.0f} yrs) -> "
              f"{'CONFIRMABLE here' if n_needed <= len(v) else 'NOT confirmable on this data'}")
        for yr in ("2023", "2024", "2025"):
            yv = np.array([r[1][H] for r in rows if r[0][:4] == yr and np.isfinite(r[1].get(H, np.nan))])
            if len(yv):
                print(f"    {yr}: n={len(yv):2d} mean={yv.mean():+.2f}t %pos={np.mean(yv>0):.2f}")

    print("\n-- per-event series (hold=30min) --")
    for r in rows:
        if np.isfinite(r[1].get(1800, np.nan)):
            print(f"   {r[0]}: {r[1][1800]:+6.1f}t")
    print("\n[year-stable + broad (mean~trimmed) + decent Sharpe = forward-paper candidate despite the power wall. "
          "Decaying/outlier-driven = mirage.]")


if __name__ == "__main__":
    main()
