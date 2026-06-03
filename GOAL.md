# GOAL — options-edge-lab

**Status:** greenfield · selecting candidate edges · **target: TBD**

## Charter
Find a **real, out-of-sample-survivable options edge** and prove it under strict research integrity — or
prove there isn't one (a clean null is a valid deliverable). Inherit the process and mechanics from
`spx-0dte-pinfly-lab`; do **not** inherit its strategy assumptions.

## What "done" looks like for a candidate
A pre-registered rule, frozen before the sealed OOS look, that:
- beats dumb baselines net of realistic fills and fees,
- survives multiple-testing correction (Bonferroni/BH -> deflated-Sharpe/PBO) at |t| > 3,
- holds across purged / embargoed walk-forward (CPCV), and
- still works at the owner's real fill fraction (not just optimistic fills).

## Lessons carried in (from PinFly)
- Don't bet on a mechanism the structure already prices (the long fly priced confirmation at ~+$1/sec;
  calm was already priced; the cash index doesn't pin).
- `hit-rate != PnL` — measure money at real fills, not a proxy.
- Don't re-litigate a dead detector family on the same data; spend OOS only on genuinely fresh hypotheses.

## Current step
**Stage-1a v1 = KILL (robust).** Built + ran the incremental-signal gate (pipeline in `src/options_lab`,
plan `docs/research/plans/2026-06-03-stage1a-incremental-signal.md`). On 3,605 pre-OOS daily obs
(2011 -> 2025-08), lagged SqueezeMetrics GEX+DIX add **no** incremental out-of-fold skill over a
realized-vol baseline for forward RV / drawdown (every ΔR² < 0); robust to a nonlinear model + lag-0.
Result: `docs/research/results/2026-06-03-stage1a-v1.md`. OOS (2025-09+) untouched; no data spend.
**Decision pending:** v2 (own futures order-flow — fresh but deflated prior), pivot horizon, or stop.
