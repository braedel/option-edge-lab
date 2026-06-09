"""DECISIVE control for the pre-CPI drift (c35): is the +3.3t rally into CPI a real CPI effect, or just the
2023-25 bull-bond MORNING drift sampled on CPI days?

Test: compute the SAME morning-window move (enter 08:00/07:30/06:30 ET, exit 08:29 ET) for EVERY eligible
trading day, tag each day {CPI_clean, CPI_cont, NFP, FOMC, other}, and compare CPI(clean)-day mornings to
non-event-day mornings. The signal is real ONLY if the EXCESS (CPI_clean mean - other mean) is positive,
cost-beating, and significant -- i.e. CPI mornings drift MORE than ordinary mornings. Also per-year, to
check it isn't one regime. (NFP is 08:30 too -> its own tag, excluded from 'other'. FOMC is 14:00 so its
morning is a clean control.) Cheap, decisive, on in-sample data -- run BEFORE spending the sealed OOS.
Run on local mirror (ZB_DATA_ROOT). Reads frozen calendar.
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
from scipy import stats

from options_lab.zb_mbo.codes import TRADE, action
from options_lab.zb_mbo.loader import eligible_days, load_events, month_path, present_days
from options_lab.zb_mbo.stream import TICK

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
SEC = 1_000_000_000
WINDOWS = [(30, 8, 0), (60, 7, 30), (120, 6, 30)]   # (label_min, enter_hh, enter_mm) ET; exit fixed 08:29 ET
NPROC = 10
FEE_T = 4.0 / 31.25
CAL = Path("data/zb_macro_events.csv")


def hhmm_utc(d, hh, mm):
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC).timestamp() * 1e9)


def load_tagmap():
    tm = {}
    for r in csv.DictReader(open(CAL)):
        if r["pinning"] == "NOT_FOUND" or len(r["date"]) != 10:
            continue
        if r["event"] == "CPI":
            tm[r["date"]] = "CPI_cont" if r["contaminated"] == "True" else "CPI_clean"
        else:
            tm[r["date"]] = r["event"]   # NFP / FOMC
    return tm


def px_at(tts, tpx, t):
    j = np.searchsorted(tts, t, "right") - 1
    return float(tpx[j]) if j >= 0 else np.nan


def process_month(arg):
    mk, tagmap = arg
    a = load_events(month_path(mk))
    istr = action(a["ev"]).astype(np.int64) == TRADE
    tts, tpx = a["exch_ts"][istr], a["px"][istr]
    elig = eligible_days(present_days(a))
    out = []
    for d in elig:
        exit_px = px_at(tts, tpx, hhmm_utc(d, 8, 29))
        if not np.isfinite(exit_px):
            continue
        drifts = {}
        for lab, hh, mm in WINDOWS:
            e = px_at(tts, tpx, hhmm_utc(d, hh, mm))
            drifts[lab] = (exit_px - e) / TICK if np.isfinite(e) else np.nan
        out.append((d.isoformat(), tagmap.get(d.isoformat(), "other"), drifts))
    return mk, out


def desc(v):
    v = np.array([x for x in v if np.isfinite(x)], float)
    if len(v) < 3:
        return f"n={len(v)}", v
    se = v.std(ddof=1) / np.sqrt(len(v))
    return f"n={len(v):3d} mean={v.mean():+5.2f}t med={np.median(v):+5.2f}t %up={np.mean(v > 0):.2f} t={v.mean() / se:+5.2f}", v


def main():
    tagmap = load_tagmap()
    months = sorted({d[:7] for d in
                     [r["date"] for r in csv.DictReader(open(CAL)) if len(r["date"]) == 10]})
    nproc = min(NPROC, len(months))
    print(f"loading {len(months)} months across {nproc} workers (control = all eligible mornings)...", flush=True)
    days = []
    with mp.Pool(nproc) as pool:
        for mk, res in pool.imap_unordered(process_month, [(m, tagmap) for m in months]):
            days.extend(res)
            print(f"  done {mk} ({len(res)} eligible days)", flush=True)

    print(f"\n=== pre-event MORNING drift by day-type (exit 08:29 ET); total eligible days={len(days)} ===")
    for lab, _, _ in WINDOWS:
        print(f"\n-- enter t-{lab}min (08:30-{lab}m ET) -> exit 08:29 ET --")
        groups = {}
        for tag in ("CPI_clean", "CPI_cont", "NFP", "FOMC", "other"):
            s, v = desc([dr[lab] for (_, t, dr) in days if t == tag])
            groups[tag] = v
            print(f"   {tag:9s}: {s}")
        cpi, oth = groups["CPI_clean"], groups["other"]
        if len(cpi) >= 3 and len(oth) >= 3:
            tt = stats.ttest_ind(cpi, oth, equal_var=False)
            excess = cpi.mean() - oth.mean()
            print(f"   EXCESS CPI_clean - other = {excess:+.2f}t  (Welch t={tt.statistic:+.2f}, p={tt.pvalue:.3f})  "
                  f"net vs cost={excess - FEE_T:+.2f}t  -> {'REAL CPI effect' if tt.pvalue < 0.05 and excess > FEE_T else 'NOT distinguishable from ambient morning drift'}")

    # per-year stability of the CPI_clean excess at t-60min
    print("\n-- CPI_clean morning drift (t-60min) by year vs that year's 'other' mean --")
    for yr in ("2023", "2024", "2025"):
        c = np.array([dr[60] for (d, t, dr) in days if t == "CPI_clean" and d[:4] == yr and np.isfinite(dr[60])])
        o = np.array([dr[60] for (d, t, dr) in days if t == "other" and d[:4] == yr and np.isfinite(dr[60])])
        if len(c) and len(o):
            print(f"   {yr}: CPI_clean n={len(c)} mean={c.mean():+5.2f}t | other n={len(o)} mean={o.mean():+5.2f}t | "
                  f"excess={c.mean() - o.mean():+5.2f}t")
    print("\n[If the EXCESS is ~0 / insignificant, the pre-CPI 'edge' is ambient bull-bond morning drift -> dead. "
          "If the excess is positive, cost-beating, significant AND stable across years -> graduate to sealed OOS.]")


if __name__ == "__main__":
    main()
