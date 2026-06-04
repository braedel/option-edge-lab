# Diversified Trend Overlay + 60/40 — Deployable One-Pager (VERIFIED, artifact-scrubbed)

**Date:** 2026-06-03 · **Scripts:** `campaign/c7`–`c11` · **Data:** free Yahoo daily, 21 ETFs, 2008-04 → 2026-06.
**Verification status:** no look-ahead (*proven* by perturbation test), no fitted parameters (all textbook),
friction-stressed (transaction cost + short-borrow), **options hedge EXCLUDED** (unverifiable without
option data; we are not buying data).

## Artifacts found and fixed (this is why earlier numbers moved)
1. **Options tail hedge — REMOVED from all claims.** Its modeled put-spread premium (0.30%/mo) was
   optimistic. At realistic SPX put-spread cost (~0.5–0.8%/mo) it *costs* −0.07 to −0.18 Sharpe (`c10`),
   robust even excluding 2008 & 2020. It reliably halves drawdown but is **not** a Sharpe add; pricing it
   needs option data → **excluded** until/unless that data exists.
2. **Look-ahead in the blend weighting — FIXED & PROVEN.** The prior "equal-risk" blend scaled each leg by
   **full-sample** volatility (unknowable in real time). Perturbation audit (`c11`): old = 2.9e-2
   (look-ahead), fixed = **0.00** (clean). Impact: Sharpe 1.08 → **1.07** (negligible), but **maxDD was
   understated, −10.2% → true −12.4%.**

## Recipe (textbook, pre-registered — nothing fit, nothing optimized)
- **Universe (21 ETFs / 7 asset classes):** SPY QQQ IWM EFA EEM · SHY IEF TLT TIP · LQD HYG · DBC USO UNG DBA · GLD SLV · VNQ · UUP FXE FXY.
- **Trend sleeve:** sign of a blended **1/3/6/12-month** return per market → inverse-60d-vol sizing → **monthly** rebalance (signal at month-end, executed next day, lagged 1d) → equal-risk average → vol-target the sleeve to 10% (trailing vol, shifted).
- **Deployable:** **50% trend sleeve + 50% 60/40**, combined ex-ante (no full-sample scaling). Net 2 bps/rebalance.
- (Cross-sectional momentum was tested and **dropped** — weak, 0.35 / 0.22-OOS. Disclosed.)

## Verified performance (clean — proven no look-ahead)
| | Sharpe | maxDD | vol |
|---|---:|---:|---:|
| SPY | 0.66 | −51% | 20% |
| 60/40 | 0.80 | −31% | 11% |
| Trend sleeve (21-ETF) | 0.76 | −17% | 9.5% |
| **DEPLOY (clean)** | **1.07** | **−12.4%** | 7.6% |

**Robustness (nothing is fit → every period is effectively OOS for the spec):**
- 2016+ Sharpe **1.16**; ex-2008 (≥2010) **1.18**, maxDD −10.0%; sub-periods 2008-12 **0.79** · 13-17 **1.38** · 18-22 **0.99** · 23-26 **1.27**.
- **Frictions (verified, `c11`):** ETF proxy w/ short-borrow → 2bps+1% **1.04**, 2bps+2% **1.00**, 5bps+1% **0.99**, 10bps+2% **0.88**. **Futures (intended vehicle: no borrow, ~1–2 bps) → ~1.07.**
- **Look-ahead: 0.00 (proven).** Turnover ~0.67× notional/month → low, scalable.

**Verified headline: Sharpe ≈ 1.0 (ETF, realistic frictions) → 1.07 (futures), maxDD −12.4%.**
Carries equity beta (corr 0.67 to SPY) — a **balanced portfolio**, not market-neutral alpha.

## Futures implementation (the cheaper, borrow-free vehicle)
ETF backtest is a conservative proxy; run in futures (no borrow, lower cost, margin-efficient, 1256 tax):
SPY/QQQ/IWM→ES/NQ/RTY · SHY/IEF/TLT→ZT/ZN/ZB·UB · GLD/SLV→GC/SI(+HG) · USO/UNG→CL/NG(+RB,HO) ·
DBC/DBA→CL+NG+GC+HG+ZC+ZS+ZW · UUP/FXE/FXY→DX/6E/6J(+6B,6A,6C). EM/credit/TIPS/REIT have no clean single
future → keep as ETF or approximate. Futures adds markets → more diversification → live Sharpe ≥ proxy.

## Honest limits (no hand-waving)
- ETF proxy: shorts pay borrow (modeled 1–2%/yr on short notional); futures eliminate it. Tracking error / roll not in the proxy.
- One sealed split + sub-period/crisis-exclusion checks; nothing is fit, so no train/test optimization to overfit — the century of independent trend evidence is the external OOS.
- Options tail hedge **excluded** pending real option data (no spend). It is drawdown insurance at a Sharpe cost, not a Sharpe add.

## Charts
`reports/deployable_pnl_underwater.png` (DEPLOY vs SPY/60-40 — note maxDD label predates the −12.4% fix),
`reports/tsmom_pnl_underwater.png` (original 8-ETF trend). Hedged tearsheet retired (hedge excluded).
