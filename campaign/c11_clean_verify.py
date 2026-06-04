"""C11 - rigorous, artifact-free rebuild + verification of DEPLOY. No options hedge, no look-ahead,
no full-sample scaling, with short-borrow cost. Every number here is meant to be deployable-honest.

Fixes vs prior:
  - DROP the options hedge entirely (modeled premium was optimistic + unverifiable without data).
  - REMOVE full-sample-vol scaling (scale10) -> blend the ex-ante vol-targeted sleeve 50/50 with 60/40.
  - ADD short-borrow cost on short ETF legs (futures would avoid it; ETF proxy must pay it).
  - PROVE no look-ahead with a perturbation test (corrupt future data -> past returns must not move).
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
PX = pd.DataFrame({t: load(t) for t in U}).sort_index().dropna(how="all")


def trend_sleeve(px, cost=0.0002, borrow_yr=0.0):
    ret = px.pct_change()
    me = pd.DatetimeIndex(sorted(ret.index.to_series().groupby([ret.index.year, ret.index.month]).last().values))
    vol = ret.rolling(V).std() * np.sqrt(252)
    sig = sum(np.sign(px / px.shift(lb) - 1) for lb in (21, 63, 126, 252)) / 4
    held = (sig * (T / vol)).loc[me].reindex(ret.index, method="ffill").shift(1)
    gross = (held * ret).mean(axis=1)
    tc = cost * held.diff().abs().mean(axis=1)
    bc = (borrow_yr / 252) * held.clip(upper=0).abs().mean(axis=1)  # borrow on short notional
    trend = gross - tc - bc
    return (trend * (T / (trend.rolling(V).std() * np.sqrt(252))).clip(upper=3).shift(1))


def deploy_clean(px, cost=0.0002, borrow_yr=0.0):
    tvt = trend_sleeve(px, cost, borrow_yr)
    ret = px.pct_change()
    p = (0.6 * ret["SPY"] + 0.4 * ret["IEF"])
    idx = tvt.dropna().index.intersection(p.dropna().index)
    return (0.5 * tvt.reindex(idx) + 0.5 * p.reindex(idx)).dropna()  # ex-ante 50/50, no full-sample scaling


def deploy_old(px):  # the prior version with full-sample scale10 (for the audit contrast)
    tvt = trend_sleeve(px)
    ret = px.pct_change()
    p = (0.6 * ret["SPY"] + 0.4 * ret["IEF"])
    idx = tvt.dropna().index.intersection(p.dropna().index)
    a, b = tvt.reindex(idx), p.reindex(idx)
    s10 = lambda x: x * (0.10 / (x.std() * np.sqrt(252)))
    return (0.5 * s10(a) + 0.5 * s10(b)).dropna()


def S(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(252)) if len(r) > 50 and r.std() else np.nan


def MDD(r):
    e = (1 + r.dropna()).cumprod()
    return float((e / e.cummax() - 1).min() * 100)


def audit(fn):  # corrupt the last 8 rows; returns before then must be identical
    base = fn(PX)
    px2 = PX.copy()
    px2.iloc[-8:] = px2.iloc[-8:] * 5.0
    pert = fn(px2)
    cut = PX.index[-15]
    pre = base.index[(base.index < cut)]
    return float((base.reindex(pre) - pert.reindex(pre)).abs().max())


print("=== LOOK-AHEAD AUDIT (max change in PAST returns when FUTURE data is corrupted; 0 = clean) ===")
print(f"  deploy_OLD (full-sample scale10): {audit(deploy_old):.2e}   <- nonzero = LOOK-AHEAD (the artifact)")
print(f"  deploy_CLEAN (ex-ante)          : {audit(deploy_clean):.2e}   <- 0 = no look-ahead")

d_old = deploy_old(PX)
d = deploy_clean(PX)
y = d.index.year
print("\n=== artifact impact (Sharpe) ===")
print(f"  OLD (look-ahead scaling): Sharpe {S(d_old):.2f}  maxDD {MDD(d_old):.1f}%")
print(f"  CLEAN (ex-ante)         : Sharpe {S(d):.2f}  maxDD {MDD(d):.1f}%   OOS>=2016 {S(d[y>=2016]):.2f}")

print("\n=== CLEAN DEPLOY — full verification ===")
print(f"  full   : Sharpe {S(d):.2f}  maxDD {MDD(d):.1f}%  vol {d.std()*np.sqrt(252)*100:.1f}%")
print(f"  OOS>=2016: Sharpe {S(d[y>=2016]):.2f}")
print(f"  ex-2008 (>=2010): Sharpe {S(d[y>=2010]):.2f}  maxDD {MDD(d[y>=2010]):.1f}%")
print("  sub-periods:", {f"{a}-{b}": round(S(d[(y>=a)&(y<=b)]), 2) for a, b in [(2008,2012),(2013,2017),(2018,2022),(2023,2026)]})

print("\n=== cost + borrow stress (CLEAN) ===")
for c in (0.0002, 0.0005, 0.0010):
    for bw in (0.0, 0.01, 0.02):
        dc = deploy_clean(PX, c, bw)
        print(f"  cost {c*1e4:4.0f}bps  borrow {bw*100:.0f}%/yr: Sharpe {S(dc):.2f}  maxDD {MDD(dc):.1f}%")
