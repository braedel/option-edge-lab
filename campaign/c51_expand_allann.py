"""#1 expand: test the surprise-direction rule across CPI + NFP + FOMC (the 3 big announcements), IN-SAMPLE
(2023-01..2025-09). Does a BROAD announcement-surprise edge exist with more events (power), or was CPI/NFP
narrow? Rule (frozen): enter -sign(surprise) at t+5min, hold 60min; CPI/NFP 08:30 ET, FOMC 14:00 ET.
FOMC surprise = hawkish(+1)/dovish(-1) classification (deep-research). Big filter: CPI |core|>=0.1,
NFP |surp|>=80k, FOMC any +-1. Reports per-type + pooled + Sharpe/DD. Run on local mirror (ZB_DATA_ROOT).
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
SPIKE_AFTER, HOLD = 300 * SEC, 3600 * SEC
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
SURP_FOMC = {  # hawkish(+1)/dovish(-1)/neutral(0), 14:00 ET (deep-research classification)
    "2023-02-01": -1, "2023-03-22": -1, "2023-05-03": -1, "2023-06-14": 1, "2023-07-26": 0, "2023-09-20": 1,
    "2023-11-01": -1, "2023-12-13": -1, "2024-01-31": 1, "2024-03-20": -1, "2024-05-01": -1, "2024-06-12": 1,
    "2024-07-31": -1, "2024-09-18": 0, "2024-11-07": 0, "2024-12-18": 1, "2025-01-29": 1, "2025-03-19": -1,
    "2025-05-07": 0, "2025-06-18": 0, "2025-07-30": 1, "2025-09-17": 0,
}
EV = ([(d, "CPI", 8, 30, s) for d, s in SURP_CPI.items()]
      + [(d, "NFP", 8, 30, s) for d, s in SURP_NFP.items()]
      + [(d, "FOMC", 14, 0, s) for d, s in SURP_FOMC.items()])


def utc_ns(date_str, hh, mm):
    d = dt.date.fromisoformat(date_str)
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(dt.timezone.utc).timestamp() * 1e9)


def big(typ, s):
    return abs(s) >= (0.1 if typ == "CPI" else 80 if typ == "NFP" else 1)


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
        out.append((typ, big(typ, s), (ex - entry) / TICK * (-np.sign(s)) - COST_T))
    return out


def rep(label, v):
    v = np.array(v, float)
    if len(v) < 4:
        print(f"  {label}: n={len(v)} (few)"); return
    se = v.std(ddof=1) / np.sqrt(len(v))
    sh = v.mean() / v.std(ddof=1) * np.sqrt(len(v) / 2.75) if v.std() else float("nan")   # ~2.75yr in-sample
    dd = (np.maximum.accumulate(np.cumsum(v)) - np.cumsum(v)).max()
    print(f"  {label}: n={len(v):3d} NET/trade=${v.mean()*DOLLAR:+.0f} %pos={np.mean(v>0):.2f} "
          f"t={v.mean()/se:+.2f} Sharpe~{sh:+.2f} maxDD=${dd*DOLLAR:,.0f}")


def main():
    bymonth = defaultdict(list)
    for e in EV:
        if e[0][:7] <= "2025-09":
            bymonth[e[0][:7]].append(e)
    items = sorted(bymonth.items())
    print(f"#1 expand: loading {len(items)} in-sample months (CPI+NFP+FOMC surprise direction)...", flush=True)
    rows = []
    with mp.Pool(min(NPROC, len(items))) as pool:
        for res in pool.imap_unordered(process_month, items):
            rows.extend(res)

    print("\n=== broad announcement surprise-direction edge, IN-SAMPLE, BIG surprises, hold 60min ===")
    for typ in ("CPI", "NFP", "FOMC"):
        rep(f"{typ:4s} big", [r[2] for r in rows if r[0] == typ and r[1]])
    rep("POOL CPI+NFP+FOMC big", [r[2] for r in rows if r[1]])
    rep("POOL all (incl small)", [r[2] for r in rows])
    print("\n[Broad pooled Sharpe ~1 with n~40-60 = a more credible (higher-power) candidate for forward paper "
          "than CPI/NFP alone. FOMC adds 22 events; if FOMC is the steadiest leg, weight it.]")


if __name__ == "__main__":
    main()
