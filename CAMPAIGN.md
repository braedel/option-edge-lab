# Campaign Log — autonomous search for an OOS-surviving tradeable strategy

**Goal (owner /goal, 2026-06-03):** find a futures **or** options strategy that passes the quant process
and scrutiny and **survives a clean OOS test**. Full autonomy; integrity rules non-negotiable; a clean
null per candidate is a valid result; keep going until a genuine survivor is found, then notify owner.

**OOS discipline:** each candidate seals a recent holdout, develops on the rest (purged-CV), locks, then
ONE OOS look. This registry is the honest trial count for campaign-level multiple-testing — a survivor
must clear a Bonferroni/BH bar over *all* candidates tried, not just its own test.

## Prior art (surveyed — NULL, do not re-litigate)
- **PinFly 0DTE options** — NULL (the fly prices confirmation; cash index doesn't pin).
- **MOC close-auction futures** — NULL / non-deployable; April-2025-dominated; no fresh data (ends 2025-09).
- **options-edge-lab Stage-1a v1** (GEX/DIX → forward vol) — robust KILL (no incremental edge over realized vol).
- **DAT opening-drive pullback** — overfit / 2025-concentrated (NULL).

## Candidates
### C1 — Threshold-detector v2 forward-OOS · **VERDICT: NULL (fails forward)** · 2026-06-03
The best existing lead: 72 one-feature walk-forward rules, historically OOS-positive every year
(2023/24/25), beats matched-random p=0.0, but thin (+$2.35/trade, fails $6/RT). Test = apply the frozen
24 `test_year=2025` rules (trained 2022-2024) to the UNSEEN 2025-07→2026-03 window (ES/NQ proxy for
MES/MNQ; reproduction matched aggregate +~$2/trade but not per-year → proxy approximate).
**Forward 2025H2–2026Q1 (1,568 trades): −$0.90/trade @ $2, −$2.90 @ $4, −$4.90 @ $6 (win 50.1%).**
2026-only +$0.69 @ $2 but negative at realistic cost and one-month-dependent. The historical edge did
not persist forward. Script: `campaign/c1_threshold_forward_oos.py`.

### C2 — Overnight drift (close-to-open vs open-to-close), ES/NQ · **RUNNING** · 2026-06-03
Hypothesis: the documented overnight-return premium (most of the equity premium accrues overnight; the
intraday session is ~flat/negative). Low-turnover, cost-tolerant, in-hand (volume-roll 2019→2026).
Test = overnight vs intraday return decomposition by year + a sealed-OOS (DEV <2024, OOS ≥2024)
long-overnight strategy net of realistic cost, with t-stats. Script: `campaign/c2_overnight_drift.py`.
