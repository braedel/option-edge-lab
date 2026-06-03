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
**Direction chosen:** conditioned short-vol on SPX — cross-asset (futures supply the signal, options the
vehicle), structure deferred to the data. Pre-registration + Stage-1 design written:
`docs/research/specs/2026-06-03-conditioned-short-vol-stage1-design.md`. **Stage-1a** (differentiated
signal -> forward realized-vol / down-move, *incremental over* the crowded baseline) runs on **in-hand
data only — no spend until it passes.** Next: implementation plan, then build Stage-1a.
