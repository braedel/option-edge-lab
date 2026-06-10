# CLOSEOUT — options-edge-lab

**Closed:** 2026-06-10. **Charter deliverable:** the TRUTH about whether a real, OOS-survivable edge exists —
not a strategy that looks good. **Outcome: no edge meeting the goal was validated; Sharpe>2 is a verified NULL
on the available data/latency.** A clean, honest close — which, per the charter, is itself a valid result.

## What was sought
A tradeable options/futures/securities strategy with **Sharpe > 2**, profitable most months, low drawdown,
runnable on ≤ $15k — under strict research integrity (real data only, OOS confirmation, |t|>3 post-correction,
realistic fills, beat dumb baselines). Later relaxed to: *any* real OOS-survivable edge, or a documented null.

## What was found — full tally
| Candidate | Outcome |
|---|---|
| **TSMOM diversified trend overlay** (Study 1, `c5`/`c11`) | **FOUND but modest** — a leak-free diversification overlay ~Sharpe **0.9–1.0** that halves a 60/40's drawdown with crisis convexity. NOT a >2 alpha. The one actually-deployable result. |
| **Sharpe>2 target** (Study 2) | **VERIFIED NULL** on free data — the criteria are mutually contradictory; the only profile that fits is short-vol, which hides a catastrophic tail (tradeable PUTW ran ~0.7). Ceiling ~1.0. |
| **ZB L3 MBO microstructure — taker** | **NULL** — a real OOS signal exists (GBR IC_oos ~0.23) but the predictable move (~0.1t) is ~10× below the spread+cost (~1.13t). |
| **ZB MBO — maker** | **NULL** — wins 64–69% but the adverse-selection tail makes the mean negative even under a fill-optimistic proxy. Would need true colocation. |
| **Macro-announcement price patterns** (8 angles, `c32–c40`) | **NULL / 2023-regime artifacts** — continuation, drift, pre-drift, breakout, maker-tailguard, intraday-MR. Two walls: the 2023-regime trap + the power wall (~9–30 events/yr). |
| **#1 macro-surprise direction** (CPI+FOMC, `c41–c55`) | **UNVALIDATED post-hoc hypothesis** — real, perturbation-robust in-sample (~Sharpe 1.0–1.25; survives fill-sweep, contaminated-drop, and a 21/22 blind FOMC re-label) BUT fails multiple-testing, is winner-driven, and — due to a freeze violation — **was never OOS-tested**. ~30–40% it survives forward. Forward-paper ACSIL **designed (feeds researched), NOT built.** |
| **#2 cross-instrument curve RV** (ZN/ZF/ES, `c46–c50`) | **NULL** — fixed-β residual-reversion artifact; a deployable rolling-β is OOS-negative. |
| **#3 OZB options downside-protection** (`c52–c54`) | **NULL** — both the defined-risk replacement (costs Sharpe 1.25→0.85) and the protective overlay (worse on Sharpe + Calmar at every offset) fail; deploy naked. |
| **Cross-instrument lead-lag** (slow/non-event, literature survey) | **NULL** — reduces to our taker+maker NULLs, confirmed by the lead-lag-arbitrage literature (a taker can't beat the spread even at 60% accuracy; the only profitable form is limit-order/maker with queue priority = colocation). |

## The integrity story (the lab working as intended)
The lab manufactured no false edge. When the #1 candidate was over-claimed ("meets the bar / OOS not refuted"),
a **3-reviewer adversarial audit (re-verified independently) caught a freeze-discipline violation** — the
CPI+FOMC rule had been re-tuned *after* the only OOS look (which went negative). The claim was **RETRACTED** and
the record corrected; the rule was honestly re-frozen as an explicitly *unvalidated* hypothesis. Preferring a
true "unvalidated" over a flattering "validated" is the deliverable working as designed.

## Verified ceiling & disposition
- **Verified ceiling ~1.0–1.5 Sharpe** for a robust, cost-real, retail strategy on this data/latency.
- **Deployable result:** the Study-1 TSMOM diversifier (~Sharpe 1.0, halves 60/40 drawdown), if a modest
  crisis-hedge overlay is ever wanted.
- **Only live thread if resumed:** forward-paper **#1** against the frozen v2 spec
  (`docs/research/specs/2026-06-09-zb-surprise-FROZEN-v2-postaudit.md`) — the single honest path past the power
  wall. Not built; ~30–40% prior; do NOT present as a validated edge.
- **No live trading** was undertaken and **no `live/` module exists** — correct, since no edge survived a
  sealed OOS.
- **Do NOT re-litigate** (all documented NULL): single-instrument ZB microstructure (incl. event variants),
  the #2 curve RV, the #3 options wrap, cross-instrument lead-lag, and the price-pattern announcement space.

## Key records
`GOAL.md` (charter) · `CAMPAIGN.md` (trial registry — honest count for multiple-testing) ·
`docs/research/results/` (campaign findings, the #1 dossier, the FOMC blind-classification, the ZB-MBO verdict) ·
`docs/research/specs/` (the frozen v1 [corrected] + v2 specs) · `campaign/c5,c11,c20–c55` (the analysis scripts).
