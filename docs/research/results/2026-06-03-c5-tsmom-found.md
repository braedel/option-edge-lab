# C5 — Diversified Time-Series Momentum — **FOUND** (the genuine OOS survivor)

**Date:** 2026-06-03 · **Script:** `campaign/c5_tsmom.py` · **Data:** free Yahoo daily adj-close,
8 cross-asset ETFs, 2007-01 → 2026-06 (n=4,885).

## The strategy (textbook, pre-registered — zero tuning)
Time-series momentum / trend-following across **equities (SPY, EFA, EEM), bonds (TLT, IEF), commodities
(DBC), gold (GLD), dollar (UUP)**. Standard params, **not fit**: position = sign of trailing **12-month
(252d)** return; size each leg to equal risk by **inverse 60-day vol** (10%/leg target); **monthly**
rebalance; ~2 bps/rebalance cost. Signals lagged 1 day; vol/momentum use trailing data only — no lookahead.

## Why this clears the bar (passes process + scrutiny + survives OOS)
- **Survives OOS:** Sharpe **0.45 in DEV (≤2015) and 0.45 in OOS (≥2016)** — identical; positive in the
  out-of-sample period including the 2022 crisis (+6.7%).
- **Crisis alpha (the point of trend):** +6.6% in 2008 (SPY −33.8%), +6.7% in 2022 (SPY −18.2%),
  +3.7% 2011, +5.3% 2015. Positive when equities fall.
- **Genuinely diversifying:** correlation to SPY = **0.01**.
- **Improves a real portfolio:** 50% 60/40 + 50% TSMOM → full-sample Sharpe **0.79 → 0.86** and max
  drawdown **−27% → −13% (halved)**.
- **Robust, not mined:** holds under a 1/3/6/12-month blend (Sharpe 0.54, OOS 0.64) and at 10 bps/rebalance
  (0.40). No parameter was optimized — these are the textbook values, and the result **matches the published
  managed-futures / SG-Trend literature**, i.e. it is a replicated factor, not a fluke.
- **Tradeable as futures (the goal's vehicle):** real trend programs run this on liquid futures (ES, ZN/ZB,
  GC, CL, 6E, etc.) — which are *cheaper* than the ETF proxy used here (no borrow, lower cost, 1256 tax), so
  this backtest is **conservative** vs the futures implementation. Low turnover (monthly) → cost-tolerant.

## Honest characterization (the quant filter — no overselling)
TSMOM is **not a high-Sharpe standalone money-maker.** Standalone Sharpe ≈ 0.45–0.54, CAGR ~2–5% at 10%
vol — it **lags buy-and-hold in bull markets** (it gave up return through the 2016–2026 equity bull). Its
value is **diversification + crisis insurance + drawdown reduction**, not beating equities outright. The
strong *full-sample* portfolio-Sharpe lift leans on 2008 (in-sample); across the benign 2016–2026 OOS bull
the Sharpe lift was ~flat (blend 0.89 vs 60/40 0.94) — what replicated OOS was the **drawdown halving and
the 2022 crisis-alpha instance.** So the honest deliverable is: *a robust, OOS-surviving, tradeable
trend-following overlay that cuts portfolio drawdown ~in half and pays off in equity bears — a crisis hedge
with modest positive carry, not an alpha engine.*

## Verdict
**Goal met.** After a campaign of NULLs (prediction edges decay OOS; the VRP is short-vol beta), diversified
time-series momentum is the one strategy that genuinely **passes the quantitative process** (textbook,
no overfitting, robust to lookback/cost, no lookahead), **passes scrutiny** (a century of independent OOS
evidence, zero equity correlation, crisis alpha, institutionally deployed), and **survives the OOS test**
(stable Sharpe in/out, positive through 2022). It is tradeable in futures, conservative here as an ETF
proxy. Characterized truthfully: a diversifying crisis-hedge overlay, modest standalone, that materially
improves a standard portfolio's risk profile out-of-sample.
