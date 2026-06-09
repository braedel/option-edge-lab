"""Surprise-conditioned post-event drift -- the last on-data angle, using NEW information the price-only
tests could not see: the ACTUAL-vs-CONSENSUS surprise (CNBC/Dow-Jones consensus, BLS-verified; assembled
by deep research). Mechanism: a CPI/NFP BEAT (surprise>0) is hawkish -> yields up -> ZB DOWN, so the
expected ZB direction = -sign(surprise). We concede the colo spike; we ENTER at t+5min (post-spike,
latency-immune) in the surprise direction and hold H.

Tests:
  (1) CONSISTENCY: does the spike actually go -sign(surprise)? (validates data + mechanism)
  (2) PEAD analog: post-spike drift in the surprise direction, split by surprise MAGNITUDE (big vs small) --
      do BIG surprises keep drifting (positions adjust over hours) while small ones don't?
  (3) DIVERGENCE: when the spike went OPPOSITE the surprise (priced-in / buy-the-news), continue or revert?
Per type + pool, year-split (2023-only like the others?), honest power note. NET after 1.13t cost.
Run on local mirror (ZB_DATA_ROOT). Surprise tables hardcoded from the verified research output.
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
UTC = dt.timezone.utc
SEC = 1_000_000_000
REF_LEAD = 60 * SEC
SPIKE_AFTER = 300 * SEC          # enter 5 min post-release (concede the spike)
HOLDS = [1800, 3600, 7200]       # 30/60/120 min
COST_T = 1.0 + 4.0 / 31.25
NPROC = 10

# core CPI MoM surprise (actual-consensus, %), release date -> surprise
SURP_CPI = {
    "2023-01-12": 0.1, "2023-02-14": 0.1, "2023-03-14": 0.1, "2023-04-12": 0.0, "2023-05-10": 0.0,
    "2023-06-13": 0.0, "2023-07-12": -0.1, "2023-08-10": 0.0, "2023-09-13": 0.1, "2023-10-12": 0.0,
    "2023-11-14": -0.1, "2023-12-12": 0.0, "2024-01-11": 0.0, "2024-02-13": 0.1, "2024-03-12": 0.1,
    "2024-04-10": 0.1, "2024-05-15": 0.0, "2024-06-12": -0.1, "2024-07-11": -0.1, "2024-08-14": 0.0,
    "2024-09-11": 0.1, "2024-10-10": 0.1, "2024-11-13": 0.0, "2024-12-11": 0.0, "2025-01-15": -0.1,
    "2025-02-12": 0.1, "2025-03-12": -0.1, "2025-05-13": -0.1, "2025-06-11": -0.2, "2025-07-15": -0.1,
    "2025-08-12": 0.0, "2025-09-11": 0.0,
}
# NFP headline surprise (actual-consensus, thousands)
SURP_NFP = {
    "2023-01-06": 23, "2023-02-03": 330, "2023-03-10": 86, "2023-04-07": -2, "2023-05-05": 73,
    "2023-06-02": 149, "2023-07-07": -31, "2023-08-04": -13, "2023-09-01": 17, "2023-10-06": 166,
    "2023-11-03": -20, "2023-12-08": 9, "2024-01-05": 46, "2024-02-02": 168, "2024-03-08": 77,
    "2024-04-05": 103, "2024-05-03": -65, "2024-06-07": 82, "2024-07-05": 6, "2024-08-02": -71,
    "2024-09-06": -19, "2024-10-04": 104, "2024-11-01": -88, "2024-12-06": 13, "2025-01-10": 101,
    "2025-02-07": -26, "2025-03-07": -19, "2025-05-02": 44, "2025-06-06": 14, "2025-08-01": -27,
    "2025-09-05": -53,
}
NFP_STD = float(np.std(list(SURP_NFP.values())))   # for standardizing the magnitude split


def utc_ns(date_str, hh, mm):
    d = dt.date.fromisoformat(date_str)
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC).timestamp() * 1e9)


def px_at(tts, tpx, t):
    j = np.searchsorted(tts, t, "right") - 1
    return float(tpx[j]) if j >= 0 else np.nan


def process_month(arg):
    mk, events = arg            # events: list of (date, type, surprise)
    a = load_events(month_path(mk))
    istr = action(a["ev"]).astype(np.int64) == TRADE
    tts, tpx = a["exch_ts"][istr], a["px"][istr]
    out = []
    for date, typ, surp in events:
        t0 = utc_ns(date, 8, 30)
        ref = px_at(tts, tpx, t0 - REF_LEAD)
        p_spk = px_at(tts, tpx, t0 + SPIKE_AFTER)
        if not (np.isfinite(ref) and np.isfinite(p_spk)):
            continue
        spike = (p_spk - ref) / TICK
        exp = -np.sign(surp)                       # beat(+surp)->ZB down(-1)
        for H in HOLDS:
            ex = px_at(tts, tpx, t0 + SPIKE_AFTER + H * SEC)
            if not np.isfinite(ex):
                continue
            drift = (ex - p_spk) / TICK            # raw post-spike move
            out.append((date, typ, float(surp), H, float(spike), float(drift), float(exp)))
    return out


def rep(net):
    v = np.array(net, float)
    if len(v) < 4:
        return f"n={len(v)} (few)"
    se = v.std(ddof=1) / np.sqrt(len(v))
    if se == 0:
        return f"n={len(v):3d} NET={v.mean():+5.2f}t (zero variance -- check units)"
    return f"n={len(v):3d} NET={v.mean():+5.2f}t med={np.median(v):+5.2f}t %pos={np.mean(v>0):.2f} t={v.mean()/se:+5.2f}"


def main():
    events = [(d, "CPI", s) for d, s in SURP_CPI.items()] + [(d, "NFP", s) for d, s in SURP_NFP.items()]
    bymonth = defaultdict(list)
    for d, typ, s in events:
        bymonth[d[:7]].append((d, typ, s))
    items = sorted(bymonth.items())
    nproc = min(NPROC, len(items))
    print(f"loading {len(items)} months across {nproc} workers (CPI+NFP surprise-conditioned)...", flush=True)
    rows = []
    with mp.Pool(nproc) as pool:
        for res in pool.imap_unordered(process_month, items):
            rows.extend(res)
    print(f"events with data: {len({(r[0]) for r in rows})}")

    # (1) CONSISTENCY: does the spike go -sign(surprise)? (use one H, exclude in-line surprise=0)
    print("\n(1) spike vs surprise consistency (spike sign == -sign(surprise); in-line excluded):")
    for typ in ("CPI", "NFP"):
        s = [(r[4], r[6]) for r in rows if r[1] == typ and r[3] == HOLDS[0] and r[2] != 0]
        if s:
            cons = np.mean([np.sign(sp) == ex for sp, ex in s])
            print(f"   {typ}: n={len(s)} consistent={cons:.2f}  mean|spike|={np.mean([abs(sp) for sp,_ in s]):.1f}t")

    # (2) PEAD: post-spike drift in the SURPRISE direction, split by |surprise| magnitude
    print("\n(2) post-spike drift in surprise direction (enter t+5min, NET after cost):")
    for H in HOLDS:
        print(f"  -- hold {H//60}min --")
        for typ in ("CPI", "NFP"):
            sub = [r for r in rows if r[1] == typ and r[3] == H and r[2] != 0]
            if typ == "CPI":
                big = [r for r in sub if abs(r[2]) >= 0.1]; small = []   # CPI surprises are coarse; >=0.1 = any real surprise
            else:
                big = [r for r in sub if abs(r[2]) >= NFP_STD]; small = [r for r in sub if abs(r[2]) < NFP_STD]
            net_all = [r[5] * r[6] - COST_T for r in sub]
            net_big = [r[5] * r[6] - COST_T for r in big]
            print(f"   {typ} all : {rep(net_all)}")
            print(f"   {typ} BIG : {rep(net_big)}")
            if small:
                print(f"   {typ} small: {rep([r[5]*r[6]-COST_T for r in small])}")
    # pooled BIG-surprise, year split (the PEAD candidate)
    print("\n  pooled BIG-surprise drift (hold 60min) by year:")
    for yr in ("2023", "2024", "2025"):
        b = [r[5]*r[6]-COST_T for r in rows if r[3] == 3600 and r[2] != 0 and r[0][:4] == yr
             and ((r[1] == "CPI" and abs(r[2]) >= 0.1) or (r[1] == "NFP" and abs(r[2]) >= NFP_STD))]
        if len(b) >= 3:
            print(f"     {yr}: {rep(b)}")

    # (3) DIVERGENCE: spike opposed the surprise -> continue (spike dir) or revert?
    print("\n(3) divergence (spike went OPPOSITE the surprise): post-spike move in SPIKE direction (hold 60min):")
    div = [r for r in rows if r[3] == 3600 and r[2] != 0 and np.sign(r[4]) == -r[6]]   # spike sign != expected
    agree = [r for r in rows if r[3] == 3600 and r[2] != 0 and np.sign(r[4]) == r[6]]
    if div:
        print(f"   diverged n={len(div)}: continue-spike NET={rep([r[5]*np.sign(r[4])-COST_T for r in div])}")
    if agree:
        print(f"   agreed   n={len(agree)}: continue-spike NET={rep([r[5]*np.sign(r[4])-COST_T for r in agree])}")
    print("\n[BIG-surprise drift NET>0, year-stable, beats the price-only null = surprise adds real signal. "
          "Else the announcement space is exhausted even with fundamentals.]")


if __name__ == "__main__":
    main()
