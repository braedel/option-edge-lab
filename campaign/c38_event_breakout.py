"""Announcement BREAKOUT via resting brackets -- the owner's actual "straddle the news" thesis, and the one
on-mandate angle that is BOTH untested and structurally latency-immune: the bracket orders are placed BEFORE
the release, so no reaction latency is needed (the resting stop fills as the spike trades through it).

Direction-agnostic: ref = price at t-60s; place a buy-stop at ref+K and a sell-stop at ref-K. After the
release, the first trade to breach a stop triggers that side (OCO: the other is cancelled). The fill is the
breaching trade price + 1 tick ADVERSE (conservative fast-market slippage). Hold H, exit at the touch
(crossing). net = captured move - 1t entry slip - (1t exit cross + commission). If the spike carries past the
stop by more than the friction, breakout wins; if you just buy the top and it stalls (c32 showed no
continuation), it loses. We TEST it.

Cells: K in {2,3,5} ticks x H in {120,600,1800}s. Per event-type + pool: gross & net, %pos, t. Run on local
mirror (ZB_DATA_ROOT). Reads frozen calendar.
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
REF_LEAD = 60 * SEC          # ref price 60s before the release
TRIGGER_WIN = 600 * SEC      # must break out within 10 min of the release
KS = [2, 3, 5]               # bracket half-width (ticks)
HOLDS = [120, 600, 1800]     # hold seconds
SLIP_T = 1.0                 # adverse entry slippage (ticks) on the stop fill
EXIT_COST_T = 1.0 + 4.0 / 31.25   # exit cross (1t) + commission
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
        t0 = e["t"]
        ref = px_at(tts, tpx, t0 - REF_LEAD)
        if not np.isfinite(ref):
            continue
        # post-release trades within the trigger window
        lo = np.searchsorted(tts, t0, "left")
        hi = np.searchsorted(tts, t0 + TRIGGER_WIN, "right")
        seg_ts, seg_px = tts[lo:hi], tpx[lo:hi]
        for K in KS:
            up, dn = ref + K * TICK, ref - K * TICK
            hit_up = np.flatnonzero(seg_px >= up - 1e-9)
            hit_dn = np.flatnonzero(seg_px <= dn + 1e-9)
            iu = hit_up[0] if hit_up.size else None
            idn = hit_dn[0] if hit_dn.size else None
            if iu is None and idn is None:
                continue                                   # no breakout
            if idn is None or (iu is not None and iu <= idn):
                side, j = 1, iu
            else:
                side, j = -1, idn
            fill_t = seg_ts[j]
            entry = seg_px[j] + side * SLIP_T * TICK        # adverse slip
            for H in HOLDS:
                ex = px_at(tts, tpx, fill_t + H * SEC)
                if not np.isfinite(ex):
                    continue
                gross = (ex - entry) / TICK * side
                net = gross - EXIT_COST_T
                out.append((K, H, e["type"], e["contaminated"], float(gross), float(net)))
    return mk, out


def report(vals_gross, vals_net):
    g, n = np.array(vals_gross, float), np.array(vals_net, float)
    if len(n) < 5:
        return f"n={len(n)} (few)"
    se = n.std(ddof=1) / np.sqrt(len(n))
    return (f"n={len(n):3d} gross={g.mean():+5.2f}t NET={n.mean():+5.2f}t med={np.median(n):+5.2f}t "
            f"%pos={np.mean(n > 0):.2f} t={n.mean() / se:+5.2f}")


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

    print("\n=== announcement breakout (resting bracket; NET = gross - 1t slip - 1.13t exit) ===")
    for K in KS:
        for H in HOLDS:
            sub = [(r[4], r[5], r[2], r[3]) for r in rows if r[0] == K and r[1] == H]
            print(f"\n-- bracket +/-{K}t  hold={H // 60}min --")
            for typ in ("FOMC", "NFP", "CPI"):
                gg = [g for (g, n, t, _) in sub if t == typ]
                nn = [n for (g, n, t, _) in sub if t == typ]
                print(f"   {typ:5s}: {report(gg, nn)}")
            gg = [g for (g, n, t, ct) in sub]
            nn = [n for (g, n, t, ct) in sub]
            print(f"   POOL all : {report(gg, nn)}")
    print("\n[NET>0, sign-stable across K/H/type = a real, latency-immune, direction-agnostic announcement edge. "
          "If gross is large but NET<0, friction kills it; if gross~0, no breakout follow-through.]")


if __name__ == "__main__":
    main()
