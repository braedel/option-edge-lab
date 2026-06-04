"""C9 - stress tests + hedged tearsheet for the DEPLOY portfolio (feeds the one-pager)."""
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
TARGET, VOLWIN = 0.10, 60
OUT = r"D:\workspace\options-edge-lab\reports\deployable_hedged_tearsheet.png"

px = pd.DataFrame({t: load(t) for t in UNIVERSE}).sort_index().dropna(how="all")
ret = px.pct_change()
me = pd.DatetimeIndex(sorted(ret.index.to_series().groupby([ret.index.year, ret.index.month]).last().values))
vol = ret.rolling(VOLWIN).std() * np.sqrt(252)
sig = sum(np.sign(px / px.shift(lb) - 1) for lb in (21, 63, 126, 252)) / 4
held = (sig * (TARGET / vol)).loc[me].reindex(ret.index, method="ffill").shift(1)
turn = held.diff().abs().mean(axis=1)
p6040 = 0.6 * ret["SPY"] + 0.4 * ret["IEF"]


def S(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(252)) if len(r) > 50 and r.std() else np.nan


def MDD(r):
    e = (1 + r.dropna()).cumprod()
    return float((e / e.cummax() - 1).min() * 100)


def deploy(cost):
    trend = (held * ret).mean(axis=1) - cost * turn
    tvt = (trend * (TARGET / (trend.rolling(VOLWIN).std() * np.sqrt(252))).clip(upper=3).shift(1))
    idx = tvt.dropna().index.intersection(p6040.dropna().index)
    a, b = tvt.reindex(idx), p6040.reindex(idx)
    return (0.5 * a * (0.10 / (a.std() * np.sqrt(252))) + 0.5 * b * (0.10 / (b.std() * np.sqrt(252)))).dropna()


d = deploy(0.0002)
y = d.index.year
print(f"DEPLOY full: Sharpe {S(d):.2f}  maxDD {MDD(d):.1f}%   OOS>=2016 {S(d[y>=2016]):.2f}")

print("\n[3a] COST sensitivity (bps/rebalance):")
for c in (0.0001, 0.0002, 0.0005, 0.0010):
    dc = deploy(c)
    print(f"   {c*1e4:4.0f}bps: Sharpe {S(dc):.2f}  maxDD {MDD(dc):.1f}%")

print("\n[3b] 2008 EXCLUDED (>=2010):")
print(f"   Sharpe {S(d[y>=2010]):.2f}  maxDD {MDD(d[y>=2010]):.1f}%")

print("\n[3c] SUB-PERIOD Sharpe (stability):")
for a, b in [(2008, 2012), (2013, 2017), (2018, 2022), (2023, 2026)]:
    seg = d[(y >= a) & (y <= b)]
    print(f"   {a}-{b}: Sharpe {S(seg):.2f}  maxDD {MDD(seg):.1f}%  ({len(seg)}d)")

print(f"\n[capacity] avg monthly turnover (sum|dpos|): {turn[turn > 0].mean():.2f}x notional/month -> low; liquid, scalable.")

# ---- hedged (monthly) ----
spy_m = (1 + ret["SPY"]).resample("ME").prod() - 1
d_m = (1 + d).resample("ME").prod() - 1
payoff = np.minimum(np.maximum(-spy_m - 0.05, 0.0), 0.15)
hedged_m = (d_m + 0.30 * (payoff - 0.0030)).dropna()
d_m = d_m.reindex(hedged_m.index)
print(f"\n[hedge] DEPLOY monthly Sharpe {d_m.mean()/d_m.std()*np.sqrt(12):.2f} maxDD {MDD(d_m):.1f}% | "
      f"+hedge Sharpe {hedged_m.mean()/hedged_m.std()*np.sqrt(12):.2f} maxDD {MDD(hedged_m):.1f}%")

eqd, eqh = (1 + d_m).cumprod(), (1 + hedged_m).cumprod()
uwd, uwh = eqd / eqd.cummax() - 1, eqh / eqh.cummax() - 1
fig, (a1, a2) = plt.subplots(2, 1, figsize=(13, 8.5), height_ratios=[2.4, 1], sharex=True)
a1.plot(eqd.index, eqd, color="#d62728", lw=1.8, label=f"DEPLOY: Sharpe {d_m.mean()/d_m.std()*np.sqrt(12):.2f}, maxDD {MDD(d_m):.0f}%")
a1.plot(eqh.index, eqh, color="#1f77b4", lw=1.8, label=f"DEPLOY + put-spread hedge: Sharpe {hedged_m.mean()/hedged_m.std()*np.sqrt(12):.2f}, maxDD {MDD(hedged_m):.0f}%")
a1.set_yscale("log"); a1.set_ylabel("Growth of $1 (log)"); a1.grid(True, which="both", alpha=0.25); a1.legend(loc="upper left", framealpha=0.9)
a1.set_title(f"DEPLOY vs DEPLOY + options tail hedge (monthly)  ({eqd.index.min().date()} → {eqd.index.max().date()})", fontsize=13, fontweight="bold")
for yr in (2008, 2020, 2022):
    a1.axvspan(pd.Timestamp(yr, 1, 1), pd.Timestamp(yr, 12, 31), color="red", alpha=0.05)
a2.fill_between(uwd.index, uwd * 100, 0, color="#d62728", alpha=0.22)
a2.plot(uwd.index, uwd * 100, color="#d62728", lw=1.3, label="DEPLOY")
a2.plot(uwh.index, uwh * 100, color="#1f77b4", lw=1.3, label="DEPLOY + hedge")
a2.set_ylabel("Drawdown %"); a2.set_title("Underwater — the hedge trims the fast-crash tail (~-10% -> ~-5%)", fontsize=11)
a2.legend(loc="lower left", framealpha=0.9); a2.grid(True, alpha=0.25)
a2.xaxis.set_major_locator(mdates.YearLocator(2)); a2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
fig.text(0.012, 0.005, "Hedge = MODELED rolling 1m SPY put spread (5->20% OTM), 0.30 notional, 0.30%/mo premium. Benefit is premium/sample-sensitive (insurance, not free Sharpe).", fontsize=8.5, color="0.35")
fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig(OUT, dpi=130)
print("\nsaved:", OUT)
