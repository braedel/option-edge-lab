# Design Spec — ZB MBO Signal-Informed Market-Making (Maker pivot)

**Date:** 2026-06-08 · **Status:** DRAFT for expert review · **Branch:** `zb-mbo-taker` (continues) ·
**Owner-directed pivot** from the taker study. **Shared protocol:** the rigor in
`docs/research/specs/2026-06-08-zb-mbo-taker-design.md` §6–§10 (pre-registration, purged walk-forward,
sealed OOS, DSR/PSR/PBO, multiple-testing, leakage controls) **governs here too**; this doc adds only the
maker-specific design and economics.

## 1. Motivation (verified, not assumed)
The taker study reached a robust NULL **and** discovered a real signal:
- Predictable short-horizon move ≈ **0.1 tick** — single-feature IC ≈ 0.06 across **32 regimes**, and even a
  non-linear GBR captures only ≈ 0.12 t of gross move — structurally ~10× below the ~1.13-t taker spread+cost.
  Taker net ≈ −1.0 t, win ~1%: **dead for a spread-payer.**
- BUT a gradient-boosted model on 13 causal microstructure features predicts the 5-s forward signed move with
  **OOS rank-IC ≈ 0.23, replicated across three unseen months (2025-06/07/08).** A signal that strong is
  uncapturable by a spread-**payer** (taker) but is exactly what a spread-**earner** (maker) uses to manage
  adverse selection. **Owner directed the pivot to the maker side** (2026-06-08).

## 2. Objective
A **signal-informed ZB market-making** strategy toward the goal (Sharpe>2, win-most-months, low DD, ≤$15k),
backtested honestly in **`hftbacktest`** (L3 FIFO queue + 0.5–1.5 ms latency). A documented "still not viable,
here's why" is a valid result.

## 3. Deflated prior (carry up front)
- The goal's profile (many small wins, high Sharpe) **is** the market-making profile — for the first time the
  class matches the goal. But MM's lovely Sharpe hides an **inventory / adverse-selection TAIL** that threatens
  "low DD" (the same trap as short-vol).
- **ZB fills are the make-or-break.** The prior project found ~945 contracts queued ahead and
  **project-blocked naive retail passive-MM as non-viable** (`CAMPAIGN.md`). This is **materially different**,
  not a re-litigation: **(1)** signal-informed quoting (skew/pull by the IC-0.23 model to dodge adverse
  selection — the thing naive MM lacked), **(2)** honest L3 queue+latency validation in `hftbacktest`, **(3)**
  near-CME + Denali L3 + Teton infra. Whether that is *enough* is genuinely unknown.
- Own design — **not** a MakerFlip reconstruction. Honest expectation: uncertain; **fills + adverse selection
  decide it.**

## 4. Strategy — signal-informed passive quoting
- **Signal:** the directional model (GBR frozen on TRAIN) precomputed **offline, causally** per snapshot →
  a per-time directional forecast fed into the backtest (offline precompute per hftbacktest guide §C2; no
  in-engine model calls). Production latency of the model is a deployment note, not a backtest blocker.
- **Quoting:** post-only (GTX) passive orders, **skewed by the signal** — predict-up ⇒ provide on the **bid**
  (get filled buying before a rise) and pull/widen the **ask** (avoid selling into the rise = adverse
  selection); symmetric for down. A v1 may be **one-sided** (quote only the signal-favorable side).
- **Inventory:** hard position cap (≤ a few contracts at ≤$15k margin); skew/flatten as inventory builds; flat
  by session end. **Never-modify** invariant (submit/cancel only — hftbacktest §7).
- **Exit:** passive on the opposite side (capture full spread) where possible; managed taker-exit only when
  inventory/risk forces it.

## 5. Edge source & mandatory P&L decomposition
`net = spread_captured_on_passive_fills − adverse_selection − fees($4 RT) ± inventory_pnl`.
The signal's job is to **shrink adverse selection**; the queue determines capacity. **Report every component
separately** (a positive headline that is actually inventory beta, or spread-capture wiped by adverse
selection, must be visible).

## 6. Execution realism — the core new build (`hftbacktest`)
- L3 FIFO **queue position** (the make-or-break), 0.5–1.5 ms latency (swept 0.1–5 ms), **post-only** fills,
  partial fills for >1 lot.
- **Probe suite before trusting any fill** (extends the taker P1–P6): exact fill price/ts; FILL-drives-fills;
  rc-discipline; **maker-specific:** (a) a passive order fills **only after the queue ahead is consumed**
  (queue-position correctness — assert on a hand-built book); (b) **adverse-selection mechanics** — a fill
  immediately followed by an adverse move is marked at the correct (worse) mark; (c) **post-only** rejects/does
  not cross when it would be marketable.

## 7. Reuse & new build
- **Reuse:** engine `src/options_lab/zb_mbo/{codes,book,calendar,loader,stream,labeler}.py`; the 13-feature
  extractor + the **GBR signal** (trained & **frozen on TRAIN**); `research/stats.py`
  (DSR/PSR/PBO/bootstrap/uniqueness); the eligible_days gate; the rigorous protocol.
- **New:** `src/options_lab/zb_mbo/maker.py` (hftbacktest harness: run loop, post-only quoting, inventory,
  exit) + `maker_probes.py`; signal precompute; `campaign/c25_zb_maker.py` (backtest driver).

## 8. Validation (taker-spec rigor + maker-specific)
- Purged/embargoed walk-forward on eligible TRAIN+VAL months; **sealed-OOS one-shot** (2025-11..2026-02,
  unburned), touched once. The **GBR signal is frozen on TRAIN and never sees VAL/sealed** (cross-stage leakage
  control); its training counts as trials in the deflation (B4).
- **Headline:** net P&L/fill and annualized; **Sharpe (DSR-deflated)**; **% positive months**; **maxDD
  INCLUDING the inventory tail** (block-bootstrap, not one path); **fill rate**; **adverse-selection
  decomposition**; **latency sweep** (must survive 0.5–1.5 ms); **placebo** (signal-shuffled quoting must lose).

## 9. Kill criteria (pre-committed; numbers finalized in the plan)
- **K-fill:** fill rate too low to be a strategy (capacity-dead) → null.
- **K-adv:** adverse selection ≥ spread captured (signal fails to manage it) → null.
- **K-net:** OOS net P&L/fill ≤ 0 after fees → null.
- **K-DD:** inventory-tail maxDD violates "low DD" (the MM tail fired) → downgrade / null.
- **K-lat:** edge doesn't survive 0.5–1.5 ms → null.
- **K-stat:** PBO > 0.5 or DSR-insignificant after N_trials → null.
- **All-null →** documented "signal-informed MM still not viable on ZB for ≤$15k — mechanism (fills /
  adverse selection / tail)", a valid result.

## 10. Integrity
Don't fabricate; re-verify subagent/engine numbers (fabrication watch); the prior naive-passive-MM block is
explicitly noted and this approach is materially distinct **and owner-directed**; a clean documented NULL is a
valid deliverable. The signal model must be frozen pre-evaluation; report the honest fill/adverse-selection
decomposition, not just the headline.
