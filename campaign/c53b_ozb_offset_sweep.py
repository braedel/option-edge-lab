"""#3b offset sweep on CACHED OZB quotes (no re-download): does any strike offset (ATM..1.5pt OTM) keep more
of the #1 Sharpe than the 0.5-OTM did? Decides whether the defined-risk wrap is salvageable or a real Sharpe
sacrifice. Reuses c53's events + cache.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from c53_ozb_defined_risk import EVENTS, CACHE, atm_lookup, OPT_MULT, OPT_FEE  # noqa: E402

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc


def price(bbo, atm, t0, surprise, off):
    if bbo is None or not len(bbo):
        return None
    entry_t = pd.Timestamp(t0) + pd.Timedelta(minutes=5)
    exit_t = pd.Timestamp(t0) + pd.Timedelta(minutes=65)
    b = bbo.copy()
    b["ts"] = pd.to_datetime(b["ts_event"], utc=True)
    rs = b["symbol"].str.extract(r"\s([CP])(\d+)$")
    b["right"], b["strike"] = rs[0], pd.to_numeric(rs[1], errors="coerce") / 10.0
    dirn = -np.sign(surprise)
    right = "C" if dirn > 0 else "P"
    cand = b[b["right"] == right]["strike"].dropna().unique()
    if dirn > 0:
        cl = [k for k in cand if k >= atm + off - 0.01]; strike = min(cl) if cl else None
    else:
        cl = [k for k in cand if k <= atm - off + 0.01]; strike = max(cl) if cl else None
    if strike is None:
        return None
    leg = b[(b["right"] == right) & (np.isclose(b["strike"], strike))].set_index("ts").sort_index()
    if leg.empty:
        return None
    ea, xb = leg["ask_px_00"].asof(entry_t), leg["bid_px_00"].asof(exit_t)
    if not (np.isfinite(ea) and np.isfinite(xb)) or ea <= 0:
        return None
    return (xb - ea) * OPT_MULT - OPT_FEE


def main():
    atm_series = atm_lookup()
    cached = []
    for date, typ, hh, mm, s in EVENTS:
        f = CACHE / f"ozb_{date}.parquet"
        if not f.exists():
            continue
        d = dt.date.fromisoformat(date)
        t0 = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC)
        atm = float(atm_series.asof(pd.Timestamp(t0 + dt.timedelta(minutes=5))))
        cached.append((pd.read_parquet(f), atm, t0, s))
    print(f"cached events: {len(cached)}")
    print("offset | n   NET/trade  %pos  Sharpe  maxDD   worst")
    for off in (0.0, 0.5, 1.0, 1.5):
        nets = [price(bbo, atm, t0, s, off) for bbo, atm, t0, s in cached]
        v = np.array([x for x in nets if x is not None], float)
        if len(v) < 4:
            print(f" {off:.1f}   | n={len(v)} (few)"); continue
        sh = v.mean() / v.std(ddof=1) * np.sqrt(len(v) / 3.4)
        dd = (np.maximum.accumulate(np.cumsum(v)) - np.cumsum(v)).max()
        print(f" {off:.1f}   | {len(v):3d} ${v.mean():+5.0f}  {np.mean(v>0):.2f}  {sh:+5.2f}  ${dd:5,.0f}  ${v.min():+5.0f}")
    print("\n[Any offset Sharpe ~ naked 1.25 with lower DD = wrap salvageable. All << 1 = real premiums/spreads "
          "eat the edge -> deploy naked #1 (DD already acceptable), options not worth it.]")


if __name__ == "__main__":
    main()
