"""#2 curve-RV mean-reversion backtest (v3: in-sample sweep + OOS). Trade the ZB~ZN+UB cointegration residual
on 30-min bars: enter |z|>=ENTRY (short rich / long cheap), exit on reversion (|z|<=EXIT) or max-hold.
Hedge beta fit on IN-SAMPLE only (<2025-10), applied frozen to the OOS window (2025-10..2026-04). z-score
rolling (causal). Conservative multi-leg cost in ZB-ticks. Reports in-sample sweep + OOS for the consistent
configs. Unlike the surprise trade, the curve cointegration isn't tied to the release calendar -> the OOS
window is a less-confounded test here. Run in .venv-mbo.
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
SPLIT = pd.Timestamp("2025-10-01", tz="UTC")


def main():
    df = pd.read_parquet(PARQUET).reset_index()
    tcol = next(c for c in ("ts_event", "index", "ts_recv") if c in df.columns)
    df["ts"] = pd.to_datetime(df[tcol], utc=True)
    wide = df.pivot_table(index="ts", columns="symbol", values="close")[["ZB.c.0", "ZN.c.0", "UB.c.0"]]
    bars = wide.resample(BAR).last().dropna()
    ins = bars[bars.index < SPLIT]
    X_in = np.column_stack([np.ones(len(ins)), ins["ZN.c.0"].values, ins["UB.c.0"].values])
    b, *_ = np.linalg.lstsq(X_in, ins["ZB.c.0"].values, rcond=None)
    print(f"hedge (in-sample beta): ZB={b[0]:+.2f}{b[1]:+.3f}*ZN{b[2]:+.3f}*UB")

    resid = pd.Series(bars["ZB.c.0"].values - (b[0] + b[1] * bars["ZN.c.0"].values + b[2] * bars["UB.c.0"].values),
                      index=bars.index)
    z = ((resid - resid.rolling(W).mean()) / resid.rolling(W).std())
    idx, zv, rv = bars.index, z.values, resid.values
    yrs_in = (ins.index.max() - ins.index.min()).days / 365.25
    yrs_oos = (bars.index.max() - SPLIT).days / 365.25

    def bt(entry, cost, lo, hi, yrs):
        trades, pos, ei = [], 0, 0
        for i in range(len(zv)):
            if not np.isfinite(zv[i]):
                continue
            if pos == 0:
                if abs(zv[i]) >= entry and lo <= idx[i] < hi:      # enter only within the period
                    pos, ei = -int(np.sign(zv[i])), i
            elif abs(zv[i]) <= EXIT or (i - ei) >= MAXHOLD:
                trades.append(pos * (rv[i] - rv[ei]) / TICK - cost)
                pos = 0
        v = np.array(trades)
        if len(v) < 4:
            return f"n={len(v)} (few)"
        sh = v.mean() / v.std(ddof=1) * np.sqrt(len(v) / yrs) if v.std() else float("nan")
        dd = (np.maximum.accumulate(np.cumsum(v)) - np.cumsum(v)).max()
        return (f"n={len(v):3d} ({len(v)/yrs:3.0f}/yr) mean={v.mean():+5.2f}t %pos={np.mean(v>0):.2f} "
                f"Sharpe~{sh:+5.2f} maxDD=${dd*DOLLAR:6,.0f} total=${v.sum()*DOLLAR:+7,.0f}")

    lo_in, hi_in = idx.min(), SPLIT
    print("\n=== IN-SAMPLE sweep ===")
    for entry in (2.0, 2.5, 3.0, 3.5):
        for cost in (2.0, 3.0):
            print(f"  entry{entry} cost{cost:.0f}: {bt(entry, cost, lo_in, hi_in, yrs_in)}")
    print("\n=== OOS (2025-10..2026-04, frozen in-sample beta) ===")
    for entry in (2.5, 3.0):
        for cost in (2.0, 3.0):
            print(f"  entry{entry} cost{cost:.0f}: {bt(entry, cost, SPLIT, idx.max() + pd.Timedelta('1D'), yrs_oos)}")
    print("\n[OOS Sharpe>1 at cost~2t = a real curve-RV sleeve in the target range -> refine multi-leg "
          "execution cost + rolling beta. OOS collapse = in-sample overfit / regime.]")


if __name__ == "__main__":
    main()
