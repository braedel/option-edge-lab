# Diversified Trend Overlay + 60/40 — Deployable One-Pager

**Date:** 2026-06-03 · **Scripts:** `campaign/c7_multifactor.py`, `c8_deployable_hedged.py`,
`c9_stress_hedged.py` · **Data:** free Yahoo daily, 21 ETFs, 2008-04 → 2026-06.

**One line:** a diversified **time-series-momentum (trend / managed-futures) overlay** combined equal-risk
with a **60/40** core delivers **Sharpe 1.08 (1.15 OOS), max drawdown −10%** — a fifth of equities' −51% —
robust to costs, sub-period, and dropping 2008; an optional modeled **put-spread tail hedge** trims the
drawdown to **~−5%**.

## 1. The recipe (textbook, pre-registered — nothing tuned)
- **Universe (21 ETFs / 7 asset classes):** SPY QQQ IWM EFA EEM · SHY IEF TLT TIP · LQD HYG · DBC USO UNG DBA · GLD SLV · VNQ · UUP FXE FXY.
- **Trend sleeve:** sign of a **blended 1/3/6/12-month** return per market → **inverse-60d-vol** sizing → **monthly** rebalance → equal-risk average → **vol-target the sleeve to 10%**.
- **Deployable:** **50% trend sleeve + 50% 60/40, equal risk.** Net ~2 bps/rebalance.
- (Cross-sectional momentum was tested and **dropped** — weak, Sharpe 0.35 / 0.22-OOS. Disclosed, not hidden.)

## 2. Performance & stress (the robustness evidence)
| | Sharpe | OOS ≥2016 | maxDD | vol |
|---|---:|---:|---:|---:|
| SPY | 0.66 | 0.89 | −51% | 20% |
| 60/40 | 0.80 | 0.94 | −31% | 11% |
| Trend sleeve (21-ETF) | 0.76 | 0.79 | −17% | 9.5% |
| **DEPLOY** | **1.08** | **1.15** | **−10.2%** | 7.2% |

**[3] Stress — it is not overfit:**
- **Cost:** Sharpe 1.09 / 1.08 / 1.03 / 0.95 at 1 / 2 / 5 / 10 bps per rebalance (futures cost ~1–2 bps → it lives at the top).
- **Drop the GFC (≥2010):** Sharpe **1.16**, maxDD −9.0% — *better* without 2008; not a crisis-of-2008 artifact.
- **Sub-period stability:** 2008-12 **0.82** · 2013-17 **1.33** · 2018-22 **1.02** · 2023-26 **1.21** — >0.8 in every regime.
- **OOS > in-sample** (1.15 vs 1.08) — the opposite of an overfit signature.
- **Capacity:** ~0.67× notional turnover/month → low; the instruments are the most liquid futures on earth → highly scalable.

## 3. Options tail hedge (used surgically) — VERIFIED (C10), and the "Sharpe lift" did NOT survive
Trend is already a positive-carry synthetic hedge, so explicit puts only cover the **fast crashes trend is too slow to catch**. A **modeled** rolling 1-month SPY put **spread** (5→20% OTM, ~0.30 equity-beta notional).
At my optimistic 0.30%/mo premium it showed monthly Sharpe 1.21→1.26. **Re-tested at realistic premiums**
(real SPX 1m 5→20% spreads cost ~0.5–0.8%/mo): the lift **reverses to −0.07 (0.50%/mo) … −0.18 (0.70%/mo)**,
and stays negative even excluding 2008 **and** 2020 (−0.13 to −0.20). The apparent lift was a premium artifact.
**What IS robust at every premium/sample: maxDD −8.6% → ~−5% (the tail is reliably halved).**
**Verdict: the hedge is genuine drawdown insurance at a ~0.1–0.2 Sharpe cost (~1%/yr) — NOT a Sharpe boost.**
The headline **Sharpe 1.08 stands on the *unhedged* portfolio.** (Replace the modeled premium with real option
data — ~$200–1,500 — to finalize.) Script: `campaign/c10_verify_hedge.py`.

## 2 (spec). Futures implementation — the real, cheaper, scalable build
The ETF backtest is a **conservative proxy**; run it in futures (no borrow, lower cost, capital-efficient margin, 1256 60/40 tax). Map:

| ETF | Asset class | Liquid future (micro) |
|---|---|---|
| SPY / QQQ / IWM | US equity | ES (MES) / NQ (MNQ) / RTY (M2K) |
| EFA | Dev-intl equity | FESX (Euro Stoxx) + NK (Nikkei) |
| SHY / IEF / TLT | US rates 2y/10y/30y | ZT / ZN / ZB · UB (ultra) |
| GLD / SLV | metals | GC (MGC) / SI (SIL) · + HG (copper) |
| USO / UNG | energy | CL (MCL) / NG · + RB, HO |
| DBC / DBA | commodity / ag basket | CL+NG+GC+HG+ZC+ZS+ZW (replicate) |
| UUP / FXE / FXY | FX | DX / 6E / 6J · + 6B, 6A, 6C |
| EEM, LQD, HYG, TIP, VNQ | EM eq / credit / TIPS / REIT | **no clean single future → keep as ETF or approximate** |

Net: ~15 of 21 map to deep futures, and the futures universe naturally **adds** markets (copper, refined energy, individual grains, more FX & rate tenors) → **more diversification than the ETF proxy**, so the live Sharpe should be **≥** the backtest. Run at a 10–15% vol target; monthly rebalance; size each market by inverse-vol to equal risk.

## Honest caveats
- DEPLOY carries equity beta (corr 0.67 to SPY) — a **balanced portfolio**, not market-neutral alpha. The trend *sleeve* alone is 0.76; the >1 is the diversification math of overlay + beta.
- Free ETF data with survivorship-clean liquid names; a production build should use point-in-time futures with roll handling.
- The hedge is modeled (no option-price data on hand).

## Charts
- `reports/deployable_pnl_underwater.png` — DEPLOY vs SPY / 60-40, PnL + underwater.
- `reports/deployable_hedged_tearsheet.png` — DEPLOY vs DEPLOY+hedge, underwater tail-trim.
- `reports/tsmom_pnl_underwater.png` — the original 8-ETF trend strategy.
