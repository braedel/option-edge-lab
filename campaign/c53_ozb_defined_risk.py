"""#3b: price the cheap-OTM DEFINED-RISK trade on REAL OZB quotes, for all CPI+FOMC big-surprise events.
Per event: buy a ~0.5pt-OTM option in the fundamental-surprise direction (call if long ZB / put if short)
at the entry ASK (t+5min), sell at the exit BID (t+65min). Max loss = premium (defined risk). Two-stage,
cached per event (resumable). Compares to the naked futures: does the cheap-OTM keep the Sharpe and cut DD?
Key from the verified file (never printed). Run on ZB_DATA_ROOT not needed (uses curve + OZB).
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import databento as db
import numpy as np
import pandas as pd

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
KEY_FILE = r"D:\workspace\spx-0dte-pinfly-lab\databendto_key.txt"
GLBX = "GLBX.MDP3"
CURVE = Path(r"D:\TradingData\databento\curve\curve_ohlcv1m.parquet")
CACHE = Path(r"D:\TradingData\databento\ozb"); CACHE.mkdir(parents=True, exist_ok=True)
OTM = 0.5            # points OTM (~16 ticks)
OPT_MULT = 1000.0   # $ per point for ZB options
OPT_FEE = 3.0       # $ round-trip option fee

# (date, type, hh, mm, surprise) -- CPI big (|core|>=0.1) + FOMC big (+-1), in-sample + OOS
EVENTS = [
    ("2023-01-12", "CPI", 8, 30, 0.1), ("2023-02-14", "CPI", 8, 30, 0.1), ("2023-03-14", "CPI", 8, 30, 0.1),
    ("2023-07-12", "CPI", 8, 30, -0.1), ("2023-09-13", "CPI", 8, 30, 0.1), ("2023-11-14", "CPI", 8, 30, -0.1),
    ("2024-02-13", "CPI", 8, 30, 0.1), ("2024-03-12", "CPI", 8, 30, 0.1), ("2024-04-10", "CPI", 8, 30, 0.1),
    ("2024-06-12", "CPI", 8, 30, -0.1), ("2024-07-11", "CPI", 8, 30, -0.1), ("2024-09-11", "CPI", 8, 30, 0.1),
    ("2024-10-10", "CPI", 8, 30, 0.1), ("2025-01-15", "CPI", 8, 30, -0.1), ("2025-02-12", "CPI", 8, 30, 0.1),
    ("2025-03-12", "CPI", 8, 30, -0.1), ("2025-05-13", "CPI", 8, 30, -0.1), ("2025-06-11", "CPI", 8, 30, -0.2),
    ("2025-07-15", "CPI", 8, 30, -0.1), ("2025-10-24", "CPI", 8, 30, -0.1), ("2025-12-18", "CPI", 8, 30, -0.1),
    ("2026-01-13", "CPI", 8, 30, -0.1), ("2026-04-10", "CPI", 8, 30, -0.1),
    ("2023-02-01", "FOMC", 14, 0, -1), ("2023-03-22", "FOMC", 14, 0, -1), ("2023-05-03", "FOMC", 14, 0, -1),
    ("2023-06-14", "FOMC", 14, 0, 1), ("2023-09-20", "FOMC", 14, 0, 1), ("2023-11-01", "FOMC", 14, 0, -1),
    ("2023-12-13", "FOMC", 14, 0, -1), ("2024-01-31", "FOMC", 14, 0, 1), ("2024-03-20", "FOMC", 14, 0, -1),
    ("2024-05-01", "FOMC", 14, 0, -1), ("2024-06-12", "FOMC", 14, 0, 1), ("2024-07-31", "FOMC", 14, 0, -1),
    ("2024-12-18", "FOMC", 14, 0, 1), ("2025-01-29", "FOMC", 14, 0, 1), ("2025-03-19", "FOMC", 14, 0, -1),
    ("2025-07-30", "FOMC", 14, 0, 1), ("2025-10-29", "FOMC", 14, 0, 1), ("2026-01-28", "FOMC", 14, 0, 1),
    ("2026-03-18", "FOMC", 14, 0, 1),
]


def read_key(f):
    return re.search(r"db-[A-Za-z0-9]+", open(f, encoding="utf-8", errors="ignore").read()).group(0)


def atm_lookup():
    cv = pd.read_parquet(CURVE).reset_index()
    tcol = next(c for c in ("ts_event", "index", "ts_recv") if c in cv.columns)
    cv["ts"] = pd.to_datetime(cv[tcol], utc=True)
    return cv[cv["symbol"] == "ZB.c.0"].set_index("ts")["close"].sort_index()


def pull_event(client, date, hh, mm, atm_series):
    cache = CACHE / f"ozb_{date}.parquet"
    d = dt.date.fromisoformat(date)
    t0 = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC)
    entry, win_e = t0 + dt.timedelta(minutes=5), t0 + dt.timedelta(minutes=70)
    atm = float(atm_series.asof(pd.Timestamp(entry)))
    if cache.exists():
        return pd.read_parquet(cache), atm, t0
    defs = client.timeseries.get_range(GLBX, symbols=["OZB.OPT"], stype_in="parent", schema="definition",
                                       start=d.isoformat(), end=(d + dt.timedelta(days=1)).isoformat()).to_df()
    defs["strike_price"] = pd.to_numeric(defs["strike_price"], errors="coerce")
    if defs["strike_price"].max() > 1000:
        defs["strike_price"] /= 1000.0
    defs["expiration"] = pd.to_datetime(defs["expiration"], utc=True, errors="coerce")
    fut = [e for e in sorted(defs["expiration"].dropna().unique()) if pd.Timestamp(e) >= pd.Timestamp(entry) + pd.Timedelta(days=5)]
    exp = fut[0] if fut else sorted(defs["expiration"].dropna().unique())[-1]
    band = defs[(defs["expiration"] == exp) & (defs["strike_price"].between(atm - 2.5, atm + 2.5))]
    syms = sorted(band["raw_symbol"].unique().tolist())
    bbo = client.timeseries.get_range(GLBX, symbols=syms[:60], stype_in="raw_symbol", schema="bbo-1s",
                                      start=t0.isoformat(), end=win_e.isoformat()).to_df().reset_index()
    keep = bbo[["ts_event", "symbol", "bid_px_00", "ask_px_00"]].copy()
    keep.to_parquet(cache)
    return keep, atm, t0


def price_trade(bbo, atm, t0, surprise):
    if not len(bbo):
        return None
    entry_t, exit_t = pd.Timestamp(t0) + pd.Timedelta(minutes=5), pd.Timestamp(t0) + pd.Timedelta(minutes=65)
    bbo = bbo.copy()
    bbo["ts"] = pd.to_datetime(bbo["ts_event"], utc=True)
    rs = bbo["symbol"].str.extract(r"\s([CP])(\d+)$")
    bbo["right"], bbo["strike"] = rs[0], pd.to_numeric(rs[1], errors="coerce") / 10.0
    dirn = -np.sign(surprise)                     # +1 long ZB -> CALL ; -1 short ZB -> PUT
    right = "C" if dirn > 0 else "P"
    cand = bbo[bbo["right"] == right]["strike"].dropna().unique()
    if dirn > 0:
        otm = [k for k in cand if k >= atm + OTM - 0.01]
        strike = min(otm) if otm else None
    else:
        otm = [k for k in cand if k <= atm - OTM + 0.01]
        strike = max(otm) if otm else None
    if strike is None:
        return None
    leg = bbo[(bbo["right"] == right) & (np.isclose(bbo["strike"], strike))].set_index("ts").sort_index()
    if leg.empty:
        return None
    entry_ask = leg["ask_px_00"].asof(entry_t)
    exit_bid = leg["bid_px_00"].asof(exit_t)
    if not (np.isfinite(entry_ask) and np.isfinite(exit_bid)) or entry_ask <= 0:
        return None
    net = (exit_bid - entry_ask) * OPT_MULT - OPT_FEE
    return dict(right=right, strike=strike, entry_ask=entry_ask, exit_bid=exit_bid, net=net)


def main():
    client = db.Historical(read_key(KEY_FILE))
    atm_series = atm_lookup()
    rows = []
    for i, (date, typ, hh, mm, s) in enumerate(EVENTS, 1):
        try:
            bbo, atm, t0 = pull_event(client, date, hh, mm, atm_series)
            r = price_trade(bbo, atm, t0, s)
            if r:
                rows.append((date, typ, s, r["right"], r["strike"], r["entry_ask"], r["net"]))
                print(f"[{i}/{len(EVENTS)}] {date} {typ} surp{s:+.2f} -> buy {r['right']}{r['strike']:.1f} "
                      f"@{r['entry_ask']:.3f} exit{r['exit_bid']:.3f} net=${r['net']:+.0f}", flush=True)
            else:
                print(f"[{i}/{len(EVENTS)}] {date} {typ}: no priceable OTM leg", flush=True)
        except Exception as e:
            print(f"[{i}/{len(EVENTS)}] {date} {typ} ERROR {type(e).__name__}: {e}", flush=True)

    net = np.array([r[6] for r in rows], float)
    if not len(net):
        print("no trades priced"); return
    yrs = 3.4
    sh = net.mean() / net.std(ddof=1) * np.sqrt(len(net) / yrs) if net.std() else float("nan")
    dd = (np.maximum.accumulate(np.cumsum(net)) - np.cumsum(net)).max()
    print(f"\n=== cheap-OTM defined-risk (REAL OZB quotes), {len(net)} events ===")
    print(f"NET/trade=${net.mean():+.0f} total=${net.sum():+,.0f} %pos={np.mean(net>0):.2f} "
          f"Sharpe~{sh:+.2f} maxDD=${dd:,.0f} worst=${net.min():+,.0f}")
    print(f"(naked futures benchmark was Sharpe ~1.25, maxDD ~$1,055, worst ~-$473)")
    print("[Defined risk: max loss per trade = premium. If Sharpe ~ naked but DD/worst materially lower -> "
          "the options wrap is the deployable, lower-DD version of #1.]")


if __name__ == "__main__":
    main()
