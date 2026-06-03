"""Candidate #2 - overnight drift (close-to-open) vs intraday (open-to-close) in ES/NQ.

Documented anomaly: most of the equity premium accrues overnight; the RTH session is ~flat/negative.
Low-turnover, cost-tolerant. Test on the back-adjusted volume-roll (roll-safe), exclude roll days,
report overnight vs intraday by year, then a sealed-OOS (DEV <2024 / OOS >=2024) long-overnight
strategy net of realistic round-turn cost with t-stats.
"""
from __future__ import annotations

import datetime as dt
import sys

import numpy as np
import pandas as pd

DAT = r"D:\workspace\dat-trading-strategy-research"
sys.path.insert(0, DAT + r"\src")
from dat_strategy_research.ohlcv import INSTRUMENT_SPECS, read_ohlcv  # noqa: E402

VR = DAT + r"\data\processed\databento\es_nq_volume_roll_1m\{}_volume_roll_backadjusted_1m.parquet"
TZ = "America/New_York"
RTH_OPEN, RTH_CLOSE = dt.time(9, 30), dt.time(16, 0)


def daily_rth(df: pd.DataFrame) -> pd.DataFrame:
    lt = df["timestamp"].dt.tz_convert(TZ)
    work = df.assign(d=lt.dt.date, t=lt.dt.time)
    rth = work[(work["t"] >= RTH_OPEN) & (work["t"] <= RTH_CLOSE)]
    g = rth.groupby("d")
    out = pd.DataFrame({
        "rth_open": g["open"].first(), "rth_close": g["close"].last(),
        "inst_open": g["instrument_id"].first(), "inst_close": g["instrument_id"].last(),
    }).reset_index().sort_values("d").reset_index(drop=True)
    return out


def tstat(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))) if len(x) > 2 and x.std() else float("nan")


def sharpe(x: pd.Series) -> float:
    x = x.dropna()
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252)) if len(x) > 2 and x.std() else float("nan")


def main() -> None:
    for sym in ("ES", "NQ"):
        df = read_ohlcv(VR.format(sym))
        daily = daily_rth(df)
        daily["prev_close"] = daily["rth_close"].shift(1)
        daily["prev_inst"] = daily["inst_close"].shift(1)
        daily["overnight_pts"] = daily["rth_open"] - daily["prev_close"]
        daily["intraday_pts"] = daily["rth_close"] - daily["rth_open"]
        daily["roll"] = daily["inst_open"] != daily["prev_inst"]
        d = daily.dropna(subset=["overnight_pts", "intraday_pts"]).copy()
        d = d[~d["roll"]].copy()  # exclude cross-contract overnight
        d["year"] = pd.to_datetime(d["d"]).dt.year
        pv = INSTRUMENT_SPECS[sym].point_value
        print(f"\n===== {sym} (point_value ${pv}); n={len(d)} sessions {d['d'].min()}..{d['d'].max()} =====")
        print(" year |  n  | ON mean_pt  ON $tot  ON shrp | ID mean_pt  ID $tot  ID shrp")
        for y, g in d.groupby("year"):
            on, idr = g["overnight_pts"], g["intraday_pts"]
            print(f" {y} | {len(g):3d} | {on.mean():+8.3f}  {on.sum()*pv:+8.0f}  {sharpe(on):+5.2f} | "
                  f"{idr.mean():+8.3f}  {idr.sum()*pv:+8.0f}  {sharpe(idr):+5.2f}")
        print(" -- long-overnight strategy (enter prior RTH close, exit RTH open), net of cost --")
        for lab, mask in [("DEV  <2024", d["year"] < 2024), ("OOS >=2024", d["year"] >= 2024)]:
            g = d[mask]
            for cost_rt in (2.0, 4.0):
                net = g["overnight_pts"] * pv - cost_rt
                print(f"   {lab} @ ${cost_rt:.0f}/RT: n={len(g)} net=${net.sum():+,.0f} "
                      f"per=${net.mean():+.2f} sharpe={sharpe(net):+.2f} t={tstat(net):+.2f}")


if __name__ == "__main__":
    main()
