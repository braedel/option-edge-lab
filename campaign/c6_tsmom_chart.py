"""PnL + underwater tearsheet for the C5 diversified-TSMOM strategy (through latest data = today)."""
from __future__ import annotations

import sys

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, r"D:\workspace\options-edge-lab\campaign")
from c5_tsmom import TICKERS, build_port, load, sharpe  # noqa: E402

OUT = r"D:\workspace\options-edge-lab\reports\tsmom_pnl_underwater.png"


def mdd(e: pd.Series) -> float:
    return (e / e.cummax() - 1).min() * 100


def main() -> None:
    px = pd.DataFrame({t: load(t) for t in TICKERS}).sort_index().dropna(how="all")
    ret = px.pct_change()
    me = pd.DatetimeIndex(sorted(ret.index.to_series().groupby([ret.index.year, ret.index.month]).last().values))
    port = build_port(px, ret, me)
    df = pd.DataFrame({
        "TSMOM": port,
        "SPY": ret["SPY"],
        "60/40": 0.6 * ret["SPY"] + 0.4 * ret["IEF"],
    }).dropna()
    eq = (1 + df).cumprod()
    uw = eq / eq.cummax() - 1
    last = eq.index.max().date()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8.5), height_ratios=[2.4, 1], sharex=True)
    styles = {"TSMOM": ("#1f77b4", 2.0), "SPY": ("#999999", 1.1), "60/40": ("#2ca02c", 1.1)}
    for c, (col, lw) in styles.items():
        ax1.plot(eq.index, eq[c], color=col, lw=lw,
                 label=f"{c}: Sharpe {sharpe(df[c]):.2f}, maxDD {mdd(eq[c]):.0f}%")
    ax1.set_yscale("log")
    ax1.set_ylabel("Growth of $1 (log)")
    ax1.set_title(f"Diversified Time-Series Momentum — cumulative PnL & underwater  ({eq.index.min().date()} → {last})",
                  fontsize=13, fontweight="bold")
    ax1.legend(loc="upper left", framealpha=0.9)
    ax1.grid(True, which="both", alpha=0.25)
    for yr in (2008, 2020, 2022):
        ax1.axvspan(pd.Timestamp(yr, 1, 1), pd.Timestamp(yr, 12, 31), color="red", alpha=0.05)

    ax2.fill_between(uw.index, uw["TSMOM"] * 100, 0, color="#1f77b4", alpha=0.35)
    ax2.plot(uw.index, uw["TSMOM"] * 100, color="#1f77b4", lw=1.2, label="TSMOM")
    ax2.plot(uw.index, uw["SPY"] * 100, color="#999999", lw=0.9, label="SPY")
    ax2.set_ylabel("Drawdown %")
    ax2.set_title("Underwater (drawdown from running peak)", fontsize=11)
    ax2.legend(loc="lower left", framealpha=0.9)
    ax2.grid(True, alpha=0.25)
    ax2.xaxis.set_major_locator(mdates.YearLocator(2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    note = (f"TSMOM as built: 12m momentum, inverse-vol, monthly, ~{df['TSMOM'].std()*np.sqrt(252)*100:.0f}% vol, "
            f"net of ~2bps/rebalance. Crisis years shaded. Standalone is a diversifying hedge (modest carry); "
            f"its job is the shallow underwater, not beating SPY's return.")
    fig.text(0.012, 0.005, note, fontsize=8.5, color="0.35")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(OUT, dpi=130)
    print("saved:", OUT)
    print(f"period {eq.index.min().date()} -> {last};  TSMOM final x{eq['TSMOM'].iloc[-1]:.2f}, "
          f"maxDD {mdd(eq['TSMOM']):.1f}%, current DD {uw['TSMOM'].iloc[-1]*100:.1f}%")


if __name__ == "__main__":
    main()
