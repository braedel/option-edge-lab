"""C14 - tearsheet sliced to 2023-01 -> current. S&P vs DEPLOY (audited) vs DEPLOY + tail hedge.
Signals computed on full history (need the momentum/vol warmup); displayed/scored on 2023+ only.
Honest: 2023-2025 is a bull with no crash -> trend lags, hedge bleeds. Short window (~42 mo) -> noisy.
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

U = ["SPY", "QQQ", "IWM", "EFA", "EEM", "SHY", "IEF", "TLT", "TIP", "LQD", "HYG",
     "DBC", "USO", "UNG", "DBA", "GLD", "SLV", "VNQ", "UUP", "FXE", "FXY"]
T, V, PREM, NOTIONAL = 0.10, 60, 0.0060, 0.30
START = "2023-01-01"
OUT = r"D:\workspace\options-edge-lab\reports\tearsheet_2023_to_now.png"

px = pd.DataFrame({t: load(t) for t in U}).sort_index().dropna(how="all")
ret = px.pct_change()
me = pd.DatetimeIndex(sorted(ret.index.to_series().groupby([ret.index.year, ret.index.month]).last().values))
vol = ret.rolling(V).std() * np.sqrt(252)
sig = sum(np.sign(px / px.shift(lb) - 1) for lb in (21, 63, 126, 252)) / 4
held = (sig * (T / vol)).loc[me].reindex(ret.index, method="ffill").shift(1)
trend = (held * ret).mean(axis=1) - 0.0002 * held.diff().abs().mean(axis=1)
tvt = trend * (T / (trend.rolling(V).std() * np.sqrt(252))).clip(upper=3).shift(1)
p6040 = 0.6 * ret["SPY"] + 0.4 * ret["IEF"]
idx = tvt.dropna().index.intersection(p6040.dropna().index)
deploy = (0.5 * tvt.reindex(idx) + 0.5 * p6040.reindex(idx)).dropna()

dep_m = (1 + deploy).resample("ME").prod() - 1
spy_m = ((1 + ret["SPY"]).resample("ME").prod() - 1).reindex(dep_m.index)
payoff = np.minimum(np.maximum(-spy_m - 0.05, 0.0), 0.15)
hed_m = dep_m + NOTIONAL * (payoff - PREM)

# slice to 2023+
m = dep_m.index >= pd.Timestamp(START)
spy_m, dep_m, hed_m = spy_m[m].dropna(), dep_m[m].dropna(), hed_m[m].dropna()
common = spy_m.index.intersection(dep_m.index).intersection(hed_m.index)
spy_m, dep_m, hed_m = spy_m.reindex(common), dep_m.reindex(common), hed_m.reindex(common)


def shp(x):
    return float(x.mean() / x.std() * np.sqrt(12))


def mdd(e):
    return float((e / e.cummax() - 1).min() * 100)


def tot(e):
    return float((e.iloc[-1] - 1) * 100)


series = {"S&P 500 (SPY)": (spy_m, "#999999", 1.6),
          "DEPLOY (trend + 60/40)": (dep_m, "#d62728", 2.0),
          "DEPLOY + options tail hedge": (hed_m, "#1f77b4", 2.0)}
eq = {k: (1 + v[0]).cumprod() for k, v in series.items()}
uw = {k: e / e.cummax() - 1 for k, e in eq.items()}

fig, (a1, a2) = plt.subplots(2, 1, figsize=(13, 8.5), height_ratios=[2.4, 1], sharex=True)
for k, (r, c, lw) in series.items():
    a1.plot(eq[k].index, eq[k], color=c, lw=lw,
            label=f"{k}: total {tot(eq[k]):+.0f}%, Sharpe {shp(r):.2f}, maxDD {mdd(eq[k]):.0f}%")
a1.set_ylabel("Growth of $1"); a1.grid(True, alpha=0.25); a1.legend(loc="upper left", framealpha=0.9)
a1.set_title(f"2023 -> today: S&P vs DEPLOY vs DEPLOY+tail-hedge  ({eq['S&P 500 (SPY)'].index.min().date()} -> {eq['S&P 500 (SPY)'].index.max().date()}, ~{len(common)} months)",
             fontsize=13, fontweight="bold")
a2.plot(uw["S&P 500 (SPY)"].index, uw["S&P 500 (SPY)"] * 100, color="#999999", lw=1.2, label="S&P 500")
a2.fill_between(uw["DEPLOY (trend + 60/40)"].index, uw["DEPLOY (trend + 60/40)"] * 100, 0, color="#d62728", alpha=0.20)
a2.plot(uw["DEPLOY (trend + 60/40)"].index, uw["DEPLOY (trend + 60/40)"] * 100, color="#d62728", lw=1.5, label="DEPLOY")
a2.plot(uw["DEPLOY + options tail hedge"].index, uw["DEPLOY + options tail hedge"] * 100, color="#1f77b4", lw=1.5, label="DEPLOY + hedge")
a2.set_ylabel("Drawdown %"); a2.set_title("Underwater (drawdown from peak)", fontsize=11)
a2.legend(loc="lower left", framealpha=0.9); a2.grid(True, alpha=0.25)
a2.xaxis.set_major_locator(mdates.MonthLocator((1, 7))); a2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
fig.text(0.012, 0.005,
         "2023-2025 = strong equity bull, no crash: trend-following's WEAKEST regime and the hedge bleeds premium (nothing to pay it off). "
         f"~{len(common)}-month window -> Sharpe SE ~0.7, NOT significant. Monthly. Hedge @ realistic 0.6%/mo. This is a regime snapshot, not proof.",
         fontsize=8.0, color="0.35")
fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig(OUT, dpi=130)
print("saved:", OUT)
for k in series:
    print(f"  {k:30s}: total {tot(eq[k]):+.1f}%  Sharpe {shp(series[k][0]):.2f}  maxDD {mdd(eq[k]):.1f}%")
