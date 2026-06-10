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
- **OZB options to protect the trade — PRICED on real OZB quotes; BOTH structures FAIL to help (`c52-c54`):**
  - **(a) defined-risk REPLACEMENT** (buy a cheap OTM option *in* the trade direction *instead of* the future,
    `c53/c53b`): caps the tail as designed (best ~1pt OTM: maxDD $1,055→**$326**, worst −$473→**−$144**) BUT
    costs Sharpe (naked 1.25 → options **~0.85**) — real premiums (~$500–2,600) + bid/ask eat the modest edge.
  - **(b) protective OVERLAY** (hold the future **and** buy an *adverse-side* OTM put/call as insurance — the
    literal "protect the downside" structure the owner asked for, `c54`): **strictly WORSE than naked on Sharpe
    AND Calmar at every strike offset (0.5–2.0pt OTM), under both a generous and a harsh exit-marking.** Even
    the *generous* bound (give the hedge full salvage value) is below naked (e.g. 0.5pt OTM: naked Sharpe
    +0.47/Calmar +1.96 → overlay +0.06/+0.14). Mechanism, visible per-event: the trade wins **>50%** of the
    time, so you bleed premium on the majority of (winning) trades where the hedge expires OTM — e.g. a +$871
    win nets +$9 after an $862 put; a +$1,027 FOMC win nets +$602 after a $425 put. The loss it insures is
    modest (worst ~−$500), and the OTM strike **stops being two-sided quoted ~30 min after a big move** (it
    drifts off-the-money — *because* the trade won), so a realistic exit is an unsellable hedge that lapses,
    which actually **raises** maxDD (e.g. $731→$4,292). Per-trade option insurance is the wrong tool for a
    **losing-streak drawdown** (this trade's real risk, ~$1k) — it is not a per-trade blow-up.
  - **==> Deploy NAKED #1** (DD ~$1k already acceptable on ≤$15k); no OZB options wrap improves it (the `c44`
    cheap-premium first cut was too optimistic). OZB quotes cached at `D:\TradingData\databento\ozb`; the
    PinFly options engine is in place if a future structure is ever wanted.
- Remaining: **colocation** (the sub-second spike) — infra change.
This spec is the no-new-spend path to a tradeable result.
