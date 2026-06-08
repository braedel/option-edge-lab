"""Study 2 / E1 - diversified L/S ensemble (leak-free, cost-real). Trend + short-term reversal +
cross-sectional momentum on 21 ETFs. Each sleeve vol-targeted ex-ante to 10%; equal-weight combine;
vol-target the ensemble. Report Sharpe, % positive MONTHS, maxDD, OOS>=2016, at cost 2/5/10 bps.
Honest baseline vs the Sharpe>2 / win-most-months / low-DD goal. No look-ahead (perturbation-checked).
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


def rebals(ret, freq):
    g = ret.index.to_series()
    if freq == "M":
        key = [ret.index.year, ret.index.month]
    else:  # weekly (ISO year-week)
        iso = ret.index.isocalendar()
        key = [iso.year.values, iso.week.values]
    return pd.DatetimeIndex(sorted(g.groupby(key).last().values))


def build_ensemble(px, cost=0.0002):
    ret = px.pct_change()
    me, we = rebals(ret, "M"), rebals(ret, "W")
    vol = ret.rolling(V).std() * np.sqrt(252)

    def vt(r):
        return r * (T / (r.rolling(V).std() * np.sqrt(252))).clip(upper=3).shift(1)

    def sleeve(desired, rebal):
        held = desired.loc[desired.index.isin(rebal)].reindex(ret.index, method="ffill").shift(1)
        return vt((held * ret).mean(axis=1) - cost * held.diff().abs().mean(axis=1))

    tsig = sum(np.sign(px / px.shift(lb) - 1) for lb in (21, 63, 126, 252)) / 4
    trend = sleeve(tsig * (T / vol), me)

    r5 = px / px.shift(5) - 1
    rr = r5.rank(axis=1)
    rsig = -(rr.sub(rr.mean(axis=1), axis=0))
    rsig = rsig.div(rsig.abs().sum(axis=1), axis=0)
    rev = sleeve(rsig, we)

    r12 = px / px.shift(252) - 1
    xr = r12.rank(axis=1)
    xsig = xr.sub(xr.mean(axis=1), axis=0)
    xsig = xsig.div(xsig.abs().sum(axis=1), axis=0)
    xsec = sleeve(xsig, me)

    sleeves = pd.DataFrame({"trend": trend, "reversal": rev, "xsec": xsec})
    ens = vt(sleeves.mean(axis=1)).dropna()
    return ens, sleeves


def S(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(252)) if len(r) > 50 and r.std() else np.nan


def MDD(r):
    e = (1 + r.dropna()).cumprod()
    return float((e / e.cummax() - 1).min() * 100)


def pos_months(r):
    m = (1 + r).resample("ME").prod() - 1
    return float((m > 0).mean() * 100), int((m <= 0).sum()), len(m)


ens, sleeves = build_ensemble(PX)
y = ens.index.year
print(f"period {ens.index.min().date()} .. {ens.index.max().date()}")
print("\n=== individual sleeves (leak-free, 2bps) ===")
for c in sleeves.columns:
    print(f"  {c:9s} Sharpe={S(sleeves[c]):5.2f}  maxDD={MDD(sleeves[c]):6.1f}%")
print(f"  corr matrix:\n{sleeves.corr().round(2).to_string()}")

pm, neg, nm = pos_months(ens)
print("\n=== ENSEMBLE (vs goal: Sharpe>2, win most months, low DD) ===")
print(f"  Sharpe={S(ens):.2f}  OOS>=2016={S(ens[y>=2016]):.2f}  maxDD={MDD(ens):.1f}%  vol={ens.std()*np.sqrt(252)*100:.1f}%")
print(f"  positive months={pm:.0f}%  ({neg} losing of {nm}; ~{neg/(nm/ (len(ens)/252)):.1f}/yr)")

print("\n=== cost sensitivity ===")
for c in (0.0002, 0.0005, 0.0010):
    e, _ = build_ensemble(PX, c)
    print(f"  {c*1e4:4.0f}bps: Sharpe={S(e):.2f}  maxDD={MDD(e):.1f}%")

# leak-free perturbation check
base, _ = build_ensemble(PX)
px2 = PX.copy(); px2.iloc[-8:] = px2.iloc[-8:] * 5
pert, _ = build_ensemble(px2)
cut = PX.index[-15]
pre = base.index[base.index < cut]
print(f"\nlook-ahead audit (must be 0): {(base.reindex(pre)-pert.reindex(pre)).abs().max():.2e}")
