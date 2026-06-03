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

### C2 — Overnight drift (close-to-open vs open-to-close), ES/NQ · **VERDICT: NULL** · 2026-06-03
Overnight long is positive on average but Sharpe 0.3–0.8 and **t < 1.2** (ES OOS≥2024 +$71.64/day t=0.93;
NQ +$164/day t=1.15) — far from |t|>3, and essentially long beta. **2026 YTD reversed hard negative**
(ES −7.3pt, NQ −31.7pt overnight/day). Unstable, insignificant, not alpha. Script:
`campaign/c2_overnight_drift.py`.

### C3 — Options VRP harvest (the highest-prior surviving category) · **BLOCKED: no data** · 2026-06-03
A risk *premium* (compensation for risk) survives OOS in a way prediction edges don't — the right target.
But: in-hand SPX 0DTE data is only a **90-second pin snapshot (15:58:30–15:59:59)** with ~zero time value
to sell → no VRP harvest possible. No VIX, no VIX futures, no full option chains in-hand or on the network
share. **No Databento API key exists** (every key file is 0 bytes; the `.env` "SPX_FLY_API_KEY" is a GitHub
PAT). So proper VRP / VIX-carry / diversified-TSMOM all require a paid data pull I cannot perform.

### ZB passive market-making — **project-adjudicated BLOCKED / non-deployable** (2026-05-23)
`reports/zb_passive_exit_deep_dive/branch_blocker_decision_*`: sparse exact-HFT fills, passive-exit
mechanism unvalidated, mixed-to-negative clean checkpoints, no live-latency evidence. Re-litigation
explicitly forbidden. Retail passive-MM vs HFT — not viable.

### C4 — VRP harvest via FREE tradeable data (PUTW / SVXY / VIX) · **VERDICT: NULL as an edge** · 2026-06-03
Bypassed the data wall using free daily ETF/index data. The VRP is **real** (VIX > forward-21d RV on
**83%** of days, mean +3.7 vol-pts). But harvesting it is **not alpha**: PUTW (put-write) Sharpe **0.68**
(0.77 OOS, maxDD −28%) **does not beat buy-and-hold SPY** (0.89 full / 0.75 OOS); SVXY (short-vol)
−95% maxDD (catastrophic); a pre-registered VIX-elevated conditioning overlay **hurt** (Sharpe 0.25 OOS).
The premium is compensation for crash risk ≈ equity beta. Script: `campaign/c4_vrp_freedata.py`.

## FINAL VERDICT (2026-06-03): no edge clears the bar
Across **every accessible category — in-hand AND free data** — no strategy both *passes scrutiny* (beats
buy-and-hold risk-adjusted / is clean alpha) AND *survives OOS*:
- **Prediction edges** decay OOS (C1 detector-forward, C2 overnight, MOC, DAT pattern zoo) — NULL.
- **Vol-forecasting** (v1 GEX/DIX) — KILL.
- **Risk-premium harvest** (C4 VRP) — premium real, harvest ≈ beta, conditioning refuted — NULL as edge.
- **Passive market-making** (ZB) — project-adjudicated non-deployable.
Empirical capstone of the session's opening prior: *almost every "options edge" is a risk premium, not
alpha.* Best OOS-surviving *tradeable* result is **PUTW** (Sharpe 0.77 OOS, maxDD −16.6%, lower-DD than
equity) — a defensible allocation but **not the edge the goal seeks** (it doesn't beat the index).
**What could change this:** genuinely un-mined data/markets (paid Databento options / VIX futures /
diversified futures) for a properly-conditioned VRP or diversified-TSMOM test — but C4 shows even the
clean VRP harvest is beta-dominated, so the prior on those is now also lower. Mining the exhausted data
further would manufacture false positives — forbidden by this lab's integrity rules.
