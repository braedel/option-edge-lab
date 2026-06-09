# ZB MBO Microstructure Study — Verdict (taker + maker)

**Date:** 2026-06-09 · **Branch:** `zb-mbo-taker` · **Goal:** Sharpe>2, win-most-months, low DD, ≤$15k.
**Result: documented NULL** — a real, OOS-robust directional signal exists in ZB L3 MBO, but it is **not
economically capturable** for this goal by either a taker or a maker at the modeled latency/cost/capital.
(A documented ceiling/NULL is a valid result per the owner directive; no fabricated >2.)

## The signal IS real (this is not "no signal")
A gradient-boosted model on 13 causal microstructure features predicts the 5-s forward signed mid move with
**OOS rank-IC ≈ 0.226**, replicated over three unseen months (2025-06/07/08, 506k obs;
`reports/zb_taker/multivariate.json`). Single-feature ceiling is ~0.06 (depth imbalance, robust across 32
months); the non-linear combination roughly quadruples it. Genuine, generalizing predictive content.

## Taker — NULL (a spread-PAYER cannot capture it)
The predictable move is **~0.1 tick** while a taker pays ~1 tick spread + $4 RT (~1.13 t). Across 32 regimes
(single-feature), linear + non-linear OOS, and a 5→1800 s horizon sweep, the predictable component stays
pinned ~0.1 t (IC decays ~as fast as the move grows). Taker net **≈ −1.0 t/round-turn, win ~1%**
(`docs/research/results/2026-06-08-zb-mbo-taker-stage1-interim.md`, `campaign/c22–c24`).

## Maker — NULL (a spread-EARNER is killed by the adverse-selection tail)
Signal-informed passive quoting was tested with a **coarse, fill-optimistic offline round-trip proxy**
(`campaign/c25`, `c26`): selective top-quartile quotes, passive entry + passive-exit-or-forced-cross.
- The signal **survives fill-conditioning** (IC_fill ≈ 0.70 × unconditional) — the real reason MM was worth
  checking, and why it differs from the blocked naive passive-MM.
- **Round-trip economics, two unseen months:** wins **64% / 69%** of round-trips with a **positive median
  (+0.87 t)** — it *does* capture the spread most of the time — but the **mean is net-negative (−0.77 t /
  −1.02 t)**: the **adverse-selection / inventory tail** (losers ~−3.7 t avg, worst −16 to −28 t; ~21–30-min
  stuck holds force-crossed at adverse prices) dominates. **Net-negative even under the optimistic proxy.**
- This is the textbook **win-most-but-catastrophic-tail** signature — it superficially matches
  "win-most-months" while *failing* "low DD" via the tail. **The same finding as Study 2** ("win most months"
  *is* the tail trade), now at the microstructure level.

**Why no `hftbacktest` harness was built:** an *optimistic* offline proxy is already net-negative on both
months, and the real L3 engine is strictly harder (lower/again-adversely-selected fills, exit adverse
selection — all verified against the installed engine in the SWE review). It would only confirm worse, so the
multi-week build was not warranted. (Caveat: this maker conclusion is **proxy-based**, not a full
hftbacktest/sealed-OOS verdict; the harness remains the airtight confirmation if ever desired — expected to
confirm the NULL.)

## Synthesis & what a credible attempt would require
The real IC-0.23 signal is uncapturable for the goal because: a taker's edge (~0.1 t) is ~10× below the
spread+cost, and a maker's spread-capture is eaten by the adverse-selection tail at the modeled fills/latency.
Capturing it would require **true colocation** (sub-ms, front-of-queue passive fills that flip the maker's
fill rate and adverse-selection economics) — not the near-CME-not-colo regime here — or a fundamentally
cheaper-to-trade structure, or a different capital/capacity profile. None is available or honestly testable at
≤$15k here.

## Integrity / method notes
Leak-free causal engine (perturbation-proven); action codes/side conventions attested on real data; the
headline 0.23 was re-run and committed with provenance (an earlier lapse: it was cited before its evidence was
committed — fixed); expert quant + SWE reviews applied; deflated prior carried throughout. Both NULLs are the
deflated-prior-expected outcome.
