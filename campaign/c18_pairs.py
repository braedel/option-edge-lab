"""Study 2 / E3 - market-neutral pairs / stat-arb (the last high-Sharpe candidate testable on free data).
Pre-specified economically-related ETF pairs; standard log-ratio z-score reversion (no tuning); OOS split;
heavy pairs costs (5/10 bps/leg). Market-neutral -> could in principle be high-Sharpe + low-DD + win-most-months.
Honest prior: classic pairs alpha largely decayed post-2010 + cost-heavy. Measure and report straight.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

sys.path.insert(0, r"D:\workspace\options-edge-lab\campaign")
from c5_tsmom import load  # noqa: E402

PAIRS = [("GLD", "SLV"), ("IEF", "TLT"), ("LQD", "HYG"), ("SPY", "QQQ"),
         ("EEM", "EFA"), ("IWM", "SPY"), ("SHY", "IEF"), ("USO", "DBC")]
LB, ENTRY, EXIT = 60, 2.0, 0.5

tickers = sorted({t for p in PAIRS for t in p})
px = pd.DataFrame({t: load(t) for t in tickers}).sort_index().dropna(how="all")
lp = np.log(px)
ret = px.pct_change()


def pair_pnl(a, b, cost):
    s = lp[a] - lp[b]
    z = (s - s.rolling(LB).mean()) / s.rolling(LB).std()
    pos = pd.Series(np.nan, index=z.index)
    pos[z > ENTRY] = -1.0
    pos[z < -ENTRY] = 1.0
    pos[z.abs() < EXIT] = 0.0
    pos = pos.ffill().fillna(0.0).shift(1)
    gross = pos * (ret[a] - ret[b])          # long spread = long a / short b
    tc = cost * pos.diff().abs() * 2          # two legs
    return (gross - tc)


def vt(r, target=0.10, win=60, cap=3.0):
    return r * (target / (r.rolling(win).std() * np.sqrt(252))).clip(upper=cap).shift(1)


def S(r):
    r = r.dropna()
    return float(r.mean() / r.std() * np.sqrt(252)) if len(r) > 50 and r.std() else np.nan


def MDD(r):
    e = (1 + r.dropna()).cumprod()
    return float((e / e.cummax() - 1).min() * 100)


def posmo(r):
    m = (1 + r).resample("ME").prod() - 1
    return float((m > 0).mean() * 100), (m <= 0).sum() / (len(r) / 252)


def portfolio(cost):
    pnls = pd.DataFrame({f"{a}-{b}": vt(pair_pnl(a, b, cost)) for a, b in PAIRS})
    return vt(pnls.mean(axis=1)).dropna(), pnls


print(f"period {px.index.min().date()} .. {px.index.max().date()}  pairs={len(PAIRS)}")
port, pnls = portfolio(0.0005)
y = port.index.year
print("\n=== per-pair Sharpe (5bps/leg) ===")
print("  " + "  ".join(f"{c}:{S(pnls[c]):.2f}" for c in pnls.columns))
pm, lyr = posmo(port)
print("\n=== PAIRS PORTFOLIO vs goal (Sharpe>2, win most months, low DD) ===")
print(f"  Sharpe={S(port):.2f}  OOS>=2016={S(port[y>=2016]):.2f}  maxDD={MDD(port):.1f}%  posMonths={pm:.0f}%  losing/yr={lyr:.1f}")
print("\n=== cost sensitivity (bps/leg) ===")
for c in (0.0002, 0.0005, 0.0010):
    p, _ = portfolio(c)
    print(f"  {c*1e4:4.0f}bps/leg: Sharpe={S(p):.2f}  OOS={S(p[p.index.year>=2016]):.2f}  maxDD={MDD(p):.1f}%")
