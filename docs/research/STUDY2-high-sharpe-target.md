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

## Results (E1–E3, leak-free, cost-real, 2026-06-08)
- **E1 — diversified L/S ensemble** (trend + reversal + xsec, 21 ETFs): Sharpe **0.74** (OOS 0.73), maxDD −17%,
  **61% positive months (~7 losing/yr)**. Reversal is *dead* (0.00), xsec weak (0.33) → stacking them *hurt* vs
  trend-alone (0.76). Look-ahead audit 0.00. `campaign/c16_ensemble.py`.
- **E2 — short-vol / premium-selling** (the only shape that matches the goal's profile): naive SVXY Sharpe 0.34 /
  **maxDD −95%**; PUTW 0.68 / −28% / 74% pos-months; regime-filtered (risk-managed) short-vol **0.27 / −36%**.
  The smooth "win-almost-every-month" shape is *paid for* by a catastrophic tail; managing the tail away
  collapses the Sharpe. `campaign/c17_shortvol.py`.
- **E3 — pairs / stat-arb** (8 economically-related ETF pairs, standard z-reversion, OOS, heavy cost): Sharpe
  **−0.47** (negative), −69% DD — classic pairs is dead / cost-eaten. `campaign/c18_pairs.py`.
- **E4 — crypto trend** (BTC/ETH/LTC/BNB/XRP, new market): long/short Sharpe 0.89 (**OOS 0.20**); long/flat 1.41
  (**OOS 0.81**), −13% DD — but **42% positive months**. Full-sample inflated by 2017/2020-21 bulls; OOS decays;
  and trend is structurally too choppy to "win most months." Look-ahead 0.00. `campaign/c19_crypto.py`.

**The decisive disproof — % positive months across EVERY market/strategy tested:** crypto-trend 42%, ensemble
61%, SPY 70%, **PUTW (premium-selling) 74%** — and "&le;2 losing months/yr" needs **&ge;83%**. *Nothing* reaches it
except (closest) premium-selling, which carries the −28% to −95% tail. Trend/momentum is choppy by nature
(40–61% positive months) in every market; "win most months" is uniquely the premium-selling = tail trade.

## VERDICT (2026-06-08): the four criteria are mutually contradictory on real instruments
No honestly-backtestable, free-data strategy meets {Sharpe>2, ≤2 losing-months/yr, low DD, ≤$15k}, and the
constraints fight each other:
- **"Sharpe>2 + win-almost-every-month + low-DD" is uniquely the short-vol / premium-selling shape** — whose
  smoothness is paid for by a rare catastrophic tail (−28% to −95% DD). Remove the tail (risk management) and
  the premium goes with it (Sharpe → ~0.3).
- The non-tail paths (diversified trend/ensemble ~0.74–1.0; pairs negative) miss Sharpe>2 **and** are too choppy
  for "win most months" (~50–61% positive months, 6–7 losing/yr).
- **Verified ceiling: Sharpe ~0.9–1.0** (Study-1 trend overlay), ~60% positive months, ~−12% DD.
**Sharpe>2 + ≤2-losing-months + low-DD is not achievable honestly with available data. Not fabricating one.**

## What a credible attempt would require
1. **Defined-risk option selling** (caps per-trade loss) with **real option data** — but the tradeable realization
   (PUTW) is ~0.7 Sharpe, the ">2" lives only in tail-blind models, and a crash hits all positions at once.
2. A genuinely **un-mined market / edge**, likely **higher-frequency** (HFT-territory, not $15k-retail-feasible).
3. Or **relax one constraint** — accept that "win most months" *implies* a tail (DD isn't truly low), or target a
   realistic **Sharpe ~1** balanced/trend portfolio (which we have, audited).
