# Design Spec — ZB MBO Selective-Aggressive (Taker) Microstructure Study

**Date:** 2026-06-08 · **Status:** DRAFT for owner review · **Candidate:** options-edge-lab campaign (ZB-taker)
**Process:** instantiates `docs/research/quant_research_process.md`; trial-registered in `CAMPAIGN.md`.
**Methodology authority:** the protocol in §6–§10 is the adopted output of a critical expert-quant review
(owner directive: route quant-process decisions to a critical expert quant and document to strict quant
principles). Where this spec and the process doc agree, the process doc governs; where the review tightens
it, the review governs.

---

## 1. Objective & honest framing

Test whether a **selective aggressive (taker)** strategy on **ZB (CME 30-yr Treasury futures) L3 MBO** data
can clear a **net > ~1.1-tick** hurdle per trade (1 tick = 1/32 = **$31.25**; cost = **$4 round-turn/contract**
plus spread) **often enough** to advance the standing goal: **Sharpe > 2, profitable most months
(≤ ~2 losing/yr ⇒ ≥ 83% positive months), low drawdown, runnable on ≤ $15k.**

**Deflated prior (carried, not re-litigated):** a separate project already ran 10 ZB micro-signal baselines
(top-imbalance, queue-depletion, depth-shape, order-age, flow-impulse, trade-burst, …); **all were
net-negative after the $4 cost**, best **gross** edge ≈ **0.13 tick** (≈ $3.93/ct, below cost), and its
in-sample-best cell **flipped sign out-of-sample** (verified in
`…/zb_mbo_marketable_imbalance_baseline/summary.json`). Naive passive provision filled ~10% with ~945
contracts queued ahead and is **project-blocked** (`CAMPAIGN.md`: "retail passive-MM vs HFT — not viable",
re-litigation forbidden). **Therefore:** generic micro-signal scanning is disproven; the only remaining hope
is **conditioning on rare, large-move contexts**, traded as a taker, under realistic latency.

**Success conditions (either is a valid deliverable):**
1. A **documented NULL** with the mechanism ("the honest ceiling is ≤ ~1.0–1.5 and here is exactly why"), or
2. A **genuine survivor** that clears the campaign-level multiple-testing bar, independently re-verified.

**This is not a retail study.** Production execution is **near-CME proximity (not colocated)**, **Denali L3**
market data + **Teton** order routing. We model that explicitly; we do not assume colo, and we do not assume
retail internet.

---

## 2. Strategy class & pre-registered signals

**Class:** selective aggressive **taker** — cross the spread **only** when a microstructure trigger predicts a
forward move large enough to beat ~1 tick of spread + $4 (≈ **>1.1 ticks net**). (Owner-selected; distinct
from the blocked passive-MM class and not a reconstruction of "MakerFlip".)

**Pre-registered trigger families (small, frozen set — original designs):**
- **A — Liquidity vacuum / book-thinning.** One side's near-touch displayed depth collapses below its rolling
  norm; the next aggression gaps several ticks before the book refills. *Thesis: thin book → large impact.*
- **B — Sweep / momentum ignition.** A marketable order consumes ≥ K price levels in a short window; trade the
  short continuation. *Thesis: liquidity-consuming aggression short-term continues.*
- **C — Scheduled-event window.** Treasury auctions (~13:00 ET), 08:30 ET releases, FOMC (14:00 ET): liquidity
  withdraws and post-event moves run many ticks over seconds–minutes; condition entry on the immediate
  post-event order-flow imbalance / first sweep direction.

**Grid (frozen & hashed before any data is touched):** families {A,B,C} × **≤ 3** economically-spaced
thresholds each × **≤ 3** horizons each (horizon tied to the trigger's physical half-life: sub-second for B,
seconds for A, seconds–minutes for C) × the latency sweep points. The integer `N_trials` is computed up front
and **includes the 10 prior nulls and every Stage-1-examined config** (§6.7). Fine grid search is forbidden.

---

## 3. Repository placement & reuse (owner directive: same process, reuse what exists)

