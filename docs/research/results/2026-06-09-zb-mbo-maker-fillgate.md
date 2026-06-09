# ZB MBO Maker — Conditional-on-Fill Gate (offline, pre-hftbacktest)

**Date:** 2026-06-09 · **Status:** INCONCLUSIVE-leaning-skeptical (economics straddle zero) ·
**Branch:** `zb-mbo-taker` · **Script:** `campaign/c25_zb_maker_fillgate.py`

## Purpose
Decide cheaply, on offline data, whether the OOS-validated directional signal (GBR IC_oos ≈ 0.226,
`reports/zb_taker/multivariate.json`) plausibly supports a **maker** before building the expensive
`hftbacktest` harness. A passive maker's fills are adversely selected, so unconditional IC is not a maker
edge — this tests **fill-conditioning** with a coarse, queue-aware fill proxy (optimistic on fills by design:
a FAIL even here = null).

## Result (train 2024-05/06/07 → VAL 2025-09, unseen, ~5 days, 177,699 snapshots)
| Metric | Value |
|---|---|
| IC_uncond (signal vs fwd mid move) | +0.258 |
| **IC_fill (on the filled subset)** | **+0.181 (0.70 × uncond)** |
| quotes (top-25% \|signal\|) / fills / fill-rate | 44,426 / 4,642 / **10.4%** (~928/day) |
| post-fill drift per fill | **−0.117 t** (median 0.000; 20% favorable) |
| maker net/fill — optimistic (exit at mid) | **+0.255 t** |
| maker net/fill — conservative (cross to exit) | **−0.245 t** |

## Interpretation (honest)
- **The cheap kill did NOT fire.** The signal **survives fill-conditioning** (IC_fill = 70% of unconditional)
  — contra the strong prior that adverse selection would destroy it. This is the real, notable positive and
  the reason signal-informed MM could differ from the blocked naive MM.
- **The economics straddle zero.** +0.255 t if exits are passive (capture the full spread), −0.245 t if exits
  must cross. The sign is entirely an **exit-execution** question this proxy does not model, and **real
  adverse selection is present** (−0.117 t post-fill drift).
- **The proxy is optimistic on fills** (queue cleared by displayed-size aggressor volume; ignores hidden
  liquidity, latency, exact matching — all verified harder in the real engine by the SWE review). So the
  truth likely shifts toward the conservative/negative end.
- The "PASS" of the pre-registered K-cond rests on the **optimistic** bound; honest verdict =
  **inconclusive-leaning-skeptical**, not a go.

## Decision
A result that straddles zero on the exit assumption can only be resolved by the **real `hftbacktest`
harness** (exit fills + queue position + adverse selection modeled). Proceed to build it — justified because
the cheap kill didn't fire and signal-survival is genuine — with **calibrated expectations** (likely
marginal/negative once fills are realistic). Build order per the SWE review: **C1 (prove a passive fill at
all, from hftbacktest's own examples) → probes → strategy → purged-WF + sealed-OOS verdict.** Do not oversell;
a documented "marginal/negative under realistic fills" remains the expected and valid outcome.
