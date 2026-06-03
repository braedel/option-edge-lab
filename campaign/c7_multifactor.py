"""C7 - multi-factor, multi-asset futures portfolio (trend + cross-sectional momentum), vol-targeted.

Principled (pre-registered, no tuning) levers toward higher Sharpe + lower DD:
  - 21 ETFs across equities/bonds/credit/commodities/metals/REIT/FX (diversification).
  - TREND: blended 1/3/6/12m time-series momentum sign, inverse-vol sized.
  - XSEC: 12m cross-sectional momentum (long winners / short losers), dollar-neutral, inverse-vol.
  - Combine 50/50, then vol-target the combined sleeve to 10% annualized.
Reports full + sealed-OOS Sharpe, vol, maxDD, SPY-corr vs the 8-ETF baseline and 60/40.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, r"D:\workspace\options-edge-lab\campaign")
from c5_tsmom import load  # noqa: E402

UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "SHY", "IEF", "TLT", "TIP", "LQD", "HYG",
            "DBC", "USO", "UNG", "DBA", "GLD", "SLV", "VNQ", "UUP", "FXE", "FXY"]
TARGET, VOLWIN, COST = 0.10, 60, 0.0002


def me_index(ret):
    return pd.DatetimeIndex(sorted(ret.index.to_series().groupby([ret.index.year, ret.index.month]).last().values))


def sleeve(desired, ret, me, cost=COST):
    held = desired.loc[desired.index.isin(me)].reindex(ret.index, method="ffill").shift(1)
    return (held * ret).mean(axis=1) - (cost * held.diff().abs()).mean(axis=1)


def vol_target(r, target=TARGET, win=VOLWIN, cap=3.0):
    scale = (target / (r.rolling(win).std() * np.sqrt(252))).clip(upper=cap).shift(1)
    return r * scale


def S(r):
    r = r.dropna()
    return r.mean() / r.std() * np.sqrt(252) if len(r) > 50 and r.std() else np.nan


def MDD(r):
    e = (1 + r.dropna()).cumprod()
    return (e / e.cummax() - 1).min() * 100


def row(name, r, bench):
    r = r.dropna()
    y = r.index.year
    return (f"  {name:26s} Sharpe={S(r):5.2f}  vol={r.std()*np.sqrt(252)*100:4.1f}%  "
            f"maxDD={MDD(r):6.1f}%  OOS(>=2016) Sharpe={S(r[y>=2016]):5.2f}  corrSPY={r.corr(bench.reindex(r.index)):5.2f}")


def main():
    px = pd.DataFrame({t: load(t) for t in UNIVERSE}).sort_index().dropna(how="all")
    ret = px.pct_change()
    me = me_index(ret)
    vol = ret.rolling(VOLWIN).std() * np.sqrt(252)

    trend_sig = sum(np.sign(px / px.shift(lb) - 1) for lb in (21, 63, 126, 252)) / 4
    r12 = px / px.shift(252) - 1
    xsec_sig = r12.rank(axis=1) .sub(r12.rank(axis=1).mean(axis=1), axis=0)  # cross-sectionally demeaned ranks
    xsec_sig = xsec_sig.div(xsec_sig.abs().sum(axis=1), axis=0)  # normalize gross exposure to ~1

    trend = sleeve(trend_sig * (TARGET / vol), ret, me)
    xsec = sleeve(xsec_sig * 10.0, ret, me)  # xsec already vol/gross-normalized; scale up to ~10% vol range
    combo = (0.5 * trend + 0.5 * xsec).dropna()
    combo_vt = vol_target(combo).dropna()

    spy = ret["SPY"]
    p6040 = 0.6 * ret["SPY"] + 0.4 * ret["IEF"]

    print(f"universe {len(UNIVERSE)} ETFs  {px.index.min().date()}..{px.index.max().date()}")
    print("\n=== sleeves (21-ETF multi-asset) ===")
    print(row("TREND (blended)", trend, spy))
    print(row("XSEC (12m rank L/S)", xsec, spy))
    print(row("TREND+XSEC combo", combo, spy))
    print(row("combo vol-targeted 10%", combo_vt, spy))
    print("\n=== benchmarks ===")
    print(row("SPY", spy, spy))
    print(row("60/40", p6040, spy))

    # deployable: equal-risk blend of the vol-targeted multi-factor sleeve with 60/40
    def scale10(x):
        return x * (0.10 / (x.std() * np.sqrt(252)))
    idx = combo_vt.index.intersection(p6040.index)
    deploy = (0.5 * scale10(combo_vt.reindex(idx)) + 0.5 * scale10(p6040.reindex(idx))).dropna()
    print("\n=== deployable portfolio (50% multi-factor sleeve + 50% 60/40, equal risk) ===")
    print(row("DEPLOY", deploy, spy))

    print("\n=== crisis calendar returns % (combo_vt) ===")
    cyr = combo_vt.groupby(combo_vt.index.year).apply(lambda r: (1 + r).prod() - 1) * 100
    syr = spy.groupby(spy.index.year).apply(lambda r: (1 + r).prod() - 1) * 100
    for yr in (2008, 2018, 2020, 2022, 2023, 2024, 2025, 2026):
        if yr in cyr.index:
            print(f"  {yr}: combo {cyr[yr]:+6.1f}%   SPY {syr.get(yr, np.nan):+6.1f}%")

    combo_vt.to_frame("ret").to_parquet(r"D:\workspace\options-edge-lab\campaign\data\combo_vt.parquet")
    deploy.to_frame("ret").to_parquet(r"D:\workspace\options-edge-lab\campaign\data\deploy.parquet")


if __name__ == "__main__":
    main()
