r"""#3c PROTECTIVE OVERLAY (the owner's actual question): hold the #1 surprise-direction ZB FUTURE and BUY a
protective OTM option on the ADVERSE side as downside insurance -- vs naked futures. Structurally DIFFERENT
from c53/c53b (which bought an option IN the trade direction as a defined-risk REPLACEMENT).

Per big CPI/FOMC surprise: take the #1 trade on the FUTURE (enter t+5min, side=-sign(surprise), hold 60min)
and simultaneously buy a protective option on the side that hurts (LONG ZB -> PUT below; SHORT ZB -> CALL
above), `off` points OTM, at the entry ASK (t+5min). overlay_net = futures_net + protective_option_net.

REAL cached OZB quotes only (D:\TradingData\databento\ozb, written by c53) + ZB.c.0 curve for the futures
leg -- fully OFFLINE. FRESHNESS-GUARDED asof (a quote is used only within `tol` of the target time).

EXIT REALISM (the key issue this script surfaces): after a big macro move a FIXED strike drifts away from the
money and stops being two-sided quoted, so at +60min the protective strike is often NO LONGER quoted -- and
because a protective option goes OTM exactly when the trade WINS, "exit unquoted" correlates with WINNING.
Keeping only cleanly-priceable exits would therefore SELECT FOR LOSERS and flatter the overlay. So we BRACKET
the exit (like a fill-sensitivity sweep):
  - PESS (realistic): no fresh exit bid -> the OTM hedge is unsellable, lapses -> exit value 0 (lose premium).
  - OPT  (generous):  no fresh exit bid -> mark at the last available bid (stale), giving the hedge salvage value.
If the overlay underperforms naked under BOTH bounds, the result is robust. The futures leg is COMMON to both
arms, so its (curve-vs-L3) noise cancels in the naked-vs-overlay DELTA; the authoritative naked benchmark is
the L3-priced Sharpe ~1.25. In-sample set (discovery incl the confounded OOS window) -- a COST/SHAPE/execution
test of the overlay on the existing (unvalidated) edge, NOT a fresh edge claim. Run with .venv-mbo.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ET = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
CURVE = Path(r"D:\TradingData\databento\curve\curve_ohlcv1m.parquet")
CACHE = Path(r"D:\TradingData\databento\ozb")
FUT_MULT = 1000.0
TICK_D = 31.25
FUT_COST_D = 1.0 * TICK_D + 4.0   # 1 tick slippage + $4 RT == c42 COST_T, in $
OPT_MULT = 1000.0
OPT_FEE = 3.0
FUT_TOL = 150                     # s: curve is 1-min, accept a bar within ~2.5 min of the mark time
OPT_TOL = 300                     # s: option quote freshness
OFFSETS = (0.5, 1.0, 1.5, 2.0)

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


def atm_series():
    cv = pd.read_parquet(CURVE).reset_index()
    tcol = next(c for c in ("ts_event", "index", "ts_recv") if c in cv.columns)
    cv["ts"] = pd.to_datetime(cv[tcol], utc=True)
    return cv[cv["symbol"] == "ZB.c.0"].set_index("ts")["close"].sort_index()


def fresh(series: pd.Series, t: pd.Timestamp, tol_s: int):
    """(value, gap_s) at last index <= t; value is NaN if gap > tol_s. series must be sorted, unique-ish."""
    idx = series.index
    pos = idx.searchsorted(t, side="right") - 1
    if pos < 0:
        return np.nan, np.inf
    gap = (t - idx[pos]).total_seconds()
    v = series.iloc[pos]
    return (float(v) if (gap <= tol_s and np.isfinite(v)) else np.nan), gap


def last_at(series: pd.Series, t: pd.Timestamp):
    """Last available value <= t regardless of staleness (for the optimistic salvage mark)."""
    idx = series.index
    pos = idx.searchsorted(t, side="right") - 1
    return float(series.iloc[pos]) if pos >= 0 and np.isfinite(series.iloc[pos]) else np.nan


def prot_leg(bbo, atm, surprise, off):
    b = bbo.copy()
    b["ts"] = pd.to_datetime(b["ts_event"], utc=True)
    rs = b["symbol"].str.extract(r"\s([CP])(\d+)$")
    b["right"], b["strike"] = rs[0], pd.to_numeric(rs[1], errors="coerce") / 10.0
    side = -np.sign(surprise)
    right = "P" if side > 0 else "C"
    cand = b[b["right"] == right]["strike"].dropna().unique()
    if side > 0:
        below = [k for k in cand if k <= atm - off + 0.01]
        strike = max(below) if below else None
    else:
        above = [k for k in cand if k >= atm + off - 0.01]
        strike = min(above) if above else None
    if strike is None:
        return None, None, None
    leg = b[(b["right"] == right) & (np.isclose(b["strike"], strike))].set_index("ts").sort_index()
    leg = leg[~leg.index.duplicated(keep="last")]
    bid = pd.to_numeric(leg["bid_px_00"], errors="coerce").replace(0, np.nan).dropna()
    ask = pd.to_numeric(leg["ask_px_00"], errors="coerce").replace(0, np.nan).dropna()
    return (bid if len(bid) else None), (ask if len(ask) else None), strike


def stats(v, yrs):
    v = np.asarray(v, float)
    eq = np.cumsum(v)
    dd = float((np.maximum.accumulate(eq) - eq).max()) if len(v) else float("nan")
    sh = v.mean() / v.std(ddof=1) * np.sqrt(len(v) / yrs) if len(v) > 1 and v.std() else float("nan")
    return dict(n=len(v), mean=v.mean(), total=eq[-1], pos=np.mean(v > 0), sharpe=sh,
                maxdd=dd, worst=v.min(), calmar=(eq[-1] / dd if dd > 0 else float("nan")))


def line(label, s):
    return (f"{label:30s} n={s['n']:2d} NET=${s['mean']:+6.0f} %pos={s['pos']:.2f} "
            f"Sharpe={s['sharpe']:+5.2f} maxDD=${s['maxdd']:6,.0f} worst=${s['worst']:+6.0f} Calmar={s['calmar']:+5.2f}")


def main():
    atm = atm_series()
    yrs = (max(dt.date.fromisoformat(e[0]) for e in EVENTS) - min(dt.date.fromisoformat(e[0]) for e in EVENTS)).days / 365.25

    ev = []
    for date, typ, hh, mm, s in EVENTS:
        f = CACHE / f"ozb_{date}.parquet"
        if not f.exists():
            continue
        d = dt.date.fromisoformat(date)
        t0 = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ET).astimezone(UTC)
        entry_t, exit_t = pd.Timestamp(t0) + pd.Timedelta(minutes=5), pd.Timestamp(t0) + pd.Timedelta(minutes=65)
        a0, _ = fresh(atm, entry_t, FUT_TOL)
        fe, _ = fresh(atm, entry_t, FUT_TOL)
        fx, _ = fresh(atm, exit_t, FUT_TOL)
        if not (np.isfinite(a0) and np.isfinite(fe) and np.isfinite(fx)):
            continue
        fut = float(-np.sign(s) * (fx - fe) * FUT_MULT - FUT_COST_D)
        ev.append(dict(date=date, typ=typ, s=s, atm=a0, entry_t=entry_t, exit_t=exit_t, fut=fut,
                       bbo=pd.read_parquet(f)))
    ev.sort(key=lambda e: e["date"])   # CHRONOLOGICAL so maxDD/Calmar (sequence-dependent) are meaningful
    print(f"events with fresh futures leg + OZB cache: {len(ev)}  (span {yrs:.1f}y)\n")
    print(line("NAKED futures (curve, this set)", stats([e["fut"] for e in ev], yrs)) + "  <- benchmark")
    print("  (authoritative naked benchmark, L3-priced CPI+FOMC: Sharpe ~1.25, maxDD ~$1,055, worst ~-$473)\n")

    for off in OFFSETS:
        naked, ov_pess, ov_opt = [], [], []
        lapsed = lapsed_win = priced = 0
        for e in ev:
            bid, ask, strike = prot_leg(e["bbo"], e["atm"], e["s"], off)
            if ask is None:
                continue
            ea, _ = fresh(ask, e["entry_t"], OPT_TOL)        # must be able to ENTER (buy at fresh ask)
            if not np.isfinite(ea) or ea <= 0:
                continue
            xb_fresh, _ = (fresh(bid, e["exit_t"], OPT_TOL) if bid is not None else (np.nan, np.inf))
            if np.isfinite(xb_fresh):
                xb_pess = xb_opt = xb_fresh
            else:                                            # hedge no longer quoted at exit
                lapsed += 1
                lapsed_win += int(e["fut"] > 0)
                xb_pess = 0.0                                # realistic: unsellable OTM hedge lapses
                xb_opt = max(last_at(bid, e["exit_t"]), 0.0) if bid is not None else 0.0  # generous salvage
            priced += 1
            naked.append(e["fut"])
            ov_pess.append(e["fut"] + (xb_pess - ea) * OPT_MULT - OPT_FEE)
            ov_opt.append(e["fut"] + (xb_opt - ea) * OPT_MULT - OPT_FEE)
        if priced < 8:
            print(f"-- {off:.1f}pt OTM: only {priced} priceable-entry events (skip) --")
            continue
        print(f"-- protective {off:.1f}pt OTM  (priced {priced}; exit unquoted on {lapsed}, of which "
              f"{lapsed_win} were futures WINNERS -> confirms lapse<->win selection) --")
        print("  " + line("naked (same events)", stats(naked, yrs)))
        print("  " + line("overlay PESS (lapse=0)", stats(ov_pess, yrs)))
        print("  " + line("overlay OPT (stale-mark)", stats(ov_opt, yrs)))
    print("\n[Overlay Sharpe>=naked AND higher Calmar under BOTH bounds -> protection earns its premium. "
          "Overlay worse under both -> per-trade option insurance does not help; the trade's risk is a "
          "losing-streak DD, not a per-trade blow-up, and OTM OZB strikes are illiquid at exit -> deploy naked.]")


if __name__ == "__main__":
    main()
