"""#3 cheap-first ILLUSTRATION (NOT a priced backtest): does wrapping the surprise edge in a DEFINED-RISK
debit spread improve drawdown/reliability enough to justify buying OZB option data?

Takes the actual big-surprise FUTURES per-event P&L (reports/zb_surprise/per_event.csv) and overlays a
debit-spread payoff in the SAME (surprise) direction: pnl_spread = clip(favorable_move, 0, W) - D ticks.
This CAPS the loss at the debit D (a wrong big surprise can't blow you up) and caps the gain at W-D.

HONEST CAVEATS (why this only motivates the data spend, not concludes): (1) expiry-INTRINSIC payoff -- at a
60-min hold the option is not at expiry, so real marks are smoother (less extreme both ways); (2) the debit D
and width W depend on IV, which is unobservable without OZB data; values here are plausible placeholders.
The ONE thing it shows reliably: the SHAPE benefit -- capping the left tail. Run after c43 (reads its CSV).
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DOLLAR = 31.25
FUT_COST_T = 1.0 + 4.0 / 31.25          # cost embedded in the futures net (to back out the gross move)
CSV = Path("reports/zb_surprise/per_event.csv")
# (label, width ticks, debit ticks) -- plausible ATM-ish debit spreads; real D needs OZB IV
CONFIGS = [("spread W6/D2.5", 6, 2.5), ("spread W10/D4", 10, 4.0), ("spread W4/D1.8", 4, 1.8)]


def stats(pnl_dollars, dates):
    v = np.asarray(pnl_dollars, float)
    eq = np.cumsum(v); dd = eq - np.maximum.accumulate(eq)
    yrs = (dates[-1] - dates[0]).days / 365.25
    sharpe = v.mean() / v.std(ddof=1) * np.sqrt(len(v) / yrs) if v.std() else float("nan")
    return dict(total=eq[-1], mean=v.mean(), pos=np.mean(v > 0), sharpe=sharpe,
                maxdd=-dd.min(), worst=v.min(), eq=eq, dd=dd)


def main():
    import datetime as dt
    rows = list(csv.DictReader(open(CSV)))
    dates = [dt.date.fromisoformat(r["date"]) for r in rows]
    fut = np.array([float(r["net_dollars"]) for r in rows])           # futures net $ per event
    move = fut / DOLLAR + FUT_COST_T                                  # favorable move in ticks (signed)

    print(f"=== #3 defined-risk OVERLAY (illustrative; n={len(rows)} big-surprise events) ===")
    sN = stats(fut, dates)
    print(f"NAKED futures : total=${sN['total']:+.0f} mean=${sN['mean']:+.0f} %pos={sN['pos']:.2f} "
          f"Sharpe~{sN['sharpe']:+.2f} maxDD=${sN['maxdd']:,.0f} worst1=${sN['worst']:+.0f}")
    overlays = {}
    for label, W, D in CONFIGS:
        spread_t = np.clip(move, 0, W) - D                            # debit-spread payoff (ticks), capped both ways
        s = stats(spread_t * DOLLAR, dates)
        overlays[label] = s
        print(f"{label:16s}: total=${s['total']:+.0f} mean=${s['mean']:+.0f} %pos={s['pos']:.2f} "
              f"Sharpe~{s['sharpe']:+.2f} maxDD=${s['maxdd']:,.0f} worst1=${s['worst']:+.0f} "
              f"(loss capped at -${D*DOLLAR:.0f})")

    # single long options: uncapped upside (preserves winner-driven edge), loss = premium
    print("\nSingle long options (uncapped upside, loss capped at premium; intrinsic-optimistic):")
    for label, O, P in [("ATM P5", 0, 5), ("ATM P8", 0, 8), ("ATM P12", 0, 12),
                        ("OTM O5/P2.5", 5, 2.5), ("OTM O8/P1.5", 8, 1.5)]:
        opt = np.maximum(move - O, 0) - P                            # long option in surprise dir
        s = stats(opt * DOLLAR, dates)
        overlays[label] = s
        print(f"  {label:12s}: total=${s['total']:+.0f} mean=${s['mean']:+.0f} %pos={s['pos']:.2f} "
              f"Sharpe~{s['sharpe']:+.2f} maxDD=${s['maxdd']:,.0f} worst1=${s['worst']:+.0f}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), height_ratios=[3, 1], sharex=True)
    fig.suptitle("#3 defined-risk overlay on the surprise edge  —  ILLUSTRATIVE (needs OZB data to price)",
                 fontsize=12, weight="bold")
    ax1.plot(dates, sN["eq"], "-o", ms=3, lw=2, color="black", label="NAKED futures")
    for label, s in overlays.items():
        ax1.plot(dates, s["eq"], "-", lw=1.3, alpha=0.85, label=label)
    ax1.axhline(0, color="grey", lw=0.7); ax1.set_ylabel("cumulative P&L ($)"); ax1.legend(fontsize=8, loc="upper left")
    ax2.plot(dates, sN["dd"], color="black", lw=1.2, label="naked DD")
    for label, s in overlays.items():
        ax2.plot(dates, s["dd"], lw=1.0, alpha=0.8, label=label)
    ax2.set_ylabel("drawdown ($)"); ax2.axhline(0, color="grey", lw=0.7); ax2.legend(fontsize=7, ncol=4)
    fig.text(0.5, 0.005, "Illustrative payoff-shape overlay (expiry-intrinsic; debit/width are IV placeholders). "
             "Shows tail-capping; real pricing needs OZB option quotes.", ha="center", fontsize=8, style="italic", color="#777")
    out = Path("reports/zb_surprise"); fig.tight_layout(rect=[0, 0.02, 1, 0.97])
    fig.savefig(out / "defined_risk_overlay.png", dpi=130)
    print(f"-> wrote {out/'defined_risk_overlay.png'}")
    print("[If a defined-risk wrap materially cuts maxDD/worst-trade at acceptable total -> worth buying OZB "
          "data to price it for real. If it just bleeds premium -> skip the options spend.]")


if __name__ == "__main__":
    main()
