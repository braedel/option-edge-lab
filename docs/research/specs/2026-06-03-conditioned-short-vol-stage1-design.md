# Conditioned Short-Vol on SPX — Pre-Registration & Stage-1 Design

**Date:** 2026-06-03 · **Status:** pre-registration for owner review · **Lab:** options-edge-lab
**Companion rules:** `CLAUDE.md` (integrity) · `docs/research/quant_research_process.md` (process)

## 0. One-paragraph thesis (and the deflated prior)
Retail has no *pricing* edge over market-makers; the variance/skew risk premium is compensation for
tail risk, not alpha, and it is the most crowded trade in the retail options world. The *only*
combination with a real chance is **retail selectivity** (we can sit out 95% of the time; an MM cannot)
+ **free structural edges** (SPX/XSP: Section-1256 tax, European, cash-settled, deep liquidity) + a
**non-crowded conditioning signal.** This project tests exactly one thing before spending a dollar on
new data: **do our differentiated signals (futures order-flow / absorption / regime) predict the forward
states premium-selling needs — a quiet tape and the absence of a down-move — *incrementally over* the
crowded baseline every premium-seller already uses?** Deflated prior: modest. The realistic outcome is a
small, tail-dominated positive edge or an honest null. We hunt the *increment*, not the premium.

## 1. Design principles
- **Cross-asset by design.** Futures (ES/NQ/YM) supply the differentiated *signal* (order flow,
  absorption, regime). Options (SPX/XSP) supply the crowded *baseline features* and, later, the
  *execution vehicle.* Signal and instrument live in different asset classes on purpose.
- **Structure is downstream.** Vertical / calendar / diagonal / condor are Stage-2 wrappers the data
  chooses. Stage-1 is structure-agnostic — it tests predictability of the favorable states, which gates
  everything.
- **Spend gated by evidence.** Stage-1a uses only in-hand data (no pull). New options-surface / OI data
  is purchased only if Stage-1a earns it.
- **Increment over baseline is the edge.** "Recent vol predicts forward vol" is mechanical and crowded.
  The hypothesis is strictly about the *incremental* power of the differentiated signals over baseline.

## 2. Data universe (grounded in on-disk inventory, 2026-06-03)
**In-hand (no spend) — sufficient for Stage-1a:**
- Futures intraday (ES/NQ/YM) order-flow & microstructure — `dat-trading-strategy-research/data`,
  `moc-signal-analysis/data`. Source of order-flow / absorption / regime signals.
- SPX underlying intraday — derivable from `spx-0dte-pinfly-lab/data` (~32 GB parquet) + futures.
  Source of the realized-vol & down-move *targets* and the crowded realized-vol *baseline.*
- SPX **0DTE** options (front-of-surface only) — front IV proxy; **not** a term structure.

**Needs a pull (spend) — required only for Stage-1b / Stage-2:**
- Full SPX/XSP **vol surface across tenors** (weekly → 1-yr), multi-year span — for term-structure
  features/targets, dealer-gamma/GEX (needs full-chain OI), and the tradeable longer-dated structures.
  Vendor: Databento OPRA (a vendor key is present in the workspace env, `SPX_FLY_API_KEY`).
- **Plan Step 0** inventories the exact span / tenors / granularity on disk before any modeling; this
  section is the universe, not the line-item manifest.

## 3. Signal inventory
**Baseline B (crowded — the benchmark to beat, NOT the edge):**
- Trailing realized vol (multiple windows), `realized_range`, `efficiency_ratio`, recent returns/trend.
- Calendar: time-of-day / day-of-week (DAT), macro-event flags (FOMC/CPI/NFP/OPEX).
- *(Stage-1b, when surface in-hand:)* IV level / IV-rank, term-structure slope, skew, VRP gap.

**Differentiated D (the actual shot at a non-crowded edge):**
- *In-hand (Stage-1a):* futures **order-flow / trade-sign imbalance** (`trade_sign`, DAT threshold
  detectors), **absorption** (MOC work), intraday **regime label** (`regime` + nonstationarity).
- *(Stage-1b, needs OI/surface pull:)* **dealer gamma / GEX** (`scratch_gex_regime`), `dom_skew`,
  `oi_concentration`.

