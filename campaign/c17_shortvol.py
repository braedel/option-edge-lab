"""Study 2 / E2 - the profile-match: short-vol / premium-selling (the ONLY thing whose shape fits
Sharpe>2 + win-most-months + low-DD). Test naive short-vol (SVXY), a REGIME-FILTERED + risk-managed
version (the genuine best shot at the goal), and PUTW (put-write). Show win-rate vs the tail.
Data: free Yahoo (SVXY/VIX/SPY/PUTW, 2016+, includes Feb-2018 + Mar-2020). Honest about ETF limits.
"""
from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pandas as pd

DIR = r"D:\workspace\options-edge-lab\campaign\data"


def load(name, use_adj=True):
    j = json.load(open(f"{DIR}\\{name}.json", encoding="utf-8"))
    res = j["chart"]["result"][0]
    ind = res["indicators"]
    px = ind["adjclose"][0]["adjclose"] if (use_adj and "adjclose" in ind) else ind["quote"][0]["close"]
    d = pd.DataFrame({"date": [dt.datetime.fromtimestamp(t, dt.UTC).date() for t in res["timestamp"]], "px": px})
    d = d.dropna().drop_duplicates("date")
    d["date"] = pd.to_datetime(d["date"])
    return d.sort_values("date").set_index("date")["px"]


svxy, vix, spy, putw = load("svxy"), load("vix", False), load("spy"), load("putw")
df = pd.DataFrame({"svxy": svxy, "vix": vix, "spy": spy, "putw": putw}).dropna(how="all").sort_index()
ret = df[["svxy", "spy", "putw"]].pct_change()
vix = df["vix"]


def stats(r, label):
    r = r.dropna()
    e = (1 + r).cumprod()
    mdd = (e / e.cummax() - 1).min() * 100
    m = (1 + r).resample("ME").prod() - 1
    sh = r.mean() / r.std() * np.sqrt(252) if r.std() else np.nan
    worst = m.min() * 100
    yrs = len(r) / 252
    return (f"  {label:34s} Sharpe={sh:5.2f}  maxDD={mdd:6.1f}%  posMonths={ (m>0).mean()*100:4.0f}%  "
            f"losing/yr={ (m<=0).sum()/yrs:4.1f}  worstMonth={worst:6.1f}%")


# naive long-short-vol (hold SVXY)
print(f"period {df.index.min().date()} .. {df.index.max().date()}  (SVXY/PUTW history is 2016+)")
print("\n=== the profile-match strategies ===")
print(stats(ret["svxy"], "Naive short-vol (hold SVXY)"))
print(stats(ret["putw"], "Put-write (PUTW)"))
print(stats(ret["spy"], "S&P 500 (benchmark)"))

# REGIME-FILTERED + risk-managed short-vol (the genuine best shot at low DD):
# hold SVXY only when calm: prior-day VIX below its trailing-252 median AND SPY above its 200d MA.
calm = ((vix.shift(1) < vix.shift(1).rolling(252, min_periods=60).median())
        & (df["spy"].shift(1) > df["spy"].shift(1).rolling(200).mean()))
filt = (ret["svxy"].where(calm, 0.0)).dropna()
print("\n=== risk-managed short-vol (only short vol in calm regime; flat otherwise) ===")
print(stats(filt, "Regime-filtered short-vol"))
print(f"  in-market {calm.reindex(filt.index).mean()*100:.0f}% of days")

# does the filter dodge the worst single days?
worst_days = ret["svxy"].nsmallest(6)
print("\n=== the tail: worst SVXY days & whether the calm-filter was OUT ===")
for d, v in worst_days.items():
    print(f"  {d.date()}  SVXY {v*100:+6.1f}%   filter_in_market={bool(calm.get(d, False))}")
