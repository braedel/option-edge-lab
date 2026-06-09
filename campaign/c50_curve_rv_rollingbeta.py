"""#2 robustness: re-run the curve-RV reversion with an ADAPTIVE hedge beta (re-fit periodically on a trailing
window, no look-ahead) instead of one fixed in-sample beta. If the edge holds with rolling beta, it isn't a
fixed-beta artifact and is deployable (you'd re-estimate beta live). 30-min bars; cost 2t (limit-execution
assumption, per the cost analysis); in-sample + OOS. Run in .venv-mbo.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PARQUET = Path(r"D:\TradingData\databento\curve\curve_ohlcv1m.parquet")
TICK = 1.0 / 32.0
DOLLAR = 31.25
BAR = "30min"
W = 96
EXIT, MAXHOLD = 0.3, 10 * 48
REFIT = 480            # re-fit beta every ~10 trading days
LOOKBACK = 250 * 48    # trailing ~1 year for beta (more stable hedge)
SPLIT = pd.Timestamp("2025-10-01", tz="UTC")


def main():
    df = pd.read_parquet(PARQUET).reset_index()
    tcol = next(c for c in ("ts_event", "index", "ts_recv") if c in df.columns)
    df["ts"] = pd.to_datetime(df[tcol], utc=True)
    wide = df.pivot_table(index="ts", columns="symbol", values="close")[["ZB.c.0", "ZN.c.0", "UB.c.0"]]
    bars = wide.resample(BAR).last().dropna()
    zb, zn, ub = bars["ZB.c.0"].values, bars["ZN.c.0"].values, bars["UB.c.0"].values
    idx = bars.index
    n = len(bars)

    # adaptive beta: at each bar use beta fit on the trailing LOOKBACK bars, re-fit every REFIT bars (no look-ahead)
    resid = np.full(n, np.nan)
    last_b = None
    for i in range(n):
        if i >= LOOKBACK and (i % REFIT == 0 or last_b is None):
            s = slice(i - LOOKBACK, i)
            Xw = np.column_stack([np.ones(LOOKBACK), zn[s], ub[s]])
            last_b, *_ = np.linalg.lstsq(Xw, zb[s], rcond=None)
        if last_b is not None:
            resid[i] = zb[i] - (last_b[0] + last_b[1] * zn[i] + last_b[2] * ub[i])
    resid = pd.Series(resid, index=idx)
    z = ((resid - resid.rolling(W).mean()) / resid.rolling(W).std()).values
    rv = resid.values
    yrs_in = (SPLIT - idx[LOOKBACK]).days / 365.25
    yrs_oos = (idx.max() - SPLIT).days / 365.25

    def bt(entry, cost, lo, hi, yrs):
        trades, pos, ei = [], 0, 0
        for i in range(n):
            if not np.isfinite(z[i]) or not np.isfinite(rv[i]):
                continue
            if pos == 0:
                if abs(z[i]) >= entry and lo <= idx[i] < hi:
                    pos, ei = -int(np.sign(z[i])), i
            elif abs(z[i]) <= EXIT or (i - ei) >= MAXHOLD:
                trades.append(pos * (rv[i] - rv[ei]) / TICK - cost)
                pos = 0
        v = np.array(trades)
        if len(v) < 4:
            return f"n={len(v)} (few)"
        sh = v.mean() / v.std(ddof=1) * np.sqrt(len(v) / yrs) if v.std() else float("nan")
        dd = (np.maximum.accumulate(np.cumsum(v)) - np.cumsum(v)).max()
        return f"n={len(v):3d} mean={v.mean():+5.2f}t %pos={np.mean(v>0):.2f} Sharpe~{sh:+5.2f} maxDD=${dd*DOLLAR:6,.0f}"

    print("=== curve RV with ADAPTIVE (rolling, no-look-ahead) beta, cost=2t ===")
    print("IN-SAMPLE (post-warmup .. 2025-10):")
    for entry in (2.0, 2.5, 3.0, 3.5):
        print(f"  entry{entry}: {bt(entry, 2.0, idx[LOOKBACK], SPLIT, yrs_in)}")
    print("OOS (2025-10..2026-04):")
    for entry in (2.5, 3.0):
        print(f"  entry{entry}: {bt(entry, 2.0, SPLIT, idx.max() + pd.Timedelta('1D'), yrs_oos)}")
    print("\n[Holds with rolling beta ~ same Sharpe = robust (not a fixed-beta artifact). Collapses = fragile.]")


if __name__ == "__main__":
    main()
