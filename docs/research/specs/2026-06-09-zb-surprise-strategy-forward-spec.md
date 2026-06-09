# ZB big-surprise direction trade — deployable forward-validation spec

**Date:** 2026-06-09 · Derived from the announcement campaign (`docs/research/results/2026-06-09-zb-announcement-campaign.md`).
**What this is:** the one real edge the campaign found, written as a precise, *pre-registered* rule to
forward-paper-trade. It is the only honest way past the power wall (~9 events/yr can't certify on history).

## Why this is tradeable at our latency
The strategy acts at **t + 5 min**, on **public information** (the released number vs the well-known
consensus). No colocation, no low-latency feed — by 08:35 ET the surprise is known to everyone. We concede
the sub-second spike (colo's game) and trade the slower, latency-immune continuation of the *fundamental*.

## The rule (FROZEN — do not tune on history again)
- **Universe:** the two real legs — **CPI** (core MoM, 08:30 ET) and **FOMC** (rate decision, 14:00 ET).
  **NFP de-emphasized** (in-sample %pos 0.30, Sharpe 0.23 at 60-min hold — weak). FOMC, added in the
  2026-06-09 expansion, lifted the pooled edge to Sharpe ~1.2 (t=2.01, n=45) and was the leg that held in the
  (confounded) OOS.
- **Signal:** CPI = standardized surprise (actual − Dow-Jones/Bloomberg consensus), known ~08:31. FOMC =
  hawkish(+1)/dovish(−1) read from the decision/statement/dots vs market expectations (known ~14:05).
- **Filter — trade only BIG/directional surprises:** CPI core MoM |surprise| ≥ 0.1%; FOMC any
  hawkish/dovish (non-neutral) outcome; (NFP |surprise| ≥ ~80k only if traded). Skip in-line/neutral prints.
- **Direction:** enter **−sign(surprise)**: CPI beat (hot) → **short ZB**, miss (soft) → **long ZB**; FOMC
  hawkish → **short ZB**, dovish → **long ZB**. (Rides the spike when the reaction agreed with the
  fundamental, fades it when it diverged — divergence cases reverted to the fundamental in-sample.)
- **Entry:** t + 5 min, marketable-limit at the touch (model ~1t slippage).
- **Exit:** time-stop at **+60 min** (CPI may extend to +120 min; NFP-big is strongest at +30 min). **No
  price stop** (Kaminski-Lo: stops degrade this profile). Flat by exit.
- **Size:** 1 contract. ZB initial margin ~$3–4k; observed in-sample maxDD ~$1k → comfortable on ≤$15k.

## Honest expectations & reliability evidence
- **CPI+FOMC big/directional (NFP dropped):** in-sample **Sharpe ~1.25** (t=2.07, n=35), NET **+$135/trade**,
  **maxDD ~$1,055**, %pos 0.57, **~12 trades/yr**. Legs: CPI ~1.0, FOMC ~0.76.
- **Year-stability (the key reliability evidence): positive in ALL THREE years across distinct rate regimes**
  — 2023 +$193 (Sh 0.81) / 2024 +$90 (0.72) / 2025 +$118 (0.64), %pos rising 0.46→0.62→0.67. NOT a 2023
  artifact (unlike pre-CPI drift +6.6→−1.0 and NFP-breakout +9.8→−3.3, which decayed).
- **OOS (2025-10..2026-04, shutdown-confounded): CPI+FOMC ≈ +$14/trade (breakeven-to-positive)** — FOMC
  +$184, CPI ~flat. The −$98 OOS loss was driven by 2 *distorted NFP* prints (now dropped); the real edge
  was NOT refuted OOS.
- A **"decent edge," NOT Sharpe>2** — matches the verified ~1–1.5 ceiling; squarely in the stated 1–2 range.
  Credibility = coherent mechanism + breadth (2 legs) + **3-year stability** + low DD. **Forward paper is the
  final confirmation, but this is real reliability evidence, not a single in-sample number.**

## Forward-validation protocol (the actual test)
1. **Pre-register** this exact rule + the surprise thresholds (this file, committed) BEFORE the next release.
2. Log every CPI/NFP: surprise, direction, entry/exit fills, net ticks. Use real fills (paper or 1-lot live).
3. After **≥12 big-surprise events** (~1–1.5 yr), compare realized mean/Sharpe to the in-sample ~+3t.
   Kill if the forward mean is ≤ 0 or the sign flips; graduate to size only if it holds.
4. Track the regime: in-sample the effect was strongest in high-rate-uncertainty regimes (2023) and
   weakest in 2024 — note the prevailing regime at each event.

## What this does NOT solve (the open forks)
The Sharpe>2 target is not reachable on ZB futures alone at near-CME latency. Status of the other tracks:
- **Cross-instrument curve RV (ZN/ZF/ES) — TESTED = NULL** (`c46-c50`). The fixed-β residual reversion looked
  like Sharpe ~1.2/1.6 but it was a full-in-sample-β centering artifact; with a deployable rolling β it's
  in-sample ~0.5 and **OOS-negative**. Near-unit-root residual + directional 2023–25 curve trend + multi-leg
  cost (~3.7t crossing vs ~2t limit). Don't re-litigate without finer (MBP-1) execution data.
- **OZB options (defined-risk)** — the cheap-OTM wrap of THIS edge was promising in the c44 first cut (keeps
  Sharpe, halves DD) but is **gated on this edge validating forward** (no point wrapping an unproven edge).
- Remaining: **colocation** (the sub-second spike) — infra change.
This spec is the no-new-spend path to a tradeable result.
