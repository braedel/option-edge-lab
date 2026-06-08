"""Study 2 / E4 - crypto trend-following (new market). Long/short and long/flat, vol-targeted, leak-free,
10bps crypto costs, annualized at 365 (crypto trades daily). Honest prior: high Sharpe-ish but brutal DD.
Measure vs the goal (Sharpe>2, win-most-months, low DD)."""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, r"D:\workspace\options-edge-lab\campaign")
from c5_tsmom import load  # noqa: E402

C = ["BTC", "ETH", "LTC", "BNB", "XRP"]
APR, V, T, COST = 365, 30, 0.10, 0.0010
px = pd.DataFrame({t: load(t) for t in C}).sort_index().dropna(how="all")
ret = px.pct_change()
we = pd.DatetimeIndex(sorted(ret.index.to_series().groupby([ret.index.isocalendar().year.values,
                                                            ret.index.isocalendar().week.values]).last().values))
vol = ret.rolling(V).std() * np.sqrt(APR)


def vt(r, target=T, win=V, cap=3.0):
    return r * (target / (r.rolling(win).std() * np.sqrt(APR))).clip(upper=cap).shift(1)


def sleeve(desired):
    held = desired.loc[desired.index.isin(we)].reindex(ret.index, method="ffill").shift(1)
    return vt((held * ret).mean(axis=1) - COST * held.diff().abs().mean(axis=1))


def S(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(APR)) if len(r) > 50 and r.std() else np.nan


def MDD(r):
    e = (1 + r.dropna()).cumprod()
    return float((e / e.cummax() - 1).min() * 100)


def posmo(r):
    m = (1 + r).resample("ME").prod() - 1
    return float((m > 0).mean() * 100), float((m <= 0).sum() / (len(r) / APR))


sig = sum(np.sign(px / px.shift(lb) - 1) for lb in (20, 50, 100, 200)) / 4
ls = sleeve(sig * (T / vol)).dropna()
lo = sleeve(sig.clip(lower=0) * (T / vol)).dropna()
bh = ret["BTC"].reindex(ls.index)

print(f"period {px.index.min().date()} .. {px.index.max().date()}  cryptos={list(px.columns)}")
for nm, r in [("crypto trend long/short", ls), ("crypto trend long/flat", lo), ("BTC buy&hold", bh)]:
    pm, ly = posmo(r)
    y = r.index.year
    print(f"  {nm:26s} Sharpe={S(r):5.2f}  OOS>=2021={S(r[y>=2021]):5.2f}  maxDD={MDD(r):6.1f}%  posMonths={pm:3.0f}%  losing/yr={ly:.1f}")

# look-ahead audit on the long/short sleeve
px2 = px.copy(); px2.iloc[-8:] = px2.iloc[-8:] * 5
ret2 = px2.pct_change(); vol2 = ret2.rolling(V).std() * np.sqrt(APR)
sig2 = sum(np.sign(px2 / px2.shift(lb) - 1) for lb in (20, 50, 100, 200)) / 4
h2 = (sig2 * (T / vol2)).loc[we].reindex(ret2.index, method="ffill").shift(1)
ls2 = vt((h2 * ret2).mean(axis=1) - COST * h2.diff().abs().mean(axis=1)).dropna()
cut = px.index[-15]
pre = ls.index[ls.index < cut]
print(f"\nlook-ahead audit (must be ~0): {(ls.reindex(pre)-ls2.reindex(pre)).abs().max():.2e}")
