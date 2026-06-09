# ZB MBO Selective-Taker — Pipeline Validation (smoke test, NOT an edge result)

**Date:** 2026-06-08 · **Status:** PIPELINE VALIDATION ONLY — *not* an edge determination ·
**Branch:** `zb-mbo-taker`

> **Correction (read first).** An earlier version of this file framed a one-month, one-hour, one-latency
> probe as a "preliminary NULL" that "confirms the deflated prior." **That framing was wrong and is
> retracted.** One month is statistically insufficient to conclude anything about edge presence or absence,
> the quant protocol does **not** sanction any judgment from it, and *failure to find an edge in an hour
> does not prove the edge is not there.* This document records only that the measurement **pipeline runs
> end-to-end and is arithmetically sane**. The edge question is decided exclusively by the full registered
> run (below), which has not yet been done.

## What this probe was for
Confirm that the chain `events → L3 replay → bbo_timeline + feature stream → triggers → latency-adjusted
forward_move` executes on real ZB data and returns sane numbers, before launching the expensive full run.

## What ran (NOT a finding)
A ~5-day slice of 2024-06, frozen grid, latency 1 ms. The chain produced net-tick numbers for every cell.
Arithmetic sanity check only: a taker that crosses the spread has an **unconditional floor of ≈ −1.128
ticks** (lose the ~1-tick spread both ways + $0.128 fee). The slice's *marginal* averages sit near that
floor. **This is the expected arithmetic for any taker whose signal is not strongly predictive on a tiny
sample; it does not distinguish "no edge" from "an edge that a single month / the marginal mean does not
surface."** No conclusion is drawn.

## The real test (pending — this is what decides the question)
1. **Full registered Stage-1** over **all eligible train+validation months** (`campaign/c21_zb_stage1_screen.py`):
   per-cell latency-adjusted expectancy with **purged walk-forward folds**, per-year sign-stability,
   multiple-testing correction (Holm/BH across the 54 cells) and the latency sweep. Kill gates K1/K2/K3.
2. **Stage-2 `hftbacktest`** (L3 FIFO fills + real latency + adverse selection) for any cell that survives.
3. **Sealed-OOS one-shot** (2025-11..2026-02), DSR/PSR/PBO, then the final verdict + `CAMPAIGN.md` entry.

Until step 1 completes over the full span, **no statement about edge presence or absence is warranted.**
