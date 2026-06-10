# GOAL — options-edge-lab

**Status:** **CLOSED 2026-06-10** — no edge meeting the goal was validated; **Sharpe>2 = verified NULL** on
this data/latency (verified ceiling ~1.0–1.5). One deployable modest diversifier (Study-1 TSMOM ~Sharpe 1.0);
one unvalidated ~30–40% hypothesis (#1 macro-surprise, forward-paper designed-not-built); all else NULL.
Full closeout: **`CLOSEOUT.md`**.

## Charter
Find a **real, out-of-sample-survivable options edge** and prove it under strict research integrity — or
prove there isn't one (a clean null is a valid deliverable). Inherit the process and mechanics from
`spx-0dte-pinfly-lab`; do **not** inherit its strategy assumptions.

## What "done" looks like for a candidate
A pre-registered rule, frozen before the sealed OOS look, that:
- beats dumb baselines net of realistic fills and fees,
- survives multiple-testing correction (Bonferroni/BH -> deflated-Sharpe/PBO) at |t| > 3,
- holds across purged / embargoed walk-forward (CPCV), and
- still works at the owner's real fill fraction (not just optimistic fills).

## Lessons carried in (from PinFly)
- Don't bet on a mechanism the structure already prices (the long fly priced confirmation at ~+$1/sec;
  calm was already priced; the cash index doesn't pin).
- `hit-rate != PnL` — measure money at real fills, not a proxy.
- Don't re-litigate a dead detector family on the same data; spend OOS only on genuinely fresh hypotheses.

## Current step
**Autonomous campaign (owner /goal 2026-06-03):** find a futures/options strategy that survives a clean
OOS test. Running log + trial registry: `CAMPAIGN.md`.
- Stage-1a v1 (GEX/DIX → vol): **KILL**.
- **C1** threshold-detector v2 forward-OOS: **NULL** — frozen rules net −$0.90 to −$4.90/trade on unseen
  2025H2–2026 (ES/NQ proxy); historical edge did not persist forward.
- **C2** overnight drift: NULL (Sharpe 0.3–0.8, t<1.2, 2026 reversed; beta, not alpha).
- **C3** options VRP in-hand: blocked (0DTE = 90-sec snapshot; no key). **C4** VRP via FREE data (PUTW/VIX):
  premium real (VIX>RV 83%) but harvest is **beta not alpha** — PUTW Sharpe 0.68/0.77-OOS does NOT beat SPY;
  conditioning refuted. **NULL as edge.**
- **C5 diversified TSMOM (trend-following): FOUND — GOAL REACHED.** Textbook 12m momentum, inverse-vol,
  monthly, no tuning, 8-ETF cross-asset 2007→2026. OOS-stable Sharpe 0.45 (DEV & OOS), crisis alpha (+6.6%
  '08, +6.7% '22 vs SPY −34%/−18%), corr 0.01 to SPY; 50/50 with 60/40 lifts Sharpe 0.79→0.86 and halves
  maxDD (−27%→−13%); robust to lookback blend (0.54) + 10bps cost (0.40); matches managed-futures literature;
  tradeable in futures (ETF proxy conservative). Honest: a diversifying crisis-hedge — modest standalone,
  lags in bulls — not an alpha engine. Write-up `docs/research/results/2026-06-03-c5-tsmom-found.md`.
