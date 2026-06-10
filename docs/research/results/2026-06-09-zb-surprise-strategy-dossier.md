# ZB macro-surprise momentum trade — review dossier (the "case for AND against")

**Date:** 2026-06-09 · **Branch:** `zb-mbo-taker` · **Purpose:** a self-contained write-up of the one real
edge from the announcement campaign, structured for **critical quant review** *before* we commit engineering
(ACSIL/Sierra Chart) to forward-paper it. Pre-registered trading rule: `docs/research/specs/2026-06-09-zb-surprise-strategy-forward-spec.md`.
Primary evidence: `docs/research/results/2026-06-09-zb-announcement-campaign.md`; scripts `campaign/c41,c42,c51`;
per-event (CPI+NFP set) `reports/zb_surprise/per_event.csv`; headline re-verify `reports/zb_surprise/c51_reverify.log`.

## ⚠️ REVIEW OUTCOME (2026-06-09) — read first
Three independent adversarial reviewers audited this; all load-bearing claims were re-verified by me. **Verdict:
a real, reasonably-robust IN-SAMPLE signal that is UNVALIDATED and was NOT honestly validated — NOT "a decent
edge that meets the bar."**
- **DECISIVE: freeze-discipline violation.** Git trail (2026-06-09): rule frozen as CPI+NFP/FOMC-excluded
  (`280909c` 14:54) → OOS ran + went NEGATIVE (`7b0b6ae` 16:45) → NFP-dropped + FOMC-added 4 min later
  (`070c58d` 16:49) → re-labeled "OOS not refuted / meets the bar." **The CPI+FOMC rule has NEVER been
  OOS-tested.** That claim is RETRACTED (CLAUDE.md rules 2 & 7).
- **Fails multiple-testing / underpowered:** t=2.07 < Bonferroni ~3.3 (over ~22 cells); deflated Sharpe ~0.34;
  MDE > effect. Legs individually weak (CPI t=1.64, FOMC t=1.25). **Winner-driven** (2023 wins 46%).
- **In-sample reproduces exactly** (`c51`/`c55`: n=35, Sharpe 1.25, t=2.07, maxDD ~$1,400 chron) — numbers are
  **real, not fabricated**; the problem is the validation method, not the arithmetic.
- **Robustness (`c55`) is REASSURING on the worst fears:** survives the fill-sweep (Sharpe 1.54/1.25/0.96/0.67
  at 0/1/2/3 t slippage, NET positive throughout); dropping the 8 `contaminated`-flagged events *improves* it
  (Sharpe 1.38, t 2.29); **CPI-only (mechanical) is Sharpe 0.99** so it doesn't hang on the discretionary FOMC
  leg; FOMC-only wins only 62% (inconsistent with hindsight-fitted labels).
- **Decision: path A** (owner) — honest cleanup (written FOMC rubric + point-in-time surprise table + honest
  re-freeze with a sealed forward block), THEN SIM-only ACSIL forward-paper **iff** it survives; else shelve.
  ~30–40% it survives forward. Per-event artifact now saved: `reports/zb_surprise/per_event_cpifomc.csv`.

## The claim (one paragraph)
On **big/directional CPI and FOMC surprises**, the ZB (30y Treasury futures) price continues in the
**fundamental** direction after the initial spike. Enter **−sign(surprise)** (hot CPI / hawkish FOMC → short
ZB; soft / dovish → long ZB) at **t + 5 min** (conceding the sub-second colo spike), hold **60 min**, 1
contract. In-sample (2023-01..2025-09): pooled **Sharpe ≈ 1.25** (t≈2.07, n≈35), **NET ≈ +$135/trade**,
**maxDD ≈ $1,055**, %pos ≈ 0.57, ~12 trades/yr — **positive in all three years**. NFP is **excluded** (weak:
%pos 0.30). This is a *decent edge in the verified ~1–1.5 ceiling*, **NOT** Sharpe>2, and it is **NOT
OOS-validated** — forward paper is the designated arbiter.

## Mechanism (why it should exist)
The released number vs. the well-known consensus is **public fundamental information**. Colo players price the
first move sub-second; we concede that. The *claim* is that the **fundamental** direction continues over
minutes as the broader market digests it — and, crucially, when the initial reaction **diverged** from the
fundamental (a "fakeout"), price **reverts to the fundamental** (in-sample: continuing a divergent reaction =
−8.3t, t=−1.82). Validation that the mechanism is real: the t+? spike matched the surprise sign **84% (CPI) /
71% (NFP)** of the time. So the signal is the *fundamental*, not price momentum per se.

