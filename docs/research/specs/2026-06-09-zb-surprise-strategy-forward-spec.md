# ZB big-surprise direction trade — deployable forward-validation spec

**Date:** 2026-06-09 · Derived from the announcement campaign (`docs/research/results/2026-06-09-zb-announcement-campaign.md`).
**What this is:** the one real edge the campaign found, written as a precise, *pre-registered* rule to
forward-paper-trade. It is the only honest way past the power wall (~9 events/yr can't certify on history).

## Why this is tradeable at our latency
The strategy acts at **t + 5 min**, on **public information** (the released number vs the well-known
consensus). No colocation, no low-latency feed — by 08:35 ET the surprise is known to everyone. We concede
the sub-second spike (colo's game) and trade the slower, latency-immune continuation of the *fundamental*.

## The rule (FROZEN — do not tune on history again)
- **Universe:** scheduled **CPI** (core MoM) and **NFP** (headline) releases, 08:30 ET. (FOMC excluded —
  weaker/null in-sample; can be revisited only with its own pre-registration.)
- **Signal:** standardized surprise = actual − consensus (Dow-Jones/Bloomberg median), known by ~08:31.
- **Filter — trade only BIG surprises:** CPI core MoM |surprise| ≥ 0.1%; NFP |surprise| ≥ ~80k (≈ 1σ).
  Skip in-line prints entirely (small surprises were noise / 2024-negative in-sample).
- **Direction:** enter **−sign(surprise)**: a beat (hot) → **short ZB**; a miss (soft) → **long ZB**.
  (This rides the spike when the reaction agreed with the fundamental and fades it when it diverged — the
  divergence cases reverted to the fundamental in-sample.)
- **Entry:** t + 5 min, marketable-limit at the touch (model ~1t slippage).
- **Exit:** time-stop at **+60 min** (CPI may extend to +120 min; NFP-big is strongest at +30 min). **No
  price stop** (Kaminski-Lo: stops degrade this profile). Flat by exit.
- **Size:** 1 contract. ZB initial margin ~$3–4k; observed in-sample maxDD ~$1k → comfortable on ≤$15k.

## Honest expectations (in-sample, NOT certified)
- ~9–12 trades/yr; gross ~+3t per big surprise; **Sharpe ~0.8–1.0**; maxDD ~$1,000; %pos ~0.55–0.61 (30 min).
- CPI leg is the cleanest (Sharpe ~1.25, persists to 120 min); NFP-big strongest at 30 min.
- This is a **"decent edge," NOT Sharpe>2** — it matches the independently-verified ~1–1.5 ceiling.

## Forward-validation protocol (the actual test)
1. **Pre-register** this exact rule + the surprise thresholds (this file, committed) BEFORE the next release.
2. Log every CPI/NFP: surprise, direction, entry/exit fills, net ticks. Use real fills (paper or 1-lot live).
3. After **≥12 big-surprise events** (~1–1.5 yr), compare realized mean/Sharpe to the in-sample ~+3t.
   Kill if the forward mean is ≤ 0 or the sign flips; graduate to size only if it holds.
4. Track the regime: in-sample the effect was strongest in high-rate-uncertainty regimes (2023) and
   weakest in 2024 — note the prevailing regime at each event.

## What this does NOT solve (the open forks)
The Sharpe>2 target is not reachable on ZB futures alone at near-CME latency. Higher-ambition paths, each a
resource decision: **cross-instrument curve RV (ZN/ZF/ES)** [highest prior, needs data], **colocation** [the
spike], **options data** [vol harvesting]. This spec is the no-new-spend path to a tradeable result.
