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

## Honest expectations (in-sample, NOT certified)
- **~16 big/directional trades/yr** (CPI+FOMC); **pooled in-sample Sharpe ~1.2** (nominal t=2.01, n=45 —
  MT-discounted across the campaign it's marginal), NET ~+$116/trade, **maxDD ~$1,274**, %pos ~0.51.
- Legs: **CPI Sharpe ~1.0** (cleanest, persists to 120 min); **FOMC ~0.76** (%pos 0.62; held in confounded
  OOS); **NFP weak ~0.23** (drop/de-emphasize).
- This is a **"decent edge," NOT Sharpe>2** — matches the verified ~1–1.5 ceiling; in the stated 1–2 range.
  Credibility is from coherence + breadth + low DD, NOT statistical certainty; **forward paper is the arbiter.**

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
