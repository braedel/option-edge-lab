"""#1 OOS TEST of the frozen surprise-direction rule, on the post-in-sample window 2025-10..2026-04
(everything after the 2025-09 in-sample cutoff). Rule (FROZEN, from c42): enter -sign(surprise) at t+5min,
hold 60min, NET after 1.13t cost; CPI/NFP at 08:30 ET, FOMC at 14:00 ET.

** HEAVY CAVEAT: this OOS window is shutdown-distorted ** -- a 43-44d US govt shutdown (~Oct 1->mid-Nov 2025)
+ a 2nd shutdown (early Feb 2026) delayed/combined releases (Oct-2025 CPI never produced; Sep NFP->Nov 20;
Oct+Nov NFP combined Dec 16), and an Iran energy shock (Feb-Mar 2026) distorted headline inflation. So this
is a CONFOUNDED, low-power (~9-13 events) sign-check, NOT a clean validation. Forward paper in a normal regime
is the real test. Surprise data: deep-research, CNBC/Dow-Jones + multi-outlet verified.
Run on local mirror (ZB_DATA_ROOT).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import datetime as dt
import multiprocessing as mp
from collections import defaultdict
from zoneinfo import ZoneInfo

import numpy as np

from options_lab.zb_mbo.codes import TRADE, action
from options_lab.zb_mbo.loader import load_events, month_path
from options_lab.zb_mbo.stream import TICK

ET = ZoneInfo("America/New_York")
SEC = 1_000_000_000
SPIKE_AFTER = 300 * SEC
HOLD = 3600 * SEC
COST_T = 1.0 + 4.0 / 31.25
DOLLAR = 31.25
NPROC = 8
NFP_BIG = 80.0   # k (in-sample ~1 sigma)

# OOS events: (release_date, type, hh, mm, surprise) -- surprise sign drives direction (-sign)
OOS = [
    # CPI core MoM surprise (pp); 08:30 ET
    ("2025-10-24", "CPI", 8, 30, -0.1), ("2025-12-18", "CPI", 8, 30, -0.1),
    ("2026-01-13", "CPI", 8, 30, -0.1), ("2026-02-13", "CPI", 8, 30, 0.0),
    ("2026-03-11", "CPI", 8, 30, 0.0), ("2026-04-10", "CPI", 8, 30, -0.1),
    # NFP surprise (k); 08:30 ET (shutdown-distorted dates)
    ("2025-11-20", "NFP", 8, 30, 69), ("2025-12-16", "NFP", 8, 30, 19),
    ("2026-01-09", "NFP", 8, 30, -23), ("2026-02-11", "NFP", 8, 30, 75),
    ("2026-03-06", "NFP", 8, 30, -142), ("2026-04-03", "NFP", 8, 30, 119),
    # FOMC hawkish(+1)/dovish(-1)/neutral(0); 14:00 ET
    ("2025-10-29", "FOMC", 14, 0, 1), ("2025-12-10", "FOMC", 14, 0, 0),
    ("2026-01-28", "FOMC", 14, 0, 1), ("2026-03-18", "FOMC", 14, 0, 1),
    ("2026-04-29", "FOMC", 14, 0, 0),
]


def utc_ns(date_str, hh, mm):
    d = dt.date.fromisoformat(date_str)
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(dt.timezone.utc).timestamp() * 1e9)


def is_big(typ, s):
    if typ == "CPI":
        return abs(s) >= 0.1
    if typ == "NFP":
        return abs(s) >= NFP_BIG
    return abs(s) >= 1            # FOMC: any hawkish/dovish label


def px_at(tts, tpx, t):
    j = np.searchsorted(tts, t, "right") - 1
    return float(tpx[j]) if j >= 0 else np.nan


def process_month(arg):
    mk, evs = arg
    a = load_events(month_path(mk))
    istr = action(a["ev"]).astype(np.int64) == TRADE
    tts, tpx = a["exch_ts"][istr], a["px"][istr]
    out = []
    for date, typ, hh, mm, s in evs:
        if s == 0:
            continue
        t0 = utc_ns(date, hh, mm)
        entry = px_at(tts, tpx, t0 + SPIKE_AFTER)
        ex = px_at(tts, tpx, t0 + SPIKE_AFTER + HOLD)
        if not (np.isfinite(entry) and np.isfinite(ex)):
            continue
        net = (ex - entry) / TICK * (-np.sign(s)) - COST_T
        out.append((date, typ, float(s), is_big(typ, s), float(net)))
    return out


def show(rows, label):
    v = np.array([r[4] for r in rows], float)
    if len(v) == 0:
        print(f"  {label}: no events"); return
    se = v.std(ddof=1) / np.sqrt(len(v)) if len(v) > 1 else float("nan")
    print(f"  {label}: n={len(v)} NET/trade=${v.mean()*DOLLAR:+.0f} total=${v.sum()*DOLLAR:+.0f} "
          f"%pos={np.mean(v>0):.2f} mean={v.mean():+.2f}t" + (f" t={v.mean()/se:+.2f}" if len(v) > 1 and se else ""))


def main():
    bymonth = defaultdict(list)
    for e in OOS:
        bymonth[e[0][:7]].append(e)
    items = sorted(bymonth.items())
    print(f"OOS test: loading {len(items)} months 2025-10..2026-04 (shutdown-distorted window)...", flush=True)
    rows = []
    with mp.Pool(min(NPROC, len(items))) as pool:
        for res in pool.imap_unordered(process_month, items):
            rows.extend(res)
    rows.sort(key=lambda r: r[0])

    print("\n=== OOS per-event (frozen rule; CONFOUNDED by shutdown -- read as a weak sign-check) ===")
    for r in rows:
        flag = "BIG" if r[3] else "sml"
        print(f"  {r[0]} {r[1]:4s} surp={r[2]:+7.2f} {flag}  net=${r[4]*DOLLAR:+5.0f}")
    print("\n=== OOS aggregates vs in-sample (in-sample big-surprise 60min: NET/trade ~+$115, Sharpe ~1.0) ===")
    show(rows, "ALL OOS events")
    show([r for r in rows if r[3]], "BIG-surprise OOS (the traded set)")
    for typ in ("CPI", "NFP", "FOMC"):
        show([r for r in rows if r[1] == typ and r[3]], f"  {typ} big")
    print("\n[Caveat: shutdown/energy-distorted, ~9 big events -> directional sign-check only, not validation. "
          "A positive sign here is encouraging but NOT proof; forward paper in a normal regime is the real OOS.]")


if __name__ == "__main__":
    main()