## 4. Targets (favorable-state labels) — both computable from SPX underlying alone
For decision time *t* and horizon *h*:
- **T1 · Quiet:** forward realized vol of SPX over (t, t+h]. Favorable = low tail (e.g. bottom tercile of
  the trailing-conditional distribution). Continuous version regressed; binary version for AUC / lift.
- **T2 · No down-move:** forward maximum adverse excursion / worst drawdown of SPX over (t, t+h].
  Favorable = forward max drawdown below threshold. **This is the make-or-break target** — it directly
  tests whether the signal dodges the down-tail that kills short premium.
- *(Stage-1b:)* **T3 · Term-structure:** forward change in front-vs-back IV slope (needs surface). Gates
  the calendar / diagonal edge source.

Horizons swept: **h ∈ {1d, 3d, 1wk}** (add 2wk if 1wk is promising). The horizon where D retains
incremental power is the strike zone and constrains Stage-2 structure tenor.

## 5. Stage-1 test design (incremental predictive power)
For each (target T, horizon h):
1. **Nested models.** Baseline M_B uses B only; augmented M_BD uses B ∪ D. Both fit under **purged &
   embargoed walk-forward CV (CPCV)** on the NON-OOS span; OOS stays sealed.
2. **Incremental metric.** Out-of-fold gain of M_BD over M_B: ΔIC (rank), ΔAUC (binary), ΔR² / Δdeviance
   (continuous). D must improve *out-of-fold*, not in-fold.
3. **Honest correction.** Report effect ± SE + t-stat AND the multiple-testing-corrected version over the
   full (signal × target × horizon) grid (Bonferroni/BH; deflated metric where applicable). Maintain the
   trial registry; the haircut uses the honest count.
4. **Power / MDE.** State the minimum detectable incremental effect at the available n per (T,h). Flag
   underpowered cells — a non-significant result on a small sample is *inconclusive*, not *negative.*
5. **Robustness.** Sign-consistency of Δ across folds; sensitivity to feature-set definition; a
   label-shuffled / randomized-D null as a negative control.

## 6. Pre-registered decision rule (the gate)
- **PASS (proceed):** at ≥1 (T,h), M_BD beats M_B out-of-fold with (i) sign-consistent Δ across ≥⅔ of
  folds, (ii) |t| > 3 after multiple-testing correction, and (iii) Δ above the pre-stated MDE. → Then,
  and only then, pull the options surface for Stage-1b / Stage-2.
- **KILL (stop, cheap):** no (T,h) clears the bar → **clean null**, documented as a valid negative. No
  surface pull, no Stage-2. We do not re-litigate the same signals on the same data.
- **INCONCLUSIVE (underpowered):** favorable sign but below MDE / |t|>3 due to small n → explicitly
  decide whether a larger sample is worth assembling before any spend.

## 7. Out of scope for Stage-1 (deferred to a Stage-2 spec, only if Stage-1 passes)
- Options pricing, structure selection (vertical / calendar / diagonal / condor), strike / width, fills,
  fees, settlement, PnL.
- The Stage-2 dumb-baseline gauntlet the eventual strategy must beat net of cost: **always-sell,
  sell-when-IV-rank-high (the crowd), no-trade, random-entry.**
- Any sealed-OOS look (one look, at the very end, on explicit go-ahead) and anything in a future `live/`.

## 8. Integrity guardrails (from CLAUDE.md)
Real data only; no lookahead (features as-of *t*, enforced in code + tests); seal OOS before discovery;
purged / embargoed CV, not a single split; trial registry → honest multiple-testing; |t| > 3
post-correction for any claimed factor; provenance stamp (dataset hash + git commit) on every reported
result; prefer few, monotone, pre-registered features.

## 9. First concrete deliverables (for the plan)
1. **Step 0 — data inventory & contract:** exact in-hand span / granularity for SPX underlying + futures
   flow; define the no-lookahead "feature as-of *t*" contract.
2. **Step 1 — targets:** build T1 (forward RV) and T2 (forward down-move) over h ∈ {1d,3d,1wk}, w/ tests.
3. **Step 2 — features:** baseline B (in-hand) and differentiated D_now (futures flow / absorption /
   regime), strictly as-of *t*.
4. **Step 3 — nested CV harness:** purged / embargoed walk-forward; ΔIC / ΔAUC / ΔR² with multiple-
   testing haircut + MDE.
5. **Step 4 — verdict memo:** PASS / KILL / INCONCLUSIVE per §6, with the trial registry + provenance.
