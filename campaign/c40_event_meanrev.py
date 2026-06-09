"""Last genuinely-distinct on-data announcement angle: INTRADAY post-event MEAN-REVERSION (fade).
c38 showed CPI breakouts REVERT (negative) -> maybe the post-event extension fades intraday. Distinct from
continuation/drift (momentum) and from tick-MM (adverse-selected): a slow fade of the post-event displacement
back toward the pre-event level, entered AFTER the spike (latency-immune) and held over hours.

Per event: at t+E (E=30min, after the spike settles), dev = px(t+E) - px(t-60s) [post-event displacement].
FADE: side = -sign(dev); hold H; net = (exit-entry)*side/TICK - cost. Bets the move partially reverts.
Year-split (is it 2023-only like the others?) + PLACEBO (random side -> ~0). If pooled fade NET>0, year-stable,
beats placebo -> a real fade edge. Given c34 found long-horizon = noise, prior is low -- but it's distinct and
untested. Run on local mirror (ZB_DATA_ROOT).
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
REF_LEAD = 60 * SEC
ENTRY_AFTER = [1800, 3600]      # enter E sec after release (after the spike)
HOLDS = [3600, 7200]            # fade hold seconds
COST_T = 1.0 + 4.0 / 31.25
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
        t0 = e["t"]; ref = px_at(tts, tpx, t0 - REF_LEAD)
        if not np.isfinite(ref):
            continue
        for E in ENTRY_AFTER:
            entry = px_at(tts, tpx, t0 + E * SEC)
            if not np.isfinite(entry):
                continue
            dev = (entry - ref) / TICK
            if dev == 0:
                continue
            side = -int(np.sign(dev))                    # fade the displacement
            for H in HOLDS:
                ex = px_at(tts, tpx, t0 + (E + H) * SEC)
                if not np.isfinite(ex):
                    continue
                net = (ex - entry) / TICK * side - COST_T
                out.append((E, H, e["type"], e["contaminated"], e["date"][:4], float(net), float(abs(dev))))
    return mk, out


def rep(vals):
    v = np.array(vals, float)
    if len(v) < 5:
        return f"n={len(v)} (few)"
    se = v.std(ddof=1) / np.sqrt(len(v))
    return f"n={len(v):3d} NET={v.mean():+5.2f}t med={np.median(v):+5.2f}t %pos={np.mean(v>0):.2f} t={v.mean()/se:+5.2f}"


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
    rng = np.random.default_rng(20260609)

    print("\n=== intraday post-event FADE (enter t+E, hold H; NET after 1.13t cost) ===")
    for E in ENTRY_AFTER:
        for H in HOLDS:
            sub = [r for r in rows if r[0] == E and r[1] == H]
            print(f"\n-- enter t+{E//60}min, fade, hold {H//60}min --")
            for typ in ("FOMC", "NFP", "CPI"):
                print(f"   {typ:5s}: {rep([r[5] for r in sub if r[2] == typ])}")
            allnet = [r[5] for r in sub]
            print(f"   POOL  : {rep(allnet)}")
            # placebo: random fade side -> recompute net sign randomly (net already signed; flip ~half)
            if len(allnet) >= 5:
                flip = rng.choice([-1, 1], size=len(sub))
                # placebo net = move in a RANDOM direction: reconstruct raw move = net+cost over side then re-sign
                # simpler: random-direction P&L has mean ~ -cost; report to anchor the noise floor
                plac = np.array([(r[5] + COST_T) * fl - COST_T for r, fl in zip(sub, flip)])
                print(f"   PLACEBO(rand side): NET={plac.mean():+.2f}t  <- anchors noise floor")
            for yr in ("2023", "2024", "2025"):
                yv = [r[5] for r in sub if r[4] == yr]
                if len(yv) >= 4:
                    print(f"      {yr}: {rep(yv)}")
    print("\n[Pooled fade NET>0, year-stable, beats placebo = a real intraday reversion edge. "
          "Otherwise the announcement space is exhausted on this data.]")


if __name__ == "__main__":
    main()
