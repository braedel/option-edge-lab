"""Consolidate the one promising thread into ONE pre-registered strategy and quantify it honestly.

RULE (simple, from the c41 finding): for each CPI & NFP release, ENTER at t+5min (concede the colo spike) in
the FUNDAMENTAL-surprise direction = -sign(surprise) [beat -> ZB down], HOLD H, exit. This single rule rides
the spike when the reaction agreed with the fundamental and FADES it when the reaction diverged (the c41
divergence result showed the fundamental wins). In-line prints (surprise=0) -> no trade.

Reports, IN-SAMPLE (eligible 2023-01..2025-09; the sealed block is NOT touched -- it's too small to certify
and forward paper is the real validation): per-trade NET, %pos, annualized Sharpe (~22 trades/yr), max
drawdown, year-by-year, hold sensitivity, and a big-surprise filter. Honest power note throughout.
Run on local mirror (ZB_DATA_ROOT). Surprise tables hardcoded (verified).
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
HOLDS = [1800, 3600, 7200]
COST_T = 1.0 + 4.0 / 31.25
DOLLAR = 31.25
NPROC = 10

SURP_CPI = {
    "2023-01-12": 0.1, "2023-02-14": 0.1, "2023-03-14": 0.1, "2023-04-12": 0.0, "2023-05-10": 0.0,
    "2023-06-13": 0.0, "2023-07-12": -0.1, "2023-08-10": 0.0, "2023-09-13": 0.1, "2023-10-12": 0.0,
    "2023-11-14": -0.1, "2023-12-12": 0.0, "2024-01-11": 0.0, "2024-02-13": 0.1, "2024-03-12": 0.1,
    "2024-04-10": 0.1, "2024-05-15": 0.0, "2024-06-12": -0.1, "2024-07-11": -0.1, "2024-08-14": 0.0,
    "2024-09-11": 0.1, "2024-10-10": 0.1, "2024-11-13": 0.0, "2024-12-11": 0.0, "2025-01-15": -0.1,
    "2025-02-12": 0.1, "2025-03-12": -0.1, "2025-05-13": -0.1, "2025-06-11": -0.2, "2025-07-15": -0.1,
    "2025-08-12": 0.0, "2025-09-11": 0.0,
}
SURP_NFP = {
    "2023-01-06": 23, "2023-02-03": 330, "2023-03-10": 86, "2023-04-07": -2, "2023-05-05": 73,
    "2023-06-02": 149, "2023-07-07": -31, "2023-08-04": -13, "2023-09-01": 17, "2023-10-06": 166,
    "2023-11-03": -20, "2023-12-08": 9, "2024-01-05": 46, "2024-02-02": 168, "2024-03-08": 77,
    "2024-04-05": 103, "2024-05-03": -65, "2024-06-07": 82, "2024-07-05": 6, "2024-08-02": -71,
    "2024-09-06": -19, "2024-10-04": 104, "2024-11-01": -88, "2024-12-06": 13, "2025-01-10": 101,
    "2025-02-07": -26, "2025-03-07": -19, "2025-05-02": 44, "2025-06-06": 14, "2025-08-01": -27,
    "2025-09-05": -53,
}
CPI_BIG = 0.1                       # any non-in-line CPI surprise (coarse 0.1% grid)
NFP_BIG = float(np.std(list(SURP_NFP.values())))


def utc_ns(date_str, hh, mm):
    d = dt.date.fromisoformat(date_str)
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(dt.timezone.utc).timestamp() * 1e9)


def px_at(tts, tpx, t):
    j = np.searchsorted(tts, t, "right") - 1
    return float(tpx[j]) if j >= 0 else np.nan


def process_month(arg):
    mk, events = arg
    a = load_events(month_path(mk))
    istr = action(a["ev"]).astype(np.int64) == TRADE
    tts, tpx = a["exch_ts"][istr], a["px"][istr]
    out = []
    for date, typ, surp in events:
        if surp == 0:
            continue
        t0 = utc_ns(date, 8, 30)
        entry = px_at(tts, tpx, t0 + SPIKE_AFTER)
        if not np.isfinite(entry):
            continue
        side = -np.sign(surp)
        big = (abs(surp) >= CPI_BIG) if typ == "CPI" else (abs(surp) >= NFP_BIG)
        for H in HOLDS:
            ex = px_at(tts, tpx, t0 + SPIKE_AFTER + H * SEC)
            if not np.isfinite(ex):
                continue
            net = (ex - entry) / TICK * side - COST_T
            out.append((date, typ, H, bool(big), float(net)))
    return out


def stats(net, per_year=22):
    v = np.array(net, float)
    if len(v) < 4:
        return f"n={len(v)} (few)"
    se = v.std(ddof=1) / np.sqrt(len(v))
    sharpe = v.mean() / v.std(ddof=1) * np.sqrt(per_year) if v.std() else float("nan")
    eq = np.cumsum(v); dd = float((np.maximum.accumulate(eq) - eq).max())
    return (f"n={len(v):3d} NET={v.mean():+5.2f}t (${v.mean()*DOLLAR:+.0f}) %pos={np.mean(v>0):.2f} "
            f"t={v.mean()/se:+4.2f} Sharpe~{sharpe:+4.2f} maxDD={dd:.0f}t(${dd*DOLLAR:.0f})")


def main():
    events = [(d, "CPI", s) for d, s in SURP_CPI.items()] + [(d, "NFP", s) for d, s in SURP_NFP.items()]
    bymonth = defaultdict(list)
    for d, typ, s in events:
        bymonth[d[:7]].append((d, typ, s))
    items = sorted(bymonth.items())
    nproc = min(NPROC, len(items))
    print(f"loading {len(items)} months across {nproc} workers (surprise-direction strategy)...", flush=True)
    rows = []
    with mp.Pool(nproc) as pool:
        for res in pool.imap_unordered(process_month, items):
            rows.extend(res)

    print("\n=== surprise-direction strategy: enter t+5min, side=-sign(surprise), IN-SAMPLE ===")
    for H in HOLDS:
        print(f"\n-- hold {H//60}min (~22 trades/yr) --")
        allnet = [r[4] for r in rows if r[2] == H]
        bignet = [r[4] for r in rows if r[2] == H and r[3]]
        print(f"   ALL non-inline : {stats(allnet)}")
        print(f"   BIG surprises  : {stats(bignet, per_year=12)}")
        for typ in ("CPI", "NFP"):
            print(f"   {typ:3s}            : {stats([r[4] for r in rows if r[2] == H and r[1] == typ], per_year=11)}")
        for yr in ("2023", "2024", "2025"):
            yv = [r[4] for r in rows if r[2] == H and r[0][:4] == yr]
            if len(yv) >= 4:
                print(f"     {yr}: {stats(yv, per_year=22)}")
    print("\n[Year-stable positive + coherent = a forward-paper candidate (power wall blocks in-sample "
          "certification). The sign-stability across years is the real test, not the t-stat.]")


if __name__ == "__main__":
    main()
