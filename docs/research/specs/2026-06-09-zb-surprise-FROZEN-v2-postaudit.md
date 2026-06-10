# ZB macro-surprise trade — FROZEN v2 (post-audit re-registration)

**Frozen:** 2026-06-09, AFTER the 3-reviewer critical audit. Supersedes v1
(`2026-06-09-zb-surprise-strategy-forward-spec.md`, retained as the corrected historical record). This is the
**honest re-freeze**: the rule is locked here, in writing, as an explicitly **UNVALIDATED hypothesis**, before
any forward/sealed test. Audit + status: `docs/research/results/2026-06-09-zb-surprise-strategy-dossier.md`.

## Honest status (no overselling)
A **real, perturbation-robust IN-SAMPLE signal** (~Sharpe 1.0–1.25 in 2023-01..2025-09) whose inputs are now
leak-checked — **but it is NOT validated**: it fails multiple-testing (t≈2.07 < |t|>3 over ~22 trials;
deflated Sharpe ~0.34; underpowered), is winner-driven, and — because of the v1 freeze violation (the CPI+FOMC
rule was re-tuned after the only OOS look) — **has never been tested out-of-sample.** Estimated **~30–40%** it
survives forward. The **power wall** (~12 events/yr) makes forward paper the ONLY honest validation; history
cannot certify it. **No live orders, no size, until forward paper confirms** (kill-gate below).

## What the audit cleared (why it's worth forward-testing, not shelving)
- **Fill realism:** survives the mandated sweep — Sharpe 1.54 / 1.25 / 0.96 / 0.67 at 0/1/2/3 ticks round-trip
  slippage; NET stays POSITIVE through 3 ticks (`c55`). Not a sub-cost mirage.
- **Contamination:** dropping the 8 `contaminated`-flagged events *improves* it (Sharpe 1.38) — edge doesn't
  depend on them.
- **FOMC leakage:** an independent BLIND rubric re-classification of all 22 FOMC meetings reproduced **21/22**
  hardcoded labels; the lone flip (2024-06-12) is a +$90 winner, removing it → Sharpe 1.23. Labels are
  point-in-time-reproducible, NOT hindsight-fitted.
- **No-lookahead:** entry/exit code verified causal (`px_at` = last trade at/before t; no forward peek).
- The edge does **not** hang on the discretionary leg: CPI-only (mechanical) is Sharpe 0.99.

## THE FROZEN RULE (do not tune again; changes require a new dated re-freeze)
- **Universe:** **CPI** (core MoM, 08:30 ET) and **FOMC** (14:00 ET). NFP excluded (in-sample %pos 0.30).
- **Signal & BIG filter — trade only:** CPI core-MoM surprise (actual − point-in-time consensus) with
  **|surprise| ≥ 0.1%**; FOMC with a **non-neutral (±1)** classification per the rubric below. Skip in-line.
- **Direction:** **−sign(surprise)** — hot CPI / hawkish FOMC → **short ZB**; soft / dovish → **long ZB**.
- **Entry:** t + 5 min after the release, marketable-limit at the touch.
- **Exit:** time-stop at **+60 min**. No price stop. Flat by exit.
- **Size:** 1 contract (forward paper / SIM). DD budget ~$1.4k → fine on ≤$15k.
- **Cost basis for evaluation:** model ≥ 1 tick round-trip slippage + $4 RT; report realized fills.

## THE FOMC CLASSIFICATION RUBRIC (pre-commit each label IN WRITING at ~14:05 ET, before observing the reaction)
Classify the meeting **vs. what the market priced going in** (fed funds / SOFR futures + dealer surveys),
using only the statement, SEP/dots, decision, and presser:
- **HAWKISH (+1):** more restrictive than priced — higher dots / fewer projected cuts, a hawkish hold,
  restrictive statement-language changes, a decision or guidance tighter than priced, or a hawkish presser.
- **DOVISH (−1):** more accommodative than priced — more cuts, a dovish cut, softer language/guidance.
- **NEUTRAL (0) → NO TRADE:** broadly as priced / mixed / no clear surprise.
- Benchmark is **vs. market expectations just before the meeting**, NOT vs. the prior meeting. If genuinely
  unclear, default to NEUTRAL (no trade). The pre-committed, timestamped label is the integrity guard against
  forward hindsight. (Validated in-sample labels: `reports/zb_surprise/per_event_cpifomc.csv` + the blind
  re-classification; 2024-06-12 → neutral.)

## PRE-REGISTERED FORWARD KILL-GATE (stricter than v1 — accounts for winner-driven + the honest prior)
Log every qualifying event: date, type, surprise, pre-committed direction/label, entry/exit fills, net ticks.
- **Evaluate after ≥ 20 qualifying events (~1.5–2 yr).** Before then, paper only; no size.
- **KILL** (signal not real / shelve) if ANY of: forward mean **≤ +1 tick** net · forward **median ≤ 0** ·
  **%pos < 0.45** · sign of the mean flips vs in-sample.
- **GRADUATE to (small) size** only if ALL of: forward **mean ≥ ~+2 ticks** net (≈ half the in-sample point
  estimate, honest haircut) · forward annualized **Sharpe ≥ 0.8** · %pos ≥ 0.50 · no single event >50% of
  cumulative PnL (winner-concentration guard).
- Realistic forward expectation: **Sharpe ~0.9–1.1, winner-driven, with frequent losing trades** — not 1.25.

## What is NOT done (disclosed)
- A full point-in-time reconstruction of every CPI/NFP consensus vintage + first-print actual was **not** done
  (CPI surprises sit on the ±0.1 boundary). This does **not** contaminate the forward test (forward uses live
  consensus + first-print actuals by construction), and the in-sample edge survives dropping the
  contaminated-flagged events — but the in-sample CPI prior carries residual ±0.1 fragility. The forward test
  is the arbiter regardless.

## Next engineering step (gated on this freeze)
Build a **SIM-only Sierra Chart ACSIL** study to forward-paper this exact rule with pre-live controls
(max-loss cap, time-window guard, kill switch, audit log, no real orders). Design TBD (surprise-input
mechanism, control scaffolding).
