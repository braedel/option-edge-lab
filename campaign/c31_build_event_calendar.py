"""Build + freeze the pre-registered macro-event calendar (quant Option 1, data-anchored).

NFP: first-Friday-of-month candidate; 08:30 ET spike-verify; if the first Friday is weak but a later
     Friday clearly spikes, re-pin (cadence misfired); else KEEP the first Friday (low-surprise NFP kept
     at full weight -- never dropped by move size).
CPI: scan Mon-Thu, day-of-month 6..18, for 08:30 ET spikes; label the DOMINANT mid-month spike CPI; flag
     the month CONTAMINATED if another comparable 08:30 spike lands within +/-2 days (PPI/retail) -- such
     months are excluded from the CPI-isolated test a priori (calendar coincidence, not survivorship).
FOMC: the 22 authoritative Fed dates (already validated by c30), 14:00 ET.

Output: data/zb_macro_events.csv -- the frozen, pre-registered artifact required BEFORE any edge test.
Scans ~32 eligible months (2023-01..2025-09, one at a time for memory). Calendar only -- NO edge test.
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from options_lab.zb_mbo.codes import TRADE, action
from options_lab.zb_mbo.loader import (
    BURNED_MONTHS, DEFAULT_SEALED_MONTHS, all_months, load_events, month_path,
)
from options_lab.zb_mbo.stream import TICK

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
MIN = 60_000_000_000
MONTHS = [m for m in all_months()
          if m <= "2025-09" and m not in BURNED_MONTHS and m not in DEFAULT_SEALED_MONTHS]
FOMC = [
    "2023-02-01", "2023-03-22", "2023-05-03", "2023-06-14", "2023-07-26", "2023-09-20", "2023-11-01", "2023-12-13",
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12", "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18", "2025-07-30", "2025-09-17",
]


def utc_ns(d: dt.date, hh: int, mm: int) -> int:
    return int(dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC).timestamp() * 1e9)


def spike(tts, tpx, t0):
    """5-min trade-range post t0 (ticks) vs median 5-min range in the prior hour; ratio; n trades."""
    post = (tts >= t0) & (tts < t0 + 5 * MIN)
    pr = float((tpx[post].max() - tpx[post].min()) / TICK) if post.sum() else 0.0
    base = []
    for k in range(12):
        w = (tts >= t0 - (60 - 5 * k) * MIN) & (tts < t0 - (55 - 5 * k) * MIN)
        if w.sum():
            base.append((tpx[w].max() - tpx[w].min()) / TICK)
    bm = float(np.median(base)) if base else float("nan")
    return pr, bm, (pr / bm if bm else float("nan")), int(post.sum())


def confirmed(pr, rt):
    return bool(pr >= 5 and np.isfinite(rt) and rt >= 3)


def first_friday(y, m):
    d = dt.date(y, m, 1)
    return d + dt.timedelta((4 - d.weekday()) % 7)


def main():
    rows = []
    for mk in MONTHS:
        y, m = int(mk[:4]), int(mk[5:7])
        a = load_events(month_path(mk))
        istr = action(a["ev"]).astype(np.int64) == TRADE
        tts, tpx = a["exch_ts"][istr], a["px"][istr]
        # ---- NFP: first Friday; re-pin only if a later Friday clearly spikes and the first doesn't ----
        ff = first_friday(y, m)
        chosen = None
        for off in (0, 7, 14):
            d = ff + dt.timedelta(off)
            if d.month != m:
                break
            pr, bm, rt, n = spike(tts, tpx, utc_ns(d, 8, 30))
            if off == 0:
                chosen = (d, pr, bm, rt, n, "first_friday")
            if confirmed(pr, rt):
                chosen = (d, pr, bm, rt, n, "first_friday" if off == 0 else f"friday+{off // 7}")
                break
        d, pr, bm, rt, n, meth = chosen
        rows.append([d.isoformat(), "08:30", "NFP", round(pr, 1), round(bm, 2),
                     round(rt, 1) if np.isfinite(rt) else "", n, confirmed(pr, rt), meth, False])
        # ---- CPI: dominant Mon-Thu mid-month 08:30 spike; flag coincidence ----
        sp = []
        for day in range(6, 19):
            try:
                dd = dt.date(y, m, day)
            except ValueError:
                continue
            if dd.weekday() > 3:   # Mon-Thu only (avoid NFP-Friday and weekends)
                continue
            pr, bm, rt, n = spike(tts, tpx, utc_ns(dd, 8, 30))
            if confirmed(pr, rt):
                sp.append((dd, pr, bm, rt, n))
        sp.sort(key=lambda s: -s[1])
        if sp:
            dd, pr, bm, rt, n = sp[0]
            contaminated = any(abs((s[0] - dd).days) <= 2 and s[1] >= 0.6 * pr for s in sp[1:])
            rows.append([dd.isoformat(), "08:30", "CPI", round(pr, 1), round(bm, 2),
                         round(rt, 1), n, True, "midmonth_max_spike", contaminated])
        else:
            rows.append([f"{mk}", "08:30", "CPI", 0, 0, "", 0, False, "NOT_FOUND", False])
        del a
    for ds in FOMC:
        rows.append([ds, "14:00", "FOMC", "", "", "", "", True, "fed_authoritative", False])

    out = Path("data/zb_macro_events.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "time_et", "event", "post5_ticks", "base5_ticks", "ratio", "n_trd",
                    "spike_confirmed", "pinning", "contaminated"])
        w.writerows(rows)

    nfp = [r for r in rows if r[2] == "NFP"]
    cpi = [r for r in rows if r[2] == "CPI" and r[7]]
    cpi_bad = [r for r in rows if r[2] == "CPI" and not r[7]]
    print(f"NFP: {len(nfp)} pinned, {sum(r[7] for r in nfp)} spike-confirmed; "
          f"move median={np.median([r[3] for r in nfp]):.1f}t; re-pinned={sum(1 for r in nfp if r[8] != 'first_friday')}")
    print(f"CPI: {len(cpi)} found, {sum(r[9] for r in cpi)} contaminated-flagged, {len(cpi_bad)} NOT_FOUND; "
          f"move median={np.median([r[3] for r in cpi]):.1f}t")
    print(f"FOMC: {len(FOMC)} authoritative")
    print(f"-> wrote {out}: {len(rows)} events")
    print("REVIEW these rows:")
    for r in rows:
        if (r[2] == "NFP" and not r[7]) or (r[2] == "CPI" and (r[9] or not r[7])):
            print(f"   {r[2]} {r[0]} move={r[3]}t ratio={r[5]} confirmed={r[7]} contaminated={r[9]} ({r[8]})")
    print("[pre-registered calendar; CPI labels are data-detected -- eyeball flagged rows before the edge test]")


if __name__ == "__main__":
    main()