New candidate **inside options-edge-lab**, reusing the existing disciplined process rather than re-inventing it.

**Reused as-is (tested):** `src/options_lab/research/`
- `validation.walk_forward_folds(...)` — purged/embargoed walk-forward folds.
- `multiple_testing.{bonferroni, bh_adjust, t_to_p, min_detectable_effect}` — FWER/FDR, p-conversion, power/MDE.
- `incremental.incremental_skill(...)` — does MBO order-flow add skill over a price-only baseline.
- `stage1a.run_stage1a(...)` — **driver pattern** for the Stage-1 screen (panel → targets × horizons × folds → stats).
- `targets.*`, `features.*` — **patterns** (new ZB labels/features added alongside, not edited).

**Reused process & registries:** `docs/research/quant_research_process.md` (its **Stage 1 = signal / Stage 2 =
economics** framing *is* this two-stage design), `CAMPAIGN.md` (honest trial registry / campaign-level
multiple-testing), `docs/research/{specs,results,plans}` layout.

**Added — small, tested extensions** to `multiple_testing.py` (or a new `stats.py`):
`deflated_sharpe_ratio(sr, n_trials, skew, kurt, n)`, `probabilistic_sharpe_ratio(sr, sr_benchmark=1.0, …)`,
`pbo_cscv(returns_matrix, S)`, `stationary_bootstrap(pnl, block_len)`.

**Added — new engine package** `src/options_lab/zb_mbo/`:
- `loader.py` — `.npz` reader + **causal L3 book replay** (ADD/CANCEL/MODIFY/DEPTH_CLEAR mutate; TRADE/FILL do
  not), per-order identity, `valid` flags, day/roll exclusion, provenance tags.
- `triggers.py` — detectors for families A/B/C (event-driven, causal).
- `labeler.py` — **latency-adjusted** forward-move labels (§7).
- `screen.py` — Stage-1 driver (reuses `validation` + `multiple_testing`).
- `backtest.py` — hftbacktest Stage-2 harness (run loop, poll, fills).
- `probes.py` — the mandatory hftbacktest probe suite (§9).
- Campaign scripts: `campaign/c20_zb_census.py`, `c21_zb_stage1_screen.py`, `c22_zb_stage2_hftbt.py`.

**Isolated venv** `D:\workspace\options-edge-lab\.venv-mbo` — required because the main `.venv`
(numpy 2.4.6 / pandas 3.0.3) **cannot** host `hftbacktest==2.4.4` (needs **numpy ≥2.0,<2.3**). Contents:
python 3.12 (or 3.11 if no cp312 hftbacktest wheel), numpy<2.3, pandas 2.2, scipy, statsmodels, scikit-learn,
numba, `hftbacktest==2.4.4`, databento, zstandard, and `pip install -e .` of `options_lab` (its deps allow
numpy≥1.26 / pandas≥2.2, so the research toolkit installs cleanly here). The main `.venv` is unchanged.
*Setup risk to verify in the plan:* availability of a prebuilt `hftbacktest` wheel for the chosen CPython.

---

## 4. Data

**Source (canonical):** spliced monthly `.npz` tapes at `\\10.0.0.13\d_drive\TradingData\databento\ZB\zb_YYYY-MM.npz`
(== `\\Desktop-f9popu5\d_drive\…`), **40 months, 2023-01 → 2026-04** (~60.6 GB incl. raw `.dbn.zst` + sidecars).
Built with a **calendar-deterministic rollover rule**; vendor continuous tapes are known-wrong at rolls and
are **not** used.

**Record schema (8 fields):** `ev` (uint64 packed action+flags), `exch_ts` (ns), `local_ts` (ns), `px`, `qty`,
`order_id`, `ival`, `fval`. **Action = `ev & 0xFF`:** 2=TRADE, 3=DEPTH_CLEAR, 10=ADD, 11=CANCEL, 12=MODIFY,
13=FILL. **Flags (high bits):** EXCH 0x80000000, LOCAL 0x40000000, BUY 0x20000000, SELL 0x10000000.
**tick_size = 0.03125.**

