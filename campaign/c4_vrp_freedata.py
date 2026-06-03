"""Candidate #4 - VRP harvest via FREE tradeable-instrument data (no paid pull).

PUTW = systematic SPX put-write ETF (the VRP harvest, tradeable). Test the realized track record vs SPY
buy-and-hold (Sharpe, maxDD, tails), a sealed OOS (dev<2022 / oos>=2022), the raw VRP (VIX vs forward
realized vol), and whether a pre-registered VIX-conditioning overlay (sell vol only when VIX is elevated)
lifts risk-adjusted return out-of-sample -- i.e. edge vs beta.
"""
from __future__ import annotations

import datetime as dt
import json

import numpy as np
import pandas as pd

DIR = r"D:\workspace\options-edge-lab\campaign\data"


def load_yahoo(name: str, use_adj: bool = True) -> pd.DataFrame:
    with open(f"{DIR}\\{name}.json", encoding="utf-8") as f:
        j = json.load(f)
    res = j["chart"]["result"][0]
    ts = res["timestamp"]
    ind = res["indicators"]
    px = ind["adjclose"][0]["adjclose"] if (use_adj and "adjclose" in ind) else ind["quote"][0]["close"]
    d = pd.DataFrame({"date": [dt.datetime.fromtimestamp(t, dt.UTC).date() for t in ts], "px": px})
    d = d.dropna().drop_duplicates("date")
    d["date"] = pd.to_datetime(d["date"])
    return d.sort_values("date").reset_index(drop=True)


def stats(ret: pd.Series) -> str:
    ret = ret.dropna()
    if len(ret) < 20 or ret.std() == 0:
        return f"n={len(ret)} (insufficient)"
    eq = (1 + ret).cumprod()
    cagr = eq.iloc[-1] ** (252 / len(ret)) - 1
    sharpe = ret.mean() / ret.std() * np.sqrt(252)
    dd = (eq / eq.cummax() - 1).min()
    t = ret.mean() / (ret.std() / np.sqrt(len(ret)))
    return f"n={len(ret)} CAGR={cagr*100:5.1f}% vol={ret.std()*np.sqrt(252)*100:4.1f}% Sharpe={sharpe:5.2f} maxDD={dd*100:6.1f}% t={t:4.2f}"


def main() -> None:
    s = {nm: load_yahoo(nm, adj) for nm, adj in [("vix", False), ("putw", True), ("spy", True), ("svxy", True)]}
    for nm, d in s.items():
        print(f"{nm}: n={len(d)} {d['date'].min().date()}..{d['date'].max().date()}")
    px = pd.DataFrame({nm: d.set_index("date")["px"] for nm, d in s.items()}).sort_index()
    ret = px.pct_change()
    yr = ret.index.year

    print("\n=== tradeable track records ===")
    for c in ["putw", "spy", "svxy"]:
        print(f"  {c.upper():5s} FULL  {stats(ret[c])}")
    print("\n=== sealed OOS (DEV <2022 | OOS >=2022) ===")
    for c in ["putw", "spy", "svxy"]:
        print(f"  {c.upper():5s} DEV   {stats(ret.loc[yr < 2022, c])}")
        print(f"  {c.upper():5s} OOS   {stats(ret.loc[yr >= 2022, c])}")
    print("\n=== PUTW calendar-year returns % ===")
    print("  ", {int(k): round(v * 100, 1) for k, v in ret.groupby(yr)["putw"].apply(lambda r: (1 + r).prod() - 1).items()})

    # raw VRP: VIX (implied %) vs forward-21d realized vol of SPY (annualized %)
    rv_fwd = ret["spy"].rolling(21).std().shift(-21) * np.sqrt(252) * 100
    vrp = (px["vix"] - rv_fwd).dropna()
    print(f"\n=== raw VRP (VIX - forward21d RV): mean={vrp.mean():.2f} median={vrp.median():.2f} "
          f"%positive={(vrp > 0).mean()*100:.1f} n={len(vrp)} ===")

    # pre-registered conditioning: hold PUTW only when prior-day VIX > trailing-252 median (elevated regime)
    elevated = px["vix"].shift(1) > px["vix"].shift(1).rolling(252, min_periods=120).median()
    cond = ret["putw"].where(elevated, 0.0)
    print("\n=== VIX-conditioned PUTW (hold only when prior VIX > trailing-252 median) vs always ===")
    for lab, m in [("DEV <2022", yr < 2022), ("OOS >=2022", yr >= 2022)]:
        print(f"  {lab}")
        print(f"     always PUTW   {stats(ret.loc[m, 'putw'])}")
        print(f"     conditioned   {stats(cond.loc[m])}  (in-market {elevated.loc[m].mean()*100:.0f}% of days)")
        print(f"     SPY benchmark {stats(ret.loc[m, 'spy'])}")


if __name__ == "__main__":
    main()
