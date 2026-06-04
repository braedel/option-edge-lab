"""C12 - independently verify the QUANT-AUDIT findings (do not trust the subagent's numbers).
Checks: (1) cost on ACTUAL levered turnover vs the pre-leverage charge; (2) DEPLOY return vs 60/40;
(3) Sharpe standard error + block-bootstrap significance vs 60/40; (4) SHY/illiquid universe dependence.
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
ALL = pd.DataFrame({t: load(t) for t in U}).sort_index().dropna(how="all")


def S(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(252))


def CAGR(r):
    r = r.dropna()
    return float((1 + r).prod() ** (252 / len(r)) - 1) * 100


def MDD(r):
    e = (1 + r.dropna()).cumprod()
    return float((e / e.cummax() - 1).min() * 100)


def build(cost, proper, borrow=0.0, names=U):
    px = ALL[names]
    ret = px.pct_change()
    me = pd.DatetimeIndex(sorted(ret.index.to_series().groupby([ret.index.year, ret.index.month]).last().values))
    vol = ret.rolling(V).std() * np.sqrt(252)
    sig = sum(np.sign(px / px.shift(lb) - 1) for lb in (21, 63, 126, 252)) / 4
    held = (sig * (T / vol)).loc[me].reindex(ret.index, method="ffill").shift(1)
    base = (held * ret).mean(axis=1) - 0.0002 * held.diff().abs().mean(axis=1)
    scale = (T / (base.rolling(V).std() * np.sqrt(252))).clip(upper=3).shift(1)
    pos = held.mul(scale, axis=0)                       # ACTUAL levered position per name
    gross = (pos * ret).mean(axis=1)
    if proper:
        tc = cost * pos.diff().abs().mean(axis=1)        # cost on actual (levered, daily) turnover
        bc = (borrow / 252) * pos.clip(upper=0).abs().mean(axis=1)
    else:
        tc = scale * cost * held.diff().abs().mean(axis=1)  # the ORIGINAL pre-leverage monthly charge
        bc = (borrow / 252) * scale * held.clip(upper=0).abs().mean(axis=1)
    sleeve = (gross - tc - bc).dropna()
    p = 0.6 * ret["SPY"] + 0.4 * ret["IEF"]
    idx = sleeve.index.intersection(p.dropna().index)
    return (0.5 * sleeve.reindex(idx) + 0.5 * p.reindex(idx)).dropna(), p.reindex(idx).dropna()


print("[1] COST: original (pre-leverage monthly) vs proper (actual levered daily turnover)")
for c in (0.0002, 0.0005, 0.0010):
    do, _ = build(c, proper=False)
    dp, _ = build(c, proper=True)
    print(f"   {c*1e4:4.0f}bps: original Sharpe {S(do):.2f}  |  PROPER Sharpe {S(dp):.2f}")
# avg leverage
d0, p60 = build(0.0002, proper=True)
print(f"   (avg vol-target leverage shown separately below)")

print("\n[2] RETURN vs 60/40 (is the Sharpe edge real return, or just lower vol?)")
idx = d0.index
p = p60.reindex(idx)
print(f"   DEPLOY : CAGR {CAGR(d0):.2f}%  vol {d0.std()*np.sqrt(252)*100:.1f}%  Sharpe {S(d0):.2f}  maxDD {MDD(d0):.1f}%")
print(f"   60/40  : CAGR {CAGR(p):.2f}%  vol {p.std()*np.sqrt(252)*100:.1f}%  Sharpe {S(p):.2f}  maxDD {MDD(p):.1f}%")
print(f"   -> DEPLOY return minus 60/40 return = {CAGR(d0)-CAGR(p):+.2f}%/yr")

print("\n[3] SIGNIFICANCE: Sharpe SE + block-bootstrap of Sharpe(DEPLOY) - Sharpe(60/40)")
n_yr = len(d0) / 252
se = np.sqrt((1 + 0.5 * S(d0) ** 2) / n_yr)
print(f"   analytic SE(Sharpe) ~ {se:.2f}  -> DEPLOY Sharpe 95% CI ~ [{S(d0)-1.96*se:.2f}, {S(d0)+1.96*se:.2f}]")
rng = np.random.default_rng(0)
a, b = d0.values, p.values
nb, blk, n = 3000, 21, len(d0)
diffs = np.empty(nb)
for k in range(nb):
    starts = rng.integers(0, n - blk, size=n // blk + 1)
    bi = np.concatenate([np.arange(s, s + blk) for s in starts])[:n]
    aa, bb = a[bi], b[bi]
    diffs[k] = aa.mean() / aa.std() * np.sqrt(252) - bb.mean() / bb.std() * np.sqrt(252)
lo, mid, hi = np.percentile(diffs, [2.5, 50, 97.5])
print(f"   bootstrap Sharpe(DEPLOY)-Sharpe(60/40): median {mid:+.2f}  95% CI [{lo:+.2f}, {hi:+.2f}]  P(>0)={np.mean(diffs>0):.2f}")

print("\n[4] UNIVERSE dependence (proper cost 2bps, 1% borrow):")
for lbl, names in [("all 21", U),
                   ("drop SHY", [x for x in U if x != "SHY"]),
                   ("drop illiquid (UNG,USO,DBA,FXE,FXY,SHY,TIP)", [x for x in U if x not in ("UNG", "USO", "DBA", "FXE", "FXY", "SHY", "TIP")]),
                   ("liquid core 11", ["SPY", "QQQ", "IWM", "EFA", "EEM", "IEF", "TLT", "LQD", "HYG", "GLD", "SLV"])]:
    dd, _ = build(0.0002, proper=True, borrow=0.01, names=names)
    yy = dd.index.year
    print(f"   {lbl:46s}: Sharpe {S(dd):.2f}  OOS>=2016 {S(dd[yy>=2016]):.2f}  maxDD {MDD(dd):.1f}%")