**Hard data rules (from the databento handling guide; non-negotiable):**
- **Bit-0 trap:** select actions by `(ev & 0xFF) == code`, **never** `(ev & 1)`. Import-time assert.
- **Side convention:** TRADE(2) flag = **aggressor** side; FILL(13) flag = **resting** side (opposite). Signed
  flow **branches on action code**; unit-tested with a known buy-aggressor case.
- **Causal book replay** from the daily `DEPTH_CLEAR` boundary; mid-session starts replay the prefix (no L2 seed).
- **Roll exclusion:** drop **expiration −3 .. +1 trading days** (owner-chosen conservative buffer) *after*
  splicing; trade only **native (non-spliced)** days; tag `event_source` on every row; honor the `valid` flag.
- **Excluded days:** the guide's 7 legitimate exclusions (5 supplier-degraded + 2 holidays) plus the roll buffer.

**Splits (decide & seal before looking — §1 of the process doc, tightened by review §2):**
- **Walk-forward** over the early span: train ≈ 12 mo → validate ≈ 3 mo, step 3 mo (~8 folds), **purged** by
  the max label horizon and **embargoed** by ≥ max(horizon, event-cluster length); whole event-days never split.
- **Sealed final OOS = last ~6 mo, touched exactly once at the very end.** **Excludes 2026-04, 2025-04,
  2025-10, 2026-03** — already **burned** by the prior baseline's train/test windows (verified). If a clean
  6-mo sealed block cannot be formed from unburned months, reduce it and **document** the reduction.

---

## 5. Method — cheapest kill first (the run ordering)

1. **Event census** *(first; hours; cheapest kill).* Replay L3, detect {A,B,C} with the frozen thresholds,
   count **independent trigger episodes** per family per regime (after roll/exclusion). **< ~50 episodes/family
   in-sample ⇒ power-dead ⇒ STOP** with the underpowered-null memo. **Owner checkpoint: report census before
   building further.**
2. **Stage 1 — signal (TRAIN folds only).** Latency-adjusted forward-move screen (§7). Survive iff net
   E[favorable move] clears ~1.1 ticks with a **stable sign across folds** and ≥ ~50 episodes. Most/all families
   are expected to die here (prior says so) — by design, cheaply.
3. **hftbacktest probes (§9)** — must pass before any Stage-2 fill is trusted.
4. **Stage 2 — economics (survivors only).** hftbacktest L3 FIFO, **latency swept 0.1–5 ms** (must survive
   0.5–1.5 ms), $4 RT, adverse selection live (§8) → Sharpe, %-pos-months, maxDD, walk-forward OOS distribution.
5. **Placebo control (§10.6).** Time-shuffled / sign-flipped triggers must **lose** to the real trigger after
   deflation; otherwise the "edge" is mechanical/leak.
6. **Sealed-block one-shot unlock**, then the memo. Headline = **DSR + PSR(SR\*=1.0) + PBO(CSCV)**.

Stage-1 screens on **train only**; Stage-2/validation/sealed data is data Stage-1 **never saw** (kills
cross-stage selection leakage, §6.5). Trigger math/thresholds are **frozen** at end of Stage 1; Stage 2 changes
only execution realism.

---

## 6. Multiple-testing / overfitting control

- **6.1** Pre-register & **hash** the exact grid (§2); `N_trials` fixed before data.
- **6.2** Trial budget tied to **events, not compute**: target ≥ ~50 independent episodes per Stage-2 config.
- **6.3** ≤ 3 economically-spaced thresholds per family; **no fine grid search**.
- **6.4** **Deflated Sharpe Ratio** (Bailey–López de Prado) as the headline gate, using true `N_trials`, the
  cross-trial Sharpe variance, and the strategy's skew/kurtosis (HFT P&L is fat-tailed / negatively skewed).
