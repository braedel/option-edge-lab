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
**Autonomous campaign (owner /goal 2026-06-03):** find a futures/options strategy that survives a clean
OOS test. Running log + trial registry: `CAMPAIGN.md`.
- Stage-1a v1 (GEX/DIX → vol): **KILL**.
- **C1** threshold-detector v2 forward-OOS: **NULL** — frozen rules net −$0.90 to −$4.90/trade on unseen
  2025H2–2026 (ES/NQ proxy); historical edge did not persist forward.
- **C2** overnight drift: NULL (Sharpe 0.3–0.8, t<1.2, 2026 reversed; beta, not alpha).
- **C3** options VRP (highest-prior survivor category): **BLOCKED — no data** (in-hand 0DTE is a 90-sec pin
  snapshot; no VIX/option-chains; no Databento key).
- **Status: comprehensive null + data wall.** Remaining OOS-surviving categories (VRP, VIX-carry, diversified
  TSMOM) need a Databento key + small pull budget. Next data-free step: build VRP harness ready-to-run.
