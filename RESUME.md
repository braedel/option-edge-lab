# RESUME — read this first

> ## ⛔ PROJECT CLOSED 2026-06-10 — see `CLOSEOUT.md`
> Final outcome: **no edge meeting the goal was validated; Sharpe>2 = verified NULL** on this data/latency.
> One deployable modest result (Study-1 TSMOM ~Sharpe 1.0 diversifier); one unvalidated ~30–40% hypothesis
> (**#1** macro-surprise, forward-paper *designed, not built*); everything else NULL. Full tally + the
> integrity story (the #1 "meets the bar" retraction after the freeze-violation audit) + disposition are in
> **`CLOSEOUT.md`**. Everything below is the (now-historical) working state.

## CLOSED 2026-06-09 — ZB MBO study = NULL (real signal, uncapturable)
A real OOS-robust directional signal exists (GBR IC_oos ~0.226) but is **not capturable for the goal**:
TAKER net ~−1.0t (predictable move ~0.1t ≪ ~1.13t cost); MAKER wins 64-69%/+0.87t median but mean net
−0.77/−1.02t (adverse-selection tail dominates — win-most-but-catastrophic-tail, same as Study-2). hftbacktest
harness NOT built (optimistic proxy already net-negative). Verdict:
`docs/research/results/2026-06-09-zb-mbo-verdict.md`; registry in `CAMPAIGN.md`. Would need true colocation.
**EVENTS (owner's NFP/FOMC/CPI thesis, tested 2026-06-09): also NULL** -- post-release continuation,
mid-based/ZERO-spread, 32 months: pooled ~0t, %cont~0.50, LOO sign-unstable at realistic >=5s entry; the
only signal is at +1s (NFP +8t continue / CPI -9t reverse, incoherent, decays by 5s) = the conceded
sub-second/colo window. Quant CONCUR-KILL; doc `docs/research/results/2026-06-09-zb-mbo-event-continuation-null.md`.
Data now mirrored local `D:\TradingData\databento\ZB` (loader honors `ZB_DATA_ROOT`; share is ~13 MB/s).
**Do not re-litigate single-instrument ZB microstructure (incl event variants -- PinFly trap); untested =
forward live/paper TCA only.**
**3-PATH GOAL (Stop-hook, 2026-06-09, c32-c53b) -- COMPLETE; outcomes:**
**#1 surprise-direction = UNVALIDATED post-hoc hypothesis (critical review 2026-06-09 RETRACTED the earlier
"meets the bar"):** enter -sign(surprise) at t+5min on BIG CPI + FOMC surprises, hold 60min. In-sample
reproduces exactly (c51/c55): **Sharpe ~1.25 (t=2.07, n=35)**, NET +$135/tr, %pos 0.57, maxDD ~$1,400 (chron;
$1,055 was wrong), positive all 3 yrs; legs CPI ~0.99/t1.64 + FOMC ~0.76/t1.25. **3-reviewer adversarial audit
(re-verified) found, BINDING:** (1) **FREEZE-VIOLATION** -- rule was frozen as CPI+NFP/FOMC-excluded (280909c),
OOS ran + went NEGATIVE (7b0b6ae), then NFP-dropped+FOMC-added 4min later (070c58d) -> **the CPI+FOMC rule was
NEVER OOS-tested;** "OOS not refuted/meets the bar" RETRACTED. (2) **fails MT** (t2.07 < Bonferroni ~3.3 over
~22 cells; deflated Sharpe ~0.34; underpowered MDE>effect). (3) **winner-driven** (2023 wins only 46%).
(4) FOMC = discretionary hand-label, no rubric (leakage risk). **BUT robustness (c55) reassuring:** survives
fill-sweep (Sh 0.96 @2t slip, +NET @3t), survives/improves dropping 8 contaminated events (Sh1.38), CPI-only
(mechanical) Sh0.99 so doesn't hang on FOMC, FOMC-only wins only 62% (not hindsight-fitted). **Honest status:
real reasonably-robust IN-SAMPLE signal, UNVALIDATED (~30-40% survives forward).** **CLEANUP DONE (path A):**
FOMC blind rubric re-classification = **21/22 match** (lone flip 2024-06-12 = +$90 winner, Sh1.25->1.23 --
labels NOT hindsight-fitted); all robustness passed. **Re-FROZEN v2**
`docs/research/specs/2026-06-09-zb-surprise-FROZEN-v2-postaudit.md` as an UNVALIDATED hypothesis w/ a strict
pre-registered forward kill-gate. **NEXT: build SIM-only Sierra Chart ACSIL** to forward-paper it (design TBD:
surprise-input mechanism + pre-live controls). Only a forward/sealed test can validate (power wall +
never-OOS-tested). Artifacts: dossier, `2026-06-09-fomc-blind-classification.md`, per_event_cpifomc.csv; c51/c55.
**#2 cross-instrument curve RV (ZN/ZF/ES) = NULL:** ZB~ZN+UB residual reversion looked Sharpe ~1.2/1.6 on a
FIXED in-sample beta but COLLAPSES with a deployable rolling beta (in-sample ~0.5, OOS-negative) = fixed-beta
artifact + near-unit-root + directional curve trend. databento curve ohlcv-1m pulled ($19). c46-c50.
**#3 OZB options to protect the trade = PRICED on real OZB quotes; BOTH structures FAIL (c52-c54), deploy
naked:** OZB data pulled+cached+validated. **(a) defined-risk REPLACEMENT** (option IN trade dir instead of
the future, c53/c53b): caps the tail (best ~1pt OTM maxDD $1,055->$326, worst -$473->-$144) BUT costs Sharpe
(naked 1.25 -> ~0.85). **(b) protective OVERLAY** (future + ADVERSE-side OTM put/call = the literal "protect
the downside" ask, c54): **strictly WORSE than naked on Sharpe AND Calmar at every offset (0.5-2.0pt OTM)
under both exit-marking bounds** -- even the generous bound (0.5 OTM: naked Sh+0.47 -> overlay +0.06). Why:
trade wins >50%, so you bleed premium on the majority of winners where the hedge expires OTM (+$871 win ->
+$9 after an $862 put); insured loss is modest (worst ~-$500); and the OTM strike STOPS being quoted ~30min
post-move (drifts off-money *because* the trade won) so a realistic exit lapses, which *raises* maxDD
($731->$4,292). Per-trade insurance is the wrong tool for a losing-streak DD (~$1k), not a per-trade blow-up.
**==> Deploy NAKED #1** (DD ~$1k fine on <=$15k); the c44 cheap-premium first cut was too optimistic. PinFly
engine `spx-0dte-pinfly-lab/src/spx_pinfly_lab/core/butterfly.py`; **databento key
`spx-0dte-pinfly-lab\databendto_key.txt`**; OZB quotes cached `D:\TradingData\databento\ozb`.
**==> Sharpe>2 = VERIFIED NULL on ZB futures at near-CME latency (confirms Study-2). Best honest result =
#1 (~1.25 in-sample, forward-paper-pending). Awaiting owner decision: forward-paper #1, or authorize a data
spend / infra change for a fresh direction (NOT more single-instrument ZB microstructure -- exhausted).**
Price-pattern angles (continuation/drift/pre-drift/breakout/maker-tailguard/intraday-MR) ALL NULL/2023-regime.
Campaign doc `docs/research/results/2026-06-09-zb-announcement-campaign.md`. Below = the (now-historical) build log.

## ACTIVE BUILD — ZB MBO selective-taker (branch `zb-mbo-taker`, since 2026-06-08)
Owner granted **100% autonomy + expert-subagent reviews** (route quant/code reviews to subagents, NOT the
owner — they are not a quant). Goal: an honest tradeable edge from ZB L3 MBO toward Sharpe>2 (deflated prior:
likely NULL; a documented ceiling is a valid result). **Do NOT fabricate >2.** Full context: auto-memory
`project_zb_mbo_taker.md`; spec `docs/research/specs/2026-06-08-zb-mbo-taker-design.md`; plan (v2, includes the
SWE-review corrections) `docs/research/plans/2026-06-08-zb-mbo-taker-plan.md`.

**Engine venv:** `.venv-mbo` (hftbacktest 2.4.4, numpy<2.3 — separate from main `.venv`). Tests:
`.venv-mbo\Scripts\python.exe -m pytest tests/zb_mbo tests/test_stats.py -q` (56 green).

**DONE & committed:** Phase 0 venv + real-data attestation (A1 clear=3 / A2 TRADE-vs-FILL side conventions / D1
dtypes / E Sum(TRADE)=Sum(FILL) volume oracle — ALL PASS on zb_2024-12). Phase 1 causal engine
`src/options_lab/zb_mbo/{codes,book,calendar,loader,stream}.py` (L3 per-order replay; section-2 roll calendar;
`eligible_days` gate excluding burned {2025-04,2025-10,2026-03,2026-04} + sealed {2025-11..2026-02}; per-trade
causal feature stream + B2 leak proof). Phase 2 `triggers.py` (vacuum/sweep/event, B3 oracles). Phase 4
`src/options_lab/research/stats.py` (DSR/PSR/PBO-CSCV/stationary-bootstrap/Holm/uniqueness).
**Calibration peek (2024-06):** engine OK on real data; pure-Python ~5s/1M events (~6s/trading-day → full census
~1–1.5h, NO numba needed); **K3 power gate CLEARED** (vacuum ~13–42/day, sweep ~2–3k/day → thousands/family) — so
the verdict hinges on **Stage-1/2 economics (the 1.1-tick cost hurdle)**, per the deflated prior.

**NEXT (resume here):** (1) Phase 3 `labeler.py` — latency-adjusted forward move from `t+latency`, excluding the
trigger's own prints, taker far-touch entry (review A5/B6/§7.x). (2) Freeze+commit `reports/zb_taker/grid.json`
+hash (G3) and the kill-gate table with exact K1–K10 numbers (G1). (3) `c20` full census over eligible days; `c21`
Stage-1 TRAIN-ONLY screen (K1 net>1.1 tick, K2 sign-stable, K3 ≥50 episodes). (4) Phase 6: hftbacktest probes
P1–P6 (A5/A6/A7/B6/C1) → Stage-2 + latency sweep + placebo → sealed-OOS one-shot → DSR/PSR/PBO verdict (K4–K10).
N_trials MUST include the 10 prior nulls + every Stage-1 cell (B4).

---

**Workspace:** `D:\workspace\options-edge-lab` (git &rarr; https://github.com/braedel/option-edge-lab).
**Python:** `D:\workspace\options-edge-lab\.venv\Scripts\python.exe` (full scientific stack) — run all analyses with it.

## ACTIVE GOAL (owner /goal, 2026-06-08)
> Create a tradeable strategy (options / futures / securities) with **Sharpe > 2**, profitable **most months**
> (give up no more than ~2/yr), **low drawdown**, runnable on **&le; $15k** capital.

A session Stop-hook enforces this. **Do NOT fabricate a >2** — see the deflated prior. Pursue it hard the
legitimate way; report only audited, verified numbers.

## DEFLATED PRIOR (carry this — it is the whole point)
A *robust* Sharpe > 2 (cost-real, leak-free, tail-included, OOS) is extraordinarily rare for retail. The goal's
**profile** (very high Sharpe + win-almost-every-month + low DD + small capital) is the textbook signature of
**short-volatility / option-premium selling**, whose lovely Sharpe **hides a catastrophic tail** (2018, 2020).
Hard evidence already in hand: the tradeable **PUTW** ETF (systematic put-selling) ran Sharpe **~0.7**, not >2.
No option-price data + **no data spend** &rarr; options strategies cannot be honestly backtested here.
**Verified ceiling is likely ~1–1.5.** A clean "lower than 2, here's why" is a valid result.

## STATUS
- **Study 1 — COMPLETE & pushed.** Diversified trend-following overlay + 60/40. After independent quant+eng
  audits and self re-verification, honest result = a **leak-free diversification overlay, Sharpe ~0.9–1.0**,
  that halves a 60/40's risk at ~equal return with crisis convexity — **NOT a 60/40-beating alpha** (not
  significant at 95%). Early "1.08 / >1 alpha / futures 1.07 / options-hedge lift" claims were artifacts,
  corrected. Deck: `docs/research/results/2026-06-03-trend-overlay-study-deck.html`; one-pager:
  `docs/research/results/2026-06-03-deployable-onepager.md`; registry: `CAMPAIGN.md`.
- **Study 2 — E1–E4 DONE, VERDICT REACHED & RE-VERIFIED (2026-06-08).** Charter+results+verdict:
  `docs/research/STUDY2-high-sharpe-target.md`. Scripts: c16 (ensemble **0.74**), c17 (short-vol: PUTW 0.68/
  −28%, SVXY 0.34/−95%, regime-filtered 0.27), c18 (pairs **−0.47**), c19 (crypto trend 1.41 full/**0.81 OOS**,
  but 42% pos-months). All 4 re-ran 2026-06-08, numbers replicate exactly, look-ahead audits = 0.00.
  **VERDICT: {Sharpe>2 + ≤2 losing-months/yr + low-DD + ≤$15k} is NOT achievable honestly on free data — the
  criteria are mutually contradictory.** Proof: ≤2 losing-months/yr ⇒ ≥83% positive months ⇒ Sharpe≈3.3
  (symmetric) OR negative skew = premium-selling = catastrophic tail. **Verified ceiling ~0.9–1.0** (Study-1
  trend overlay, already audited/deployable). **Awaiting owner decision (see NEXT STEPS).**

## CRITICAL METHOD LESSONS (from Study-1 audit — non-negotiable)
1. **Leak-free, PROVEN.** Every result passes a perturbation/truncation test (corrupt FUTURE data &rarr; PAST
   returns must not move). **No full-sample scaling** — it is look-ahead. Pattern in `campaign/c11_clean_verify.py`.
2. **Cost on ACTUAL levered turnover** (not pre-leverage) — `campaign/c12_audit_verify.py`. Add **short-borrow**
   on short legs (ETF proxy). Stress to 10 bps.
3. **Tail-inclusive DD** (bootstrap; one path understates it). **OOS** split + sub-periods. **Significance:**
   SE(Sharpe) &asymp; &radic;((1+0.5&middot;SR&sup2;)/years) &asymp; 0.3 over ~18 yr &rarr; "beats benchmark" needs a block-bootstrap.
4. **Independent audits, then RE-VERIFY them yourself** — subagents here have **fabricated** numbers (one audit's
   "0.67 @10bps" did NOT replicate; real 0.93). Always re-check in your own code.
5. Lead with the deflated prior; don't oversell.

## INFRA / DATA / HOW-TO
- **Reusable code:** `campaign/c5_tsmom.py` &rarr; `load(ticker)` (Yahoo JSON &rarr; daily adjclose Series),
  `sharpe`, `scale10`. `c11_clean_verify.py` = canonical leak-free trend+60/40 build + `audit()`. `c12` = audit
  re-verification. `c13`/`c14` = tearsheets. `c15` = deck generator.
- **Free data on disk:** `campaign/data/tsmom_*.json` = Yahoo daily for 21 ETFs (SPY QQQ IWM EFA EEM SHY IEF TLT
  TIP LQD HYG DBC USO UNG DBA GLD SLV VNQ UUP FXE FXY) + vix/spy/putw/svxy/gspc. Pull more free tickers:
  `Invoke-WebRequest "https://query1.finance.yahoo.com/v8/finance/chart/<T>?period1=1167609600&period2=1893456000&interval=1d" -Headers @{"User-Agent"="Mozilla/5.0"}` &rarr; save to `campaign/data/tsmom_<T>.json`.
- **No Databento key** (blank in `.env.txt`); **NO data spend**. In-hand SPX 0DTE = 90-sec close snapshot only
  (no morning option prices). Futures ES/NQ/YM 1-min live under `dat-trading-strategy-research` / `moc-signal-analysis`.
- **Git/GitHub:** `origin` = github.com/braedel/option-edge-lab (token-free URL; PAT in encrypted Windows cred +
  gitignored `.env.txt` &rarr; `OPT_EDGE_LAB_API_KEY`). `git -C D:\workspace\options-edge-lab push origin main` works.

## NEXT STEPS (Study 2 — awaiting owner decision, 2026-06-08)
The >2 goal is a verified NULL on free data. Owner to choose direction:
1. **Deliver the ~1.0 deployable** (recommended) — relax "win most months"; package the audited Study-1 trend
   overlay (Sharpe ~1.0, halves 60/40 risk, ≤$15k) as the real tradeable strategy. Only path that yields an
   actual tradeable result with no data spend and no fabrication.
2. **Write up the NULL** — document the verified result (criteria contradictory; ceiling ~1.0) as a Study-2
   result page/deck, mirroring Study-1's honest close.
3. **Spend on option data** — lift the no-spend constraint to test defined-risk option selling (the one path
   that *could* reach >2; but PUTW≈0.7 and a crash hits all positions at once).
4. **Keep hunting free data** — untested avenues (intraday ES/NQ 1-min, crypto funding carry). Low prior +
   multiple-testing risk: every new strategy on the same data raises the odds of a spurious >2.
