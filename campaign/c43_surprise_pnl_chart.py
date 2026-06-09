"""PnL + drawdown chart for the one real edge (big-surprise direction trade). IN-SAMPLE / DISCOVERY ONLY --
this is the eligible development set (2023-01..2025-09 minus burned/sealed); the sealed OOS was NOT touched
and the rule was chosen on this same data. NOT an out-of-sample result. Labeled as such on the chart.

Rule (the deployable spec): enter -sign(actual-consensus) at t+5min on BIG CPI/NFP surprises
(CPI |core MoM|>=0.1, NFP |surp|>=~80k), hold 60min, exit; NET after 1.13t cost; 1 contract ($31.25/tick).
Produces: reports/zb_surprise/pnl_dd.png (cumulative $ + combined drawdown) and per_event.csv.
Run on local mirror (ZB_DATA_ROOT).
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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from options_lab.zb_mbo.codes import TRADE, action
from options_lab.zb_mbo.loader import load_events, month_path
from options_lab.zb_mbo.stream import TICK

ET = ZoneInfo("America/New_York")
SEC = 1_000_000_000
SPIKE_AFTER = 300 * SEC
HOLD = 3600 * SEC
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
CPI_BIG = 0.1
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
        big = (abs(surp) >= CPI_BIG) if typ == "CPI" else (abs(surp) >= NFP_BIG)
        if surp == 0 or not big:
            continue
        t0 = utc_ns(date, 8, 30)
        entry = px_at(tts, tpx, t0 + SPIKE_AFTER)
        ex = px_at(tts, tpx, t0 + SPIKE_AFTER + HOLD)
        if not (np.isfinite(entry) and np.isfinite(ex)):
            continue
        net = (ex - entry) / TICK * (-np.sign(surp)) - COST_T
        out.append((date, typ, float(net)))
    return out


def main():
    events = [(d, "CPI", s) for d, s in SURP_CPI.items()] + [(d, "NFP", s) for d, s in SURP_NFP.items()]
    bymonth = defaultdict(list)
    for d, typ, s in events:
        bymonth[d[:7]].append((d, typ, s))
    items = sorted(bymonth.items())
    print(f"loading {len(items)} months across {min(NPROC,len(items))} workers...", flush=True)
    rows = []
    with mp.Pool(min(NPROC, len(items))) as pool:
        for res in pool.imap_unordered(process_month, items):
            rows.extend(res)
    rows.sort(key=lambda r: r[0])

    dates = [dt.date.fromisoformat(r[0]) for r in rows]
    net = np.array([r[2] for r in rows]) * DOLLAR     # $ per event
    eq = np.cumsum(net)
    peak = np.maximum.accumulate(eq)
    dd = eq - peak
    cpi_eq = np.cumsum([(r[2] * DOLLAR if r[1] == "CPI" else 0.0) for r in rows])
    nfp_eq = np.cumsum([(r[2] * DOLLAR if r[1] == "NFP" else 0.0) for r in rows])

    n = len(net)
    yrs = (dates[-1] - dates[0]).days / 365.25
    sharpe = net.mean() / net.std(ddof=1) * np.sqrt(n / yrs) if net.std() else float("nan")
    out = Path("reports/zb_surprise"); out.mkdir(parents=True, exist_ok=True)
    with open(out / "per_event.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "type", "net_dollars"])
        for r in rows:
            w.writerow([r[0], r[1], round(r[2] * DOLLAR, 2)])

    # ---- chart ----
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), height_ratios=[3, 1], sharex=True)
    fig.suptitle("ZB big-surprise direction trade  —  IN-SAMPLE / DISCOVERY (NOT out-of-sample)", fontsize=13, weight="bold")
    ax1.plot(dates, eq, "-o", ms=3, lw=1.8, color="#1f4e79", label="combined (CPI+NFP)")
    ax1.plot(dates, cpi_eq, "-", lw=1.0, color="#2e8b57", alpha=0.8, label="CPI leg")
    ax1.plot(dates, nfp_eq, "-", lw=1.0, color="#b8860b", alpha=0.8, label="NFP leg")
    ax1.axhline(0, color="grey", lw=0.7)
    for y in (2024, 2025):
        ax1.axvline(dt.date(y, 1, 1), color="grey", ls=":", lw=0.8)
    ax1.set_ylabel("cumulative P&L ($, 1 lot)")
    ax1.legend(loc="upper left", fontsize=9)
    txt = (f"n={n} big-surprise trades ({yrs:.1f}y)\nNET/trade=${net.mean():+.0f}  total=${eq[-1]:+.0f}\n"
           f"%pos={np.mean(net>0):.2f}  Sharpe~{sharpe:+.2f}\nmaxDD=${-dd.min():,.0f}\n"
           f"by year: 23 ${net[[d.year==2023 for d in dates]].sum():+.0f} / "
           f"24 ${net[[d.year==2024 for d in dates]].sum():+.0f} / 25 ${net[[d.year==2025 for d in dates]].sum():+.0f}")
    ax1.text(0.985, 0.04, txt, transform=ax1.transAxes, fontsize=9, ha="right", va="bottom",
             bbox=dict(boxstyle="round", fc="#fff8e7", ec="grey"))
    ax2.fill_between(dates, dd, 0, color="#c0392b", alpha=0.5)
    ax2.set_ylabel("drawdown ($)"); ax2.axhline(0, color="grey", lw=0.7)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.text(0.5, 0.005, "In-sample: rule chosen on this same 2023-01..2025-09 data; sealed OOS NOT spent. "
             "Forward paper is the real test.", ha="center", fontsize=8, style="italic", color="#777")
    fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    fig.savefig(out / "pnl_dd.png", dpi=130)
    print(f"-> wrote {out/'pnl_dd.png'} and per_event.csv")
    print(f"n={n} total=${eq[-1]:+.0f} net/trade=${net.mean():+.0f} %pos={np.mean(net>0):.2f} "
          f"Sharpe~{sharpe:+.2f} maxDD=${-dd.min():,.0f}")
    print(f"by year $: 2023={net[[d.year==2023 for d in dates]].sum():+.0f} "
          f"2024={net[[d.year==2024 for d in dates]].sum():+.0f} 2025={net[[d.year==2025 for d in dates]].sum():+.0f}")


if __name__ == "__main__":
    main()