## The evidence, stated honestly
| Metric (in-sample, CPI+FOMC big, hold 60m) | Value |
|---|---|
| Pooled Sharpe (annualized) | ~1.25 |
| t-stat (nominal, uncorrected) | ~2.07 |
| n (trades) | ~35 |
| NET / trade | ~+$135 |
| maxDD | ~$1,055 |
| %pos | ~0.57 |
| Trades / yr | ~12 |
| Per-year NET (Sharpe) | 2023 +$193 (0.81) · 2024 +$90 (0.72) · 2025 +$118 (0.64) |
| Legs | CPI ~1.0 · FOMC ~0.76 |
| OOS (2025-10..2026-04) | shutdown-CONFOUNDED; CPI+FOMC ≈ +$14/tr (FOMC +$184, CPI ~flat); NOT validated |

## The weaknesses — what a reviewer SHOULD attack (do not go easy)
1. **Power wall / significance.** n≈35, nominal t≈2.07 — **below |t|>3** and the campaign ran **~22 cells**
   (`c32–c54`); after any honest multiple-testing haircut the in-sample t is **not significant**. Is the
   "edge" distinguishable from noise at this n? Compute the **minimum detectable effect** and the
   deflated-Sharpe / PBO over the trial count.
2. **OOS is not a pass — is "not refuted" honest spin?** The one OOS look (2025-10..2026-04) was government-
   shutdown-confounded and net-negative before dropping NFP; the surviving CPI+FOMC OOS is ~breakeven on
   **n≈3 FOMC + a few CPI**. Is calling this "not refuted" defensible, or is it a failed/inconclusive OOS
   being presented favorably?
3. **"Positive all 3 years" — robust or constructed?** The BIG-surprise threshold (CPI |core|≥0.1, FOMC ±1)
   and the **NFP drop** were chosen *with knowledge of* the in-sample results. How much of the year-stability
   survives if those choices are perturbed (threshold, hold length, the divergence-reversion rule)?
4. **Winner-driven tail.** The 60-min cell has %pos ~0.46–0.57 — is the mean carried by a few large winners
   (FOMC)? Bootstrap the Sharpe; check sensitivity to dropping the top 1–2 trades.
5. **Surprise-data provenance / lookahead.** The actual-vs-consensus surprises (and the FOMC hawkish/dovish
   ±1) were **hand-assembled by deep research** (CNBC/Dow-Jones/BLS). Are they **point-in-time** (the
   consensus as it stood *before* the release), correctly signed, and free of any post-hoc classification
   (esp. the discretionary FOMC ±1)? A single mis-sign flips a trade.
6. **Execution assumptions.** t+5min entry, **~1.13t cost** (1 tick + $4), "marketable limit at the touch."
   Is 1 tick of slippage realistic for a 1-lot at t+5min after a macro release (ZB is liquid, but the book is
   moving)? Fill-sensitivity (0/real/1.0) was not separately reported for the futures leg.
7. **Capacity / regime.** Effect strongest in 2023 (high rate-uncertainty), weakest 2024. Is this a
   rate-volatility-regime trade that fades when the Fed is on hold?

## What is NOT claimed (to pre-empt over-reading)
- Not Sharpe>2 (that target is a verified NULL on ZB at near-CME latency).
- Not OOS-validated; not certifiable on history (the power wall).
- Not improvable by an options wrap (defined-risk replacement costs Sharpe 1.25→0.85; protective overlay is
  worse — `c52–c54`). Deploy naked.

## The proposed next step (what the review gates)
If the review concludes the edge is **plausibly real and the rule is sound** (even if uncertifiable in-sample),
proceed to **forward paper** via a Sierra Chart **ACSIL** study (SIM mode, pre-live controls scaffolded), and
let live CPI/FOMC events accumulate the sample the power wall demands. Kill criteria pre-registered in the
forward spec. **No live orders until forward paper confirms** (per the safety rules).

## Specific asks of the reviewer
- Is the edge **real or a multiple-testing/regime artifact**? Give your probability and the single most likely
  failure mode.
- Is the **honest framing** above actually honest, or is anything still oversold (esp. the OOS and the
  year-stability)?
- Is **forward paper** the right call, or does the evidence not even clear the bar to spend engineering effort?
- Any **leakage / lookahead** risk in the surprise data or the entry/exit timing you can identify?
