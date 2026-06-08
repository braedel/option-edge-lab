# Study 2 — High-Sharpe target (Sharpe > 2, win most months, low DD, &le; $15k)

**Goal (owner /goal, 2026-06-08):** a tradeable strategy (options / futures / securities) with **Sharpe > 2**,
**profitable most months** (give up no more than ~2/yr), **reasonably low drawdown**, runnable on **&le; $15k**.

## Deflated prior (read first — Study-1 discipline applies)
- A **robust** Sharpe > 2 (cost-real, leak-free, tail-included, out-of-sample) is *extraordinarily rare* for
  retail. Study 1's audited trend overlay was **~0.9–1.0**.
- The goal's **profile** (very high Sharpe + win-almost-every-month + low DD + small capital) is the textbook
  signature of **option-premium selling / short-volatility** — whose lovely Sharpe and rare losses **hide a
  catastrophic tail** (2018 "volmageddon", 2020). "Low DD" is an illusion until the tail fires. This is the
  #1 way retail backtests fool themselves.
- **Hard evidence already in hand:** the *tradeable* realization of premium-selling, the **PUTW** ETF, ran
  **Sharpe ~0.68 / 0.77-OOS** (Study-1 `c4`) — nowhere near 2. The ">2" for option-selling lives only in
  tail-blind models/sub-periods.
- **Data constraint:** no option-price data, **no data spend** &rarr; options strategies cannot be rigorously
  backtested here (only modeled, which we don't trust). Testable space = **free price data** (ETFs, futures, vol ETPs).
- **Honest expectation:** the *verified* achievable Sharpe is likely **~1–1.5**; a credible >2 would need option
  data (untestable here) or overfitting. **No fabricated >2** — every figure gets the leak-free / cost-real /
  tail-inclusive / OOS / independent-audit treatment from Study 1.

## Plan (pursue hard, report only verified)
1. **Best honest diversified ensemble** — stack genuinely-uncorrelated sleeves (trend + short-term reversal +
   cross-sectional momentum + defensive), vol-targeted, leak-free, cost-real. Measure Sharpe, % positive months,
   maxDD, OOS. (The legitimate Sharpe-stacking path: combined &asymp; sleeve_Sharpe &times; &radic;N_uncorrelated.)
2. **Profile-match honesty check** — quantify what short-vol / premium-selling *would* look like vs the tail it
   carries, to show why the requested profile is a trap on real instruments.
3. If anything genuinely clears the bar with low DD, OOS, costs, and an independent audit &rarr; lock it.
   Otherwise: report the honest ceiling and exactly what would be required to attempt >2 credibly.

## Trial log
- (pending) E1: diversified L/S ensemble (trend + reversal + xsec), vol-targeted, leak-free, cost-stressed.
