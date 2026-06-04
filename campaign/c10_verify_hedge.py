"""C10 - verify the options-hedge Sharpe 'lift' under REALISTIC premiums + crash-exclusion.

My headline hedge used 0.30%/mo for a 5->20% OTM 1m SPY put spread. Realistic SPX put-spread cost is
~0.5-0.8%/mo (the long 5% put alone is ~0.6-1.0% of spot at normal VIX). This re-tests whether the Sharpe
'lift' survives honest premiums, and whether it's just 2008+2020.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, r"D:\workspace\options-edge-lab\campaign")
from c5_tsmom import load  # noqa: E402

U = ["SPY", "QQQ", "IWM", "EFA", "EEM", "SHY", "IEF", "TLT", "TIP", "LQD", "HYG",
     "DBC", "USO", "UNG", "DBA", "GLD", "SLV", "VNQ", "UUP", "FXE", "FXY"]
T, V = 0.10, 60
px = pd.DataFrame({t: load(t) for t in U}).sort_index().dropna(how="all")
ret = px.pct_change()
me = pd.DatetimeIndex(sorted(ret.index.to_series().groupby([ret.index.year, ret.index.month]).last().values))
vol = ret.rolling(V).std() * np.sqrt(252)
sig = sum(np.sign(px / px.shift(lb) - 1) for lb in (21, 63, 126, 252)) / 4
held = (sig * (T / vol)).loc[me].reindex(ret.index, method="ffill").shift(1)
trend = (held * ret).mean(axis=1) - 0.0002 * held.diff().abs().mean(axis=1)
tvt = (trend * (T / (trend.rolling(V).std() * np.sqrt(252))).clip(upper=3).shift(1))
p6040 = 0.6 * ret["SPY"] + 0.4 * ret["IEF"]
idx = tvt.dropna().index.intersection(p6040.dropna().index)
a, b = tvt.reindex(idx), p6040.reindex(idx)
deploy = (0.5 * a * (0.10 / (a.std() * np.sqrt(252))) + 0.5 * b * (0.10 / (b.std() * np.sqrt(252)))).dropna()

spy_m = (1 + ret["SPY"]).resample("ME").prod() - 1
d_m = (1 + deploy).resample("ME").prod() - 1
spy_m = spy_m.reindex(d_m.index)
NOTIONAL = 0.30
payoff = np.minimum(np.maximum(-spy_m - 0.05, 0.0), 0.15)


def shp(x):
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(12))


def mdd(x):
    e = (1 + x.dropna()).cumprod()
    return float((e / e.cummax() - 1).min() * 100)


print(f"DEPLOY (unhedged, monthly): Sharpe {shp(d_m):.2f}  maxDD {mdd(d_m):.1f}%")
print(f"months SPY < -5%: {(spy_m < -0.05).sum()} of {len(spy_m)}  -> hedge pays in "
      f"{(payoff > 0).mean()*100:.0f}% of months")

print("\n[verify] hedge Sharpe + maxDD vs PREMIUM (realistic ~0.5-0.8%/mo):")
for prem in (0.0030, 0.0050, 0.0070, 0.0100):
    h = (d_m + NOTIONAL * (payoff - prem)).dropna()
    print(f"   premium {prem*100:.2f}%/mo (~{prem*1200:4.1f}%/yr): Sharpe {shp(h):.2f}  maxDD {mdd(h):.1f}%  "
          f"(deltaSharpe {shp(h)-shp(d_m):+.2f})")

print("\n[verify] at a REALISTIC 0.60%/mo premium, exclude big crashes:")
yr = d_m.index.year
for label, excl in [("full sample", []), ("ex-2008", [2008]), ("ex-2020", [2020]), ("ex-2008&2020", [2008, 2020])]:
    m = ~yr.isin(excl)
    dh = (d_m[m] + NOTIONAL * (payoff[m] - 0.0060)).dropna()
    du = d_m[m].dropna()
    print(f"   {label:14s}: unhedged Sharpe {shp(du):.2f} | +hedge {shp(dh):.2f}  (delta {shp(dh)-shp(du):+.2f}), "
          f"maxDD {mdd(du):.1f}% -> {mdd(dh):.1f}%")
