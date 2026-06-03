"""C8 - the deployable Sharpe>1 portfolio + surgical options tail hedge, with tearsheet.

Sleeve = diversified blended-lookback TREND on 21 ETFs (xsec dropped: it was weak, 0.35/0.22-OOS).
Deployable = equal-risk 50% (vol-targeted trend) + 50% (60/40). Then a MODELED rolling 1m SPY put
SPREAD (5%->20% OTM) tail hedge sized to the portfolio's equity beta -- to trim the fast crashes trend
is too slow to catch. Option premium has no free lunch, so it's shown as a cost/benefit, not a freebie.
"""
from __future__ import annotations

import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, r"D:\workspace\options-edge-lab\campaign")
from c5_tsmom import load  # noqa: E402

UNIVERSE = ["SPY", "QQQ", "IWM", "EFA", "EEM", "SHY", "IEF", "TLT", "TIP", "LQD", "HYG",
            "DBC", "USO", "UNG", "DBA", "GLD", "SLV", "VNQ", "UUP", "FXE", "FXY"]
TARGET, VOLWIN, COST = 0.10, 60, 0.0002
OUT = r"D:\workspace\options-edge-lab\reports\deployable_pnl_underwater.png"


def S(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(252)) if len(r) > 50 and r.std() else np.nan


def MDD(e):
    return float((e / e.cummax() - 1).min() * 100)


def scale10(x):
    return x * (0.10 / (x.std() * np.sqrt(252)))


def main():
    px = pd.DataFrame({t: load(t) for t in UNIVERSE}).sort_index().dropna(how="all")
    ret = px.pct_change()
    me = pd.DatetimeIndex(sorted(ret.index.to_series().groupby([ret.index.year, ret.index.month]).last().values))
    vol = ret.rolling(VOLWIN).std() * np.sqrt(252)

    sig = sum(np.sign(px / px.shift(lb) - 1) for lb in (21, 63, 126, 252)) / 4
    desired = sig * (TARGET / vol)
    held = desired.loc[desired.index.isin(me)].reindex(ret.index, method="ffill").shift(1)
    trend = (held * ret).mean(axis=1) - (COST * held.diff().abs()).mean(axis=1)
    trend_vt = (trend * (TARGET / (trend.rolling(VOLWIN).std() * np.sqrt(252))).clip(upper=3).shift(1)).dropna()

    p6040 = 0.6 * ret["SPY"] + 0.4 * ret["IEF"]
    idx = trend_vt.index.intersection(p6040.dropna().index)
    deploy = (0.5 * scale10(trend_vt.reindex(idx)) + 0.5 * scale10(p6040.reindex(idx))).dropna()
    spy = ret["SPY"].reindex(deploy.index)

    # ---- modeled options tail hedge (monthly put SPREAD on SPY, sized to ~equity beta) ----
    spy_m = (1 + ret["SPY"]).resample("ME").prod() - 1
    deploy_m = (1 + deploy).resample("ME").prod() - 1
    beta = 0.30  # DEPLOY's approx SPY-notional (half of a 60/40 that is 60% SPY)
    print("=== options tail-hedge sensitivity (monthly put spread 5%->20% OTM, sized to 0.30 notional) ===")
    best = None
    for prem in (0.0020, 0.0030, 0.0040):  # premium %/month of hedged notional
        payoff = np.minimum(np.maximum(-spy_m - 0.05, 0.0), 0.15)
        hedge_m = beta * (payoff - prem)
        hed = (deploy_m + hedge_m).dropna()
        e = (1 + hed).cumprod()
        print(f"  premium {prem*1e2:.1f}%/mo (~{prem*1200:.1f}%/yr): Sharpe={hed.mean()/hed.std()*np.sqrt(12):.2f} "
              f"maxDD={MDD(e):6.1f}%  (vs unhedged Sharpe={deploy_m.mean()/deploy_m.std()*np.sqrt(12):.2f} "
              f"maxDD={MDD((1+deploy_m).cumprod()):.1f}%)")
        if prem == 0.0030:
            best = hed

    # ---- summary table (daily) ----
    print("\n=== summary (daily, full + OOS>=2016) ===")
    for nm, r in [("TREND sleeve (21-ETF)", trend_vt), ("DEPLOY 50/50 (Sharpe>1)", deploy),
                  ("SPY", spy), ("60/40", p6040.reindex(deploy.index))]:
        r = r.dropna(); y = r.index.year
        print(f"  {nm:26s} Sharpe={S(r):5.2f} OOS={S(r[y>=2016]):5.2f} vol={r.std()*np.sqrt(252)*100:4.1f}% maxDD={MDD((1+r).cumprod()):6.1f}%")

    # ---- tearsheet ----
    df = pd.DataFrame({"DEPLOY": deploy, "60/40": p6040.reindex(deploy.index), "SPY": spy}).dropna()
    eq = (1 + df).cumprod()
    uw = eq / eq.cummax() - 1
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(13, 8.5), height_ratios=[2.4, 1], sharex=True)
    for c, col, lw in [("DEPLOY", "#d62728", 2.2), ("60/40", "#2ca02c", 1.1), ("SPY", "#999999", 1.0)]:
        a1.plot(eq.index, eq[c], color=col, lw=lw, label=f"{c}: Sharpe {S(df[c]):.2f}, maxDD {MDD(eq[c]):.0f}%")
    a1.set_yscale("log"); a1.set_ylabel("Growth of $1 (log)"); a1.grid(True, which="both", alpha=0.25)
    a1.legend(loc="upper left", framealpha=0.9)
    a1.set_title(f"Sharpe>1 deployable: diversified TREND overlay + 60/40  ({eq.index.min().date()} → {eq.index.max().date()})",
                 fontsize=13, fontweight="bold")
    for yr in (2008, 2020, 2022):
        a1.axvspan(pd.Timestamp(yr, 1, 1), pd.Timestamp(yr, 12, 31), color="red", alpha=0.05)
    a2.fill_between(uw.index, uw["DEPLOY"] * 100, 0, color="#d62728", alpha=0.30)
    a2.plot(uw.index, uw["DEPLOY"] * 100, color="#d62728", lw=1.2, label="DEPLOY")
    a2.plot(uw.index, uw["SPY"] * 100, color="#999999", lw=0.9, label="SPY")
    a2.set_ylabel("Drawdown %"); a2.set_title("Underwater (drawdown from peak)", fontsize=11)
    a2.legend(loc="lower left", framealpha=0.9); a2.grid(True, alpha=0.25)
    a2.xaxis.set_major_locator(mdates.YearLocator(2)); a2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.text(0.012, 0.005, "DEPLOY = 50% vol-targeted diversified-trend overlay (21 ETFs, blended lookbacks) + 50% 60/40, equal risk, monthly, net ~2bps/rebal. "
             "Trend is futures-native; ETF proxy is conservative.", fontsize=8.5, color="0.35")
    fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig(OUT, dpi=130)
    print("\nsaved:", OUT)


if __name__ == "__main__":
    main()