- **6.5** **PBO via CSCV** (combinatorially-symmetric CV over WF blocks); **kill the whole study if PBO > ~0.5.**
- **6.6** Error-rate regime: **FWER (Holm-Bonferroni)** across the 3 primary families; **FDR (BH)** within a
  family's correlated threshold/horizon sub-grid.
- **6.7** **Cumulative across the program:** include the 10 prior null baselines and every Stage-1-examined
  config in the deflation count (multiple testing is per-program, not per-notebook).
- **6.8** **Researcher-DoF quarantine:** triggers/grid defined blind to OOS; the sealed unlock is a separate,
  logged, one-shot action; no "one more threshold" after any OOS peek.

---

## 7. Leakage controls (L3 + latency specific)

- **7.1** Two timestamps per episode: `t_signal` (last event feeding the trigger) and
  `t_decision = t_signal + one_way_latency`. **Signal uses only events with `exch_ts ≤ t_signal`.** Forward move
  is measured from **`t_decision`**, not `t_signal` (measuring from `t_signal` steals the latency window).
- **7.2** **Exclude the trigger's own prints** from the forward move: `forward_window.start > t_last_trigger_event`.
- **7.3** Book reconstruction causality: ADD/CANCEL/MODIFY/DEPTH_CLEAR mutate; TRADE/FILL do not.
- **7.4** Same-`exch_ts` ties resolved by a deterministic causal order (engine `correct_event_order()` split).
- **7.5** Event-driven detection (not snapshot-grid); label clock = signal clock.
- **7.6** Side-convention (§4) and bit-0 (§4) traps enforced and unit-tested.
- **7.7** Roll exclusion + lineage tags (§4); trade only `valid`, native, non-roll days.
- **7.8** Stage-1 cost honesty: taker entry = the **far touch you'd cross** at `t_decision` (pay the offer to
  buy), exit = the touch you'd cross to flatten; not mid±½spread.
- **7.9** Touch-persistence pre-screen: a touch must persist ≥ the latency window in replay before it counts as
  crossable (a cheap adverse-selection proxy ahead of Stage 2).

---

## 8. Execution / fill realism (taker)

`$4 + L3-FIFO-at-touch` is **not** sufficient on its own; the dominant risk is **adverse selection** — a taker
keyed on momentum/vacuum crosses exactly as informed flow moves price, so the lifted liquidity is the liquidity
most likely to flee.
- **8.1** Adverse selection is realized via real L3 + latency in hftbacktest (the book moves during the latency
  window). We **verify** this with probe P2 (§9) and report the **slippage distribution**, not just the mean.
- **8.2** **Latency sweep 0.1–5 ms**; report **edge-vs-latency**; require survival at the realistic **0.5–1.5 ms**.
- **8.3** 1-lot uses `no_partial_fill_exchange()`. Any config wanting > 1 contract must switch to a partial-fill
  model and handle `PARTIALLY_FILLED`; own-order market impact is negligible at 1-lot but **re-flagged** on size-up.
- **8.4** Stage-1 assumed cost vs Stage-2 realized fill are reconciled; a large gap means Stage-1 was optimistic
  and its survivor set is suspect.

---

## 9. hftbacktest probe suite (mandatory before trusting any fill)

Synthetic hand-built L3 cases on the **same L3 path production uses**; assert **exact** integer-tick fill price
and timestamp:
- **P1** marketable cross fills at the touched tick, `exch_ts == submit + entry_latency`.
- **P2** quote cancelled during the latency window ⇒ fill at next price or no fill (adverse-selection mechanics live).
- **P3** a TRADE(2) with no FILL(13) does **not** fill a resting/marketable order.
- **P4** loop raises on `rc ∉ {0,1}`; a final post-loop fill sweep runs.
- **P5** no `_tick` index is ever passed where a price is expected.
- **P6** a synthetic buy-aggressor episode yields a long entry with correct signed P&L (ties to §7.6).
Also: keep a `NUMBA_DISABLE_JIT=1` path and confirm JIT-on == JIT-off P&L on a sample (engine-drift guard).

---

## 10. Significance, power, kill criteria

