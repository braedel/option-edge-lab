# ZB MBO Selective-Taker — Stage-1 Interim Result (exploratory)

**Date:** 2026-06-08 · **Status:** INTERIM / exploratory (TRAIN slice; not the registered OOS) ·
**Branch:** `zb-mbo-taker` · **Spec:** `docs/research/specs/2026-06-08-zb-mbo-taker-design.md`

## What was measured
On a **TRAIN-eligible slice of 2024-06 (~5 UTC days, first 6M events)**, with the **frozen grid**
(`src/options_lab/zb_mbo/grid.py`, hash-pinned), every trigger episode was labeled with the
**latency-adjusted taker round-turn P&L** (`labeler.forward_move`): cross the *far touch* at
`t_signal + 1 ms`, hold `H`, cross back to flatten, minus the $4 round-turn ($0.128 = 4/31.25 ticks).
This is the honest taker cost (spread paid both ways); the trigger's own prints are excluded by the
latency offset. Net is in **ticks per round-turn** (1 tick = $31.25).

## Result — every cell net-negative, ~ −1.2 ticks

| Family | threshold | net ticks (H=1/5/30s) | t-stat (H=1s) | n | frac > 1.1t | win-rate |
|---|---|---|---|---|---|---|
| **B sweep** | 3.0 | −1.205 / −1.195 / −1.173 | −235 | 11,837 | 0.000 | 0.001 |
| **B sweep** | 5.0 | −1.212 / −1.206 / −1.195 | −210 | 10,009 | 0.000 | 0.001 |
| **B sweep** | 8.0 | −1.218 / −1.216 / −1.207 | −180 | 7,939 | 0.000 | 0.001 |
| **A vacuum** | 0.50 | −1.128 / −1.215 / −1.308 | −7.0 | 150 | 0.013 | 0.020 |
| **A vacuum** | 0.33 | −0.964 / −1.037 / −2.219 | −2.1 | 55 | 0.036 | 0.036 |
| **A vacuum** | 0.25 | −0.723 / −0.818 / −1.342 | −1.2 | 42 | 0.048 | 0.048 |

## Interpretation
- The taker's **spread+cost floor** is ≈ **−1.128 ticks** (lose the ~1-tick spread crossing both ways +
  $0.128 fee). Every cell sits **at or below** that floor.
- **Sweep adds essentially zero gross edge**: entering 1 ms after a multiple-of-median aggression, the
  short-horizon continuation does not pay the spread. Overwhelmingly significant (t = −235, n = 11,837) —
  not noise, a structural absence of capturable edge.
- **Vacuum (thin-book) shows a *small* gross edge** (~ +0.4 tick at the deepest threshold 0.25, where the
  −0.72 net beats the −1.128 floor) — genuine but **far below the 1.1-tick hurdle** and not statistically
  distinguishable from zero (t ≈ −1.2). This is the prior project's "gross signal exists, dies after cost,"
  reproduced with an *independent* trigger family (and ~0.4 tick gross vs the prior's 0.13 tick — bigger,
  still uneconomic).
- **Kill gate K1 (net > 1.1 ticks) fails for every cell.** Consistent with the deflated prior and the prior
  project's 10 net-negative micro-signal baselines.

## Caveats (why this is strong-preliminary, not the final verdict)
1. **One month**, not the full eligible span (full Stage-1 = all eligible TRAIN+VAL days, purged walk-forward).
2. **Latency 1 ms only** — the registered run sweeps 0.1–5 ms; a slower latency only worsens a taker.
3. **Far-touch fill approximation** — Stage-2 `hftbacktest` (L3 FIFO + real fills) adds **adverse selection**,
   which makes a taker *worse*, not better.
4. **Not the sealed OOS** (2025-11..2026-02), which is touched once at the very end.

A net of −1.2 ticks at t = −235 is extraordinarily unlikely to flip under the full protocol; the registered
run is expected to **confirm the NULL** and quantify the (uneconomic) vacuum gross edge precisely.

## Next
Full census over eligible days → registered Stage-1 (latency sweep, K1/K2/K3, DSR with N_trials=64) →
Stage-2 `hftbacktest` only if any cell unexpectedly clears (none expected) → sealed-OOS one-shot → final
verdict + `CAMPAIGN.md` registry entry. Reproduce: `python campaign/c21_zb_stage1_screen.py` (to be wired
from this exploratory probe).
