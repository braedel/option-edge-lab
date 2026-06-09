"""#3b VALIDATE the OZB (options-on-ZB-futures) pull on ONE event before scaling (PinFly 'validate first'
discipline). Confirms: parent symbology OZB.OPT works, the definition schema gives strikes/expiries, and
real bid/ask come through on bbo-1s over the event window. Key from the verified file (never printed).
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import databento as db
import pandas as pd

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
KEY_FILE = r"D:\workspace\spx-0dte-pinfly-lab\databendto_key.txt"
GLBX = "GLBX.MDP3"
CURVE = Path(r"D:\TradingData\databento\curve\curve_ohlcv1m.parquet")
DATE, HH, MM = "2025-09-11", 8, 30   # a CPI event to validate on


def read_key(f):
    m = re.search(r"db-[A-Za-z0-9]+", open(f, encoding="utf-8", errors="ignore").read())
    return m.group(0)


def main():
    client = db.Historical(read_key(KEY_FILE))
    d = dt.date.fromisoformat(DATE)
    t0 = dt.datetime(d.year, d.month, d.day, HH, MM, tzinfo=ET).astimezone(UTC)
    entry, win_e = t0 + dt.timedelta(minutes=5), t0 + dt.timedelta(minutes=70)

    # ATM reference = continuous front ZB price at entry (from the curve pull)
    cv = pd.read_parquet(CURVE).reset_index()
    tcol = next(c for c in ("ts_event", "index", "ts_recv") if c in cv.columns)
    cv["ts"] = pd.to_datetime(cv[tcol], utc=True)
    zb = cv[cv["symbol"] == "ZB.c.0"].set_index("ts")["close"].sort_index()
    atm = float(zb.asof(pd.Timestamp(entry)))
    print(f"event {DATE} 08:30 ET | ZB front ~ {atm:.3f} at entry (t+5min)")

    # definition (free) -> strikes/expiries
    defs = client.timeseries.get_range(GLBX, symbols=["OZB.OPT"], stype_in="parent", schema="definition",
                                       start=d.isoformat(), end=(d + dt.timedelta(days=1)).isoformat()).to_df()
    print(f"\ndefinition rows: {len(defs)}  cols: {list(defs.columns)[:25]}")
    scol = "strike_price" if "strike_price" in defs.columns else next((c for c in defs.columns if "strike" in c), None)
    ecol = "expiration" if "expiration" in defs.columns else next((c for c in defs.columns if "expir" in c), None)
    ccol = "instrument_class" if "instrument_class" in defs.columns else next((c for c in defs.columns if "class" in c), None)
    print(f"using strike={scol} expiry={ecol} class={ccol}")
    defs[scol] = pd.to_numeric(defs[scol], errors="coerce")
    if defs[scol].max() > 1000:          # databento strikes often in 1e-9 or raw; normalize toward price scale
        defs[scol] = defs[scol] / 1000.0
    defs[ecol] = pd.to_datetime(defs[ecol], utc=True, errors="coerce")
    exps = sorted(defs[ecol].dropna().unique())
    print(f"strikes ~[{defs[scol].min():.1f}..{defs[scol].max():.1f}]  expiries: "
          + ", ".join(pd.Timestamp(e).date().isoformat() for e in exps[:8]))

    # pick front expiry >= entry+5 days; ATM-band strikes (+-2 pts)
    future = [e for e in exps if pd.Timestamp(e) >= pd.Timestamp(entry) + pd.Timedelta(days=5)]
    exp = future[0] if future else exps[-1]
    band = defs[(defs[ecol] == exp) & (defs[scol].between(atm - 2, atm + 2))]
    syms = sorted(band["raw_symbol"].unique().tolist())
    print(f"\nchosen expiry {pd.Timestamp(exp).date()} ({(pd.Timestamp(exp)-pd.Timestamp(entry)).days}d out); "
          f"ATM-band strikes: {sorted(band[scol].unique().tolist())}  ({len(syms)} symbols)")

    # bbo-1s over the window for those symbols
    bbo = client.timeseries.get_range(GLBX, symbols=syms[:40], stype_in="raw_symbol", schema="bbo-1s",
                                      start=t0.isoformat(), end=win_e.isoformat()).to_df()
    print(f"\nbbo-1s rows over [t0, t0+70min]: {len(bbo)}  cols: {list(bbo.columns)[:20]}")
    if len(bbo):
        bcol = next((c for c in bbo.columns if c.startswith("bid_px")), None)
        acol = next((c for c in bbo.columns if c.startswith("ask_px")), None)
        s = bbo.reset_index().iloc[len(bbo)//2]
        print(f"sample mid-window quote: sym={s.get('symbol')} bid={s.get(bcol)} ask={s.get(acol)} ts={s.get('ts_event')}")
        print("-> OZB pull WORKS. Next: scale to all CPI+FOMC big events + price the cheap-OTM trade.")


if __name__ == "__main__":
    main()