- **10.1** SR standard error with skew/kurtosis (Lo 2002 / Bailey-LdP); headline **PSR(SR\*=1.0)** — probability
  true Sharpe exceeds the **verified ~1.0 ceiling**, not zero.
- **10.2** **Minimum detectable effect / power:** compute the effective independent-N needed to separate SR=2
  from SR=1 at ~80% power from the realized moments; if 40 clustered months don't clear it, the honest result is
  "underpowered to confirm >2" (a valid null). Reuse `multiple_testing.min_detectable_effect`.
- **10.3** **Block / stationary bootstrap** on trade-level P&L with block length ≥ trigger autocorrelation/
  clustering length; CIs on Sharpe and on %-positive-months.
- **10.4** **%-positive-months ≥ 83%** tested on **effective** (not nominal 40) months; note ≤ ~7 total negative
  months are even observable in 3.3 yr, so one clustered bad regime can break it.
- **10.5** **Sample-uniqueness weights** (concurrency down-weighting) on clustered episodes in both the Sharpe
  estimate and the bootstrap.
- **10.6** **Placebo / time-shuffled / sign-flipped control** must lose to the real trigger after deflation.

**Pre-committed kill criteria (finalized to numbers in the plan before the first run):**
- **K1** Stage-1 net latency-adjusted E[move] < 1.1 ticks → drop.
- **K2** Sign unstable across folds → drop.
- **K3** < ~50 independent episodes (in-sample or OOS) → insufficient power → drop.
- **K4** Sealed-OOS DSR-implied p ≥ FWER budget → null.
- **K5** Sealed-OOS PSR(SR\*=1.0) < ~0.95 → cannot beat the ~1.0 ceiling → null for the >2 goal.
- **K6** Edge does not survive at 0.5–1.5 ms latency → null.
- **K7** Stage-1↔Stage-2 fill gap turns net P&L negative → null.
- **K8** PBO(CSCV) > ~0.5 → study null.
- **K9** All three families null → study null; deliver the "ceiling ≤ ~1.0–1.5, mechanism X" memo.
- **K10** Sealed block opens **once**; if peeked, it is spent — only forward paper/live TCA thereafter.

---

## 11. Deliverables

- This spec (committed) → implementation plan (`writing-plans`) → `campaign/c20–c22*.py` + `src/options_lab/zb_mbo/`.
- A result write-up in `docs/research/results/2026-06-08-zb-mbo-taker-<verdict>.md` with: trigger census;
  Stage-1 screen table; Stage-2 tearsheet (Sharpe, %-pos-months, maxDD, OOS, latency curve); DSR/PSR/PBO; the
  placebo comparison; the pre-committed kill decisions; and the deflated-prior accounting.
- `CAMPAIGN.md` registry entries (one per trigger family + the study verdict), feeding campaign multiple-testing.
- Provenance on every result: dataset version (file hashes + row counts), git commit, latency/cost params.

## 12. Integrity rules (hard — see `CLAUDE.md`)

Never tune on OOS (one look, at the end). Real fills + real fees. Log every trial/config (feeds the math).
Prefer fewer, monotone, pre-registered triggers. **A clean, documented "no edge" is a valid result.**
Subagent/engine numbers are independently re-verified (fabrication watch). Do **not** re-litigate the blocked
passive-MM class or the prior null micro-signals on this same data; untested ground is forward paper/live TCA.

---

## 13. Open items to finalize in the implementation plan

- Exact numeric thresholds for K1–K10 and the frozen grid (and its hash).
- The precise calendar anchor for the "expiration −3..+1" roll buffer (relative to last-trade / first-notice /
  the §4 calendar-deterministic roll date) — pin one definition so the excluded set is unambiguous.
- Exact sealed-block months given the burned-month exclusions.
- hftbacktest wheel/CPython choice and `.venv-mbo` lockfile.
- Whether `incremental_skill` is used to test MBO-flow-over-price as an explicit baseline.
- Census implementation cost (parallel per-month L3 replay) and runtime estimate.
