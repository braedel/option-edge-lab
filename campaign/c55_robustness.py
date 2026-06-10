"""#1 ROBUSTNESS (post critical-review): the cheap, decisive checks the review demanded, in ONE L3 pass.
Computes the GROSS per-event directional move (ticks, pre-cost) for the CPI+FOMC+NFP big-surprise set, SAVES
it (closes the provenance gap the review flagged -- no CPI+FOMC per-event artifact existed), then prints from
that in-memory set (no reload):
  1. Headline reproduction (CPI+FOMC big, cost 1t + $4) -- confirm Sharpe ~1.25 / t 2.07 / n 35.
  2. FILL-SENSITIVITY SWEEP (CLAUDE.md rule 5, never run for the futures leg): round-trip slippage 0/1/2/3 t.
  3. CONTAMINATED-EXCLUSION: drop the 7 traded BIG CPI events flagged contaminated=True in the frozen calendar.
  4. FOMC-DEPENDENCE: CPI-only vs FOMC-only -- how much of the edge hangs on the discretionary FOMC hand-label.
Run with .venv-mbo + ZB_DATA_ROOT. NOT an edge re-claim -- a robustness audit of an unvalidated, post-hoc rule.
"""
from __future__ import annotations

import csv
import datetime as dt
import multiprocessing as mp
import os
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

from options_lab.zb_mbo.codes import TRADE, action          # noqa: E402
from options_lab.zb_mbo.loader import load_events, month_path  # noqa: E402
from options_lab.zb_mbo.stream import TICK                    # noqa: E402

ET = ZoneInfo("America/New_York")
SEC = 1_000_000_000
SPIKE_AFTER, HOLD = 300 * SEC, 3600 * SEC
FEE_T = 4.0 / 31.25      # $4 RT expressed in ticks
DOLLAR = 31.25
YRS = 2.75               # in-sample span (match c51 annualization)
NPROC = 10
OUT = Path("reports/zb_surprise/per_event_cpifomc.csv")

# surprise dicts copied verbatim from c51_expand_allann.py (the rule under audit)
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
SURP_FOMC = {
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


def is_big(typ, s):
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
        move_t = (ex - entry) / TICK * (-np.sign(s))          # GROSS directional move (ticks), pre-cost
        out.append((date, typ, float(s), bool(is_big(typ, s)), float(move_t)))
    return out


def stats(move_t, slip_t, label):
    """Apply a round-trip slippage (ticks) + the $4 fee to gross moves; print pooled stats."""
    v = (np.asarray(move_t, float) - slip_t - FEE_T) * DOLLAR
    if len(v) < 4:
        print(f"  {label:34s} n={len(v)} (few)")
        return
    se = v.std(ddof=1) / np.sqrt(len(v))
    sh = v.mean() / v.std(ddof=1) * np.sqrt(len(v) / YRS) if v.std() else float("nan")
    dd = (np.maximum.accumulate(np.cumsum(v)) - np.cumsum(v)).max()
    print(f"  {label:34s} n={len(v):3d} NET=${v.mean():+5.0f} %pos={np.mean(v>0):.2f} "
          f"t={v.mean()/se:+4.2f} Sharpe~{sh:+4.2f} maxDD=${dd:,.0f}")


def main():
    contam = set()
    cal = Path("data/zb_macro_events.csv")
    if cal.exists():
        contam = {r["date"] for r in csv.DictReader(open(cal))
                  if r.get("contaminated", "").strip().lower() in ("true", "1")}

    bymonth = defaultdict(list)
    for e in EV:
        if e[0][:7] <= "2025-09":
            bymonth[e[0][:7]].append(e)
    items = sorted(bymonth.items())
    print(f"#1 robustness: one L3 pass over {len(items)} in-sample months...", flush=True)
    rows = []
    with mp.Pool(min(NPROC, len(items))) as pool:
        for res in pool.imap_unordered(process_month, items):
            rows.extend(res)
    rows.sort()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "type", "surprise", "big", "contaminated", "move_ticks", "gross_net_dollars_1t"])
        for date, typ, s, big, mv in rows:
            w.writerow([date, typ, s, int(big), int(date in contam), f"{mv:.4f}", f"{(mv-1.0-FEE_T)*DOLLAR:.2f}"])
    print(f"-> saved per-event artifact {OUT} ({len(rows)} events)\n")

    bigCF = [r[4] for r in rows if r[3] and r[1] != "NFP"]                       # CPI+FOMC big
    print("=== 1. HEADLINE REPRODUCTION (CPI+FOMC big, 1t slippage + $4) ===")
    stats(bigCF, 1.0, "CPI+FOMC big")

    print("\n=== 2. FILL-SENSITIVITY SWEEP (CLAUDE.md rule 5) -- CPI+FOMC big ===")
    for slip in (0.0, 1.0, 2.0, 3.0):
        stats(bigCF, slip, f"slippage {slip:.0f}t + $4")

    print("\n=== 3. CONTAMINATED-EXCLUSION (drop 7 BIG CPI flagged contaminated), 1t + $4 ===")
    bigCF_clean = [r[4] for r in rows if r[3] and r[1] != "NFP" and r[0] not in contam]
    n_drop = sum(1 for r in rows if r[3] and r[1] != "NFP" and r[0] in contam)
    stats(bigCF_clean, 1.0, f"CPI+FOMC big, -{n_drop} contaminated")

    print("\n=== 4. FOMC-DEPENDENCE (how much hangs on the discretionary FOMC label), 1t + $4 ===")
    stats([r[4] for r in rows if r[3] and r[1] == "CPI"], 1.0, "CPI big ONLY (no FOMC)")
    stats([r[4] for r in rows if r[3] and r[1] == "FOMC"], 1.0, "FOMC big ONLY")
    print("\n[Edge must survive realistic slippage AND the contaminated drop AND not hang entirely on FOMC to "
          "justify the point-in-time/FOMC-rubric cleanup. If it dies here, converge to shelve (path B).]")


if __name__ == "__main__":
    main()
