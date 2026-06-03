"""Candidate #5 - diversified time-series momentum / trend-following (free Yahoo ETF universe).

The most robustly OOS-documented strategy class (Hurst-Ooi-Pedersen, a century of evidence): crisis-alpha,
low equity correlation. Textbook, PRE-REGISTERED params (no tuning): 12-month (252d) momentum sign,
inverse-vol sizing to 10% per instrument, monthly rebalance, ~2bps/rebalance cost. Universe spans
equities/bonds/commodities/gold/FX. The bar: Sharpe, maxDD, LOW SPY correlation, and positive/diversifying
returns in equity-bear years (2008/2020/2022) -> beats buy-and-hold on a risk-adjusted/diversifying basis.
"""
from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pandas as pd

DIR = r"D:\workspace\options-edge-lab\campaign\data"
TICKERS = ["SPY", "EFA", "EEM", "TLT", "IEF", "GLD", "DBC", "UUP"]
TARGET, LOOKBACK, VOLWIN, COST = 0.10, 252, 60, 0.0002


def load(t: str) -> pd.Series:
    j = json.load(open(f"{DIR}\\tsmom_{t}.json", encoding="utf-8"))
    res = j["chart"]["result"][0]
    ind = res["indicators"]
    px = ind["adjclose"][0]["adjclose"] if "adjclose" in ind else ind["quote"][0]["close"]
    d = pd.DataFrame({"date": [dt.datetime.fromtimestamp(x, dt.UTC).date() for x in res["timestamp"]], "px": px})
    d = d.dropna().drop_duplicates("date")
    d["date"] = pd.to_datetime(d["date"])
    return d.set_index("date")["px"]


def stats(ret: pd.Series, label: str) -> str:
    ret = ret.dropna()
    if len(ret) < 50 or ret.std() == 0:
        return f"{label}: n={len(ret)} insufficient"
    eq = (1 + ret).cumprod()
    cagr = eq.iloc[-1] ** (252 / len(ret)) - 1
    sharpe = ret.mean() / ret.std() * np.sqrt(252)
    dd = (eq / eq.cummax() - 1).min()
    return f"{label}: CAGR={cagr*100:5.1f}% vol={ret.std()*np.sqrt(252)*100:4.1f}% Sharpe={sharpe:5.2f} maxDD={dd*100:6.1f}%"


def build_port(px, ret, me_days, lookbacks=(LOOKBACK,), cost=COST) -> pd.Series:
    vol = ret.rolling(VOLWIN).std() * np.sqrt(252)
    sig = sum(np.sign(px / px.shift(lb) - 1) for lb in lookbacks) / len(lookbacks)
    desired = sig * (TARGET / vol)
    held = desired.loc[desired.index.isin(me_days)].reindex(ret.index, method="ffill").shift(1)
    return ((held * ret).mean(axis=1) - (cost * held.diff().abs()).mean(axis=1)).dropna()


def scale10(x: pd.Series) -> pd.Series:
    return x * (0.10 / (x.std() * np.sqrt(252)))


def sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std() * np.sqrt(252))


def main() -> None:
    px = pd.DataFrame({t: load(t) for t in TICKERS}).sort_index().dropna(how="all")
    ret = px.pct_change()
    print(f"universe {list(px.columns)}  {px.index.min().date()}..{px.index.max().date()} n={len(px)}")

    me_days = pd.DatetimeIndex(sorted(ret.index.to_series().groupby([ret.index.year, ret.index.month]).last().values))
    port = build_port(px, ret, me_days)

    spy = ret["SPY"].reindex(port.index)
    six040 = (0.6 * ret["SPY"] + 0.4 * ret["IEF"]).reindex(port.index)
    print("\n=== diversified TSMOM vs benchmarks (full sample) ===")
    print(" ", stats(port, "TSMOM   "))
    print(" ", stats(spy, "SPY b&h "))
    print(" ", stats(six040, "60/40   "))
    print(f"  corr(TSMOM, SPY) = {port.corr(spy):.2f}   (low = diversifying)")

    print("\n=== sealed split (no params fit; textbook) DEV <=2015 | OOS >=2016 ===")
    y = port.index.year
    print(" ", stats(port[y <= 2015], "TSMOM DEV"))
    print(" ", stats(port[y >= 2016], "TSMOM OOS"))
    print(" ", stats(spy[y >= 2016], "SPY   OOS"))

    print("\n=== CRISIS-ALPHA test: calendar return % in equity-bear years ===")
    pyr = port.groupby(y).apply(lambda r: (1 + r).prod() - 1) * 100
    syr = spy.groupby(spy.index.year).apply(lambda r: (1 + r).prod() - 1) * 100
    for yr in [2008, 2011, 2015, 2018, 2020, 2022, 2023, 2024, 2025, 2026]:
        if yr in pyr.index:
            print(f"  {yr}: TSMOM {pyr[yr]:+6.1f}%   SPY {syr.get(yr, float('nan')):+6.1f}%")

    def mdd(r):
        e = (1 + r.dropna()).cumprod()
        return (e / e.cummax() - 1).min() * 100

    print("\n=== does adding TSMOM improve a real portfolio? (equal-risk blends @ 10% vol) ===")
    combos = {
        "SPY only": scale10(spy),
        "60/40 only": scale10(six040),
        "50% SPY + 50% TSMOM": 0.5 * scale10(spy) + 0.5 * scale10(port.reindex(spy.index)),
        "50% 60/40 + 50% TSMOM": 0.5 * scale10(six040) + 0.5 * scale10(port.reindex(six040.index)),
    }
    for lab, r in combos.items():
        r = r.dropna()
        yo = r.index.year
        print(f"  {lab:24s} FULL Sharpe={sharpe(r):.2f} maxDD={mdd(r):6.1f}% | OOS>=2016 Sharpe={sharpe(r[yo >= 2016]):.2f}")

    print("\n=== robustness (TSMOM standalone Sharpe) ===")
    blend = build_port(px, ret, me_days, lookbacks=(21, 63, 126, 252))
    print(f"  12m-only:        full {sharpe(port):.2f}  OOS {sharpe(port[port.index.year >= 2016]):.2f}")
    print(f"  1/3/6/12m blend: full {sharpe(blend):.2f}  OOS {sharpe(blend[blend.index.year >= 2016]):.2f}")
    for c in (0.0005, 0.0010):
        p = build_port(px, ret, me_days, cost=c)
        print(f"  cost {c*1e4:.0f}bps/rebal: full Sharpe={sharpe(p):.2f}  CAGR={((1 + p).prod() ** (252 / len(p)) - 1) * 100:.1f}%")


if __name__ == "__main__":
    main()
