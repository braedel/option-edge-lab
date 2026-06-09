"""#2 curve-RV FIRST LOOK (structure, before designing a strategy). Local 1-min bars (c46 download).
IN-SAMPLE only (<2025-10) to preserve the OOS window.

Reports: (1) 1-min log-return correlation across ZN/ZF/ZB/UB/TN/ES (the curve's one-factor-ness);
(2) cointegration ZB~ZN (and ZB~ZN+UB): hedge beta, residual AR(1) -> mean-reversion half-life (minutes) &
residual std in ticks (is there a stationary spread with a TRADEABLE half-life?); (3) lead-lag: lagged
cross-correlation of 1-min returns ZN->ZB and ES->ZB (does anything lead ZB at the minute scale we can trade?).
Roll caveat: continuous-front has roll jumps; returns are winsorized for corr/lead-lag, and the level
cointegration is a first look (a proper version roll-adjusts). Run in .venv-mbo.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

PARQUET = Path(r"D:\TradingData\databento\curve\curve_ohlcv1m.parquet")
TICK_ZB = 1.0 / 32.0


def ols(y, X):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return b


def main():
    df = pd.read_parquet(PARQUET).reset_index()
    tcol = next(c for c in ("ts_event", "index", "ts_recv") if c in df.columns)
    df["ts"] = pd.to_datetime(df[tcol], utc=True)
    wide = df.pivot_table(index="ts", columns="symbol", values="close")
    wide = wide[wide.index < pd.Timestamp("2025-10-01", tz="UTC")].dropna()
    print(f"aligned in-sample minutes: {len(wide):,}  ({wide.index.min().date()}..{wide.index.max().date()})")
    syms = ["ZF.c.0", "ZN.c.0", "TN.c.0", "ZB.c.0", "UB.c.0", "ES.c.0"]
    wide = wide[[s for s in syms if s in wide.columns]]

    ret = np.log(wide).diff()
    ret = ret.clip(ret.quantile(0.001), ret.quantile(0.999), axis=1).dropna()   # winsorize roll/outlier bars
    print("\n1-min return correlation:")
    print((ret.corr() * 100).round(1).to_string())

    print("\nCointegration / mean-reversion (ZB residual):")
    zb = wide["ZB.c.0"].values
    for name, xs in [("ZB~ZN", ["ZN.c.0"]), ("ZB~ZN+UB", ["ZN.c.0", "UB.c.0"])]:
        X = np.column_stack([np.ones(len(wide))] + [wide[s].values for s in xs])
        b = ols(zb, X)
        resid = zb - X @ b
        r0, r1 = resid[:-1], resid[1:]
        phi = ols(r1 - r1.mean(), np.column_stack([np.ones(len(r0)), r0 - r0.mean()]))[1]
        hl = -np.log(2) / np.log(phi) if 0 < phi < 1 else float("inf")
        betas = ", ".join(f"{s}={bb:+.3f}" for s, bb in zip(xs, b[1:]))
        print(f"  {name:9s}: {betas}  resid std={resid.std()/TICK_ZB:.1f} ticks  AR(1) phi={phi:.4f}  "
              f"half-life={hl:.1f} min")

    print("\nLead-lag (corr of ZB 1-min return vs other return lagged k min; k>0 = other LEADS ZB):")
    zbr = ret["ZB.c.0"]
    for s in ("ZN.c.0", "ES.c.0"):
        if s not in ret.columns:
            continue
        cc = {k: zbr.corr(ret[s].shift(k)) for k in range(-3, 4)}
        best = max(cc, key=lambda k: abs(cc[k]))
        print(f"  {s} vs ZB: " + " ".join(f"k{k:+d}={cc[k]*100:+.0f}" for k in range(-3, 4)) +
              f"   | peak k={best:+d} ({cc[best]*100:+.0f})")
    print("\n[Stationary residual w/ a multi-minute half-life + meaningful tick std = a tradeable curve-RV "
          "mean-reversion. Peak lead-lag at k>=1 min = a capturable lead (k=0 dominant = contemporaneous, colo-only).]")


if __name__ == "__main__":
    main()
