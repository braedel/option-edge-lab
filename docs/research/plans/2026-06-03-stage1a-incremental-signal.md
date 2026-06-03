# Stage-1a — Incremental-Signal Gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:executing-plans (inline) or
> superpowers:subagent-driven-development to implement task-by-task. Steps use `- [ ]` checkboxes.

**Goal:** Decide — on in-hand data only, before any spend — whether differentiated signals add
*incremental* predictive power over a crowded realized-vol baseline for the forward states short-vol
selling needs (a quiet tape, no down-move), under purged walk-forward CV with honest multiple-testing.

**Architecture:** A small `options_lab` research pipeline: load a daily panel → build no-lookahead
targets and features → fit nested models (baseline `B` vs `B ∪ D`) inside purged/embargoed walk-forward
folds → report the out-of-fold increment with a multiple-testing haircut and a minimum-detectable-effect
floor → emit a PASS / KILL / INCONCLUSIVE verdict. Staged by data cost (see below).

**Tech stack:** Python 3.12, numpy, pandas, scikit-learn, scipy, statsmodels, pytest, ruff. Data is
in-hand CSV/parquet under the three sibling labs; **no network, no new data pull** for v1.

**Spec:** `docs/research/specs/2026-06-03-conditioned-short-vol-stage1-design.md` (§ refs below).

---

## Data findings (from the 2026-06-03 inventory — ground truth for the executor)
- **`D:\workspace\spx-0dte-pinfly-lab\data\squeezemetrics_gex.csv`** — columns `date, price, dix, gex`;
  daily; **2011-05-02 → 2026-06-02** (3,794 rows). `price` = SPX close. This single file powers v1.
- **`...\data\official_settlement*.csv`** — official SPX settlements (train / 2025 / oos splits). Cross-check.
- **`...\data\processed\by_day\factor_YYYY-MM-DD.parquet`** — 1 row/day (2024+): `date, spot,
  realized_range_30m, realized_vol_30m, efficiency_ratio_30m, dom_skew, oi_concentration, pin_strength,
  settlement, ...`. v3 feature source.
- **`...\data\raw\by_day\anchor_YYYY-MM-DD.parquet`** — raw Databento MBP-1 SPX 0DTE tape
  (`ts_event, action, side, price, size, bid_px_00, ask_px_00, strike, right, mid`). 0DTE-gamma-proxy source (v3+).
- **DAT** `...\dat-trading-strategy-research\data\processed\databento\es_nq_volume_roll_1m\*.parquet` —
  back-adjusted 1-min ES/NQ (`timestamp, session_date, open..close, volume`). v2 source (crude flow / range).
- **MOC** `...\moc-signal-analysis\data\interim\moc_ohlcv_raw_alignment.parquet` — has **signed close-auction
  flow** `dBuy, dSell, sBuy, sSell, ...` + `es_forward_return_*`. v2 source (genuine order-flow imbalance).

## Staging (data-cost gated)
- **v1 (this plan):** signals `D = {gex, dix}` (lagged, as-of *t*) vs baseline `B` = trailing realized vol
  + recent return + calendar; targets forward RV & forward down-move; horizons h ∈ {1,3,5} trading days;
  sample = daily SPX 2011→ (pre-OOS). Pure CSV. **Honest caveat:** SqueezeMetrics GEX/DIX are
  retail-sold ⇒ *semi*-crowded; v1 screens whether the gamma/flow *idea* has legs on a long sample.
- **v2 (next plan, only if v1 ≠ KILL):** add genuinely-differentiated futures order-flow (MOC `dBuy/dSell`
  imbalance, ES range/flow) on 2019+; re-run the increment.
- **v3:** add 0DTE microstructure (`dom_skew`, `oi_concentration`, computed 0DTE-gamma proxy) on 2024+.

## File structure (create under `src/options_lab/`)
- `data/panel.py` — `load_daily_panel()` → tidy daily DataFrame (`date, spx_close, ret, gex, dix`), sorted,
  dedup, date-typed. One responsibility: in-hand CSV → clean daily frame.
- `research/targets.py` — `forward_realized_vol(ret, h)`, `forward_max_drawdown(close, h)`, and binary
  label helpers. No-lookahead by construction (uses only (t, t+h]).
- `research/features.py` — `baseline_features(panel)` (B) and `differentiated_features(panel)` (D), both
  strictly as-of *t* (D lags gex/dix by ≥1 day).
- `research/validation.py` — port & **generalize** PinFly `walk_forward_folds`: configurable `oos_start`
  (no hardcoded date), purge + embargo for the h-day label horizon.
- `research/incremental.py` — `incremental_skill(X_B, X_D, y, folds, task)` → out-of-fold ΔR² (continuous)
  / ΔAUC (binary), per-fold deltas, pooled t-stat, sign-consistency.
- `research/multiple_testing.py` — port PinFly haircut + `min_detectable_effect(n)`; BH/Bonferroni over
  the (target × horizon) grid.
- `research/stage1a.py` — orchestrate the grid, apply §6 decision rule, return a verdict table.
- `cli.py` — add `optlab stage1a` subcommand (prints the verdict table; writes `reports/stage1a_v1/`).
- Tests mirror each module under `tests/`.

---

## Task 1: Daily panel loader
**Files:** Create `src/options_lab/data/panel.py`, `tests/test_panel.py`.

- [ ] **Step 1 — failing test** (`tests/test_panel.py`): build a tiny CSV in `tmp_path` with
  `date,price,dix,gex` rows; assert `load_daily_panel(path)` returns a DataFrame with columns
  `["date","spx_close","ret","gex","dix"]`, `date` dtype datetime64, sorted ascending, `ret` =
  `spx_close.pct_change()` (first row `ret` is NaN), and duplicate dates dropped (keep last).
- [ ] **Step 2 — run, expect fail** (`ModuleNotFoundError`/`AttributeError`).
- [ ] **Step 3 — implement** `load_daily_panel(path: str|Path) -> pd.DataFrame`: read CSV, rename
  `price→spx_close`, parse `date`, `sort_values("date")`, `drop_duplicates("date", keep="last")`,
  `ret = spx_close.pct_change()`, return `["date","spx_close","ret","gex","dix"]`. Raise if `source`
  column present and any value ≠ "real" (integrity rule 1) — here there is none, so skip; assert non-empty.
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — characterization test on REAL file:** add `tests/test_panel_real.py` (skipped if the
  file is absent) asserting `load_daily_panel(SQZ_CSV)` has > 3000 rows and `date.min() < 2012`.
- [ ] **Step 6 — commit:** `feat(data): daily SPX/GEX/DIX panel loader`.

## Task 2: No-lookahead targets
**Files:** Create `src/options_lab/research/targets.py`, `tests/test_targets.py`.

- [ ] **Step 1 — failing test:** on a hand-built `ret`/`close` series, assert
  `forward_realized_vol(ret, h=3)` at index *t* equals the std of `ret[t+1..t+3]` × √252, is NaN in the
  last `h` rows, and uses **no** value at or before *t* (shift a single future point → only that row's
  label changes). Assert `forward_max_drawdown(close, h=3)` at *t* = `min over k∈(t,t+3] of
  close[k]/close[t] - 1` (≤ 0), NaN in last `h`.
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement** both as vectorized forward-window rolls (reverse-roll trick), returning
  pandas Series aligned to *t*; plus `low_vol_label(fwd_rv, q)` and `no_down_label(fwd_dd, thr)` binary
  helpers (label = favorable state). Document the (t, t+h] convention in the docstring.
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit:** `feat(research): no-lookahead forward RV + drawdown targets`.

## Task 3: Features (baseline B + differentiated D), as-of t
**Files:** Create `src/options_lab/research/features.py`, `tests/test_features.py`.

- [ ] **Step 1 — failing test:** assert `baseline_features(panel)` returns trailing realized vol at
  windows {5,10,21}, last-5d return, day-of-week one-hots — each row using only `ret[..t]` (the value at
  *t* and earlier). Assert `differentiated_features(panel)` returns `gex_lag1, dix_lag1` and `gex_z` =
  trailing-252 z-score of `gex_lag1`, all shifted so **no same-day gex/dix leaks** (row *t* uses *t-1*).
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement** with explicit `.shift(1)` on every D feature and rolling windows on B; return
  `(DataFrame, list_of_colnames)`. Add an assertion helper `assert_asof(df, panel)` used in the test that
  fails if any feature column correlates with a future-shifted ret more than the contemporaneous one
  (cheap leakage tripwire).
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit:** `feat(research): as-of-t baseline + differentiated features`.

## Task 4: Generalized purged walk-forward CV
**Files:** Create `src/options_lab/research/validation.py`, `tests/test_validation.py`.
Read first: `D:\workspace\spx-0dte-pinfly-lab\src\spx_pinfly_lab\research\validation.py` (port source).

- [ ] **Step 1 — failing test:** `walk_forward_folds(dates, n_splits=4, embargo=5, oos_start="2025-09-01")`
  yields expanding (train, test) folds, chronological; raises `ValueError` if any date ≥ `oos_start`;
  the last `embargo` train dates before each test block are dropped (purge for the h-day horizon).
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement** generalized version: `oos_start` is a **parameter** (default `None` = no
  seal), expanding window, embargo purge. Keep PinFly's structure; remove the hardcoded constant.
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit:** `feat(research): generalized purged walk-forward CV (configurable OOS seal)`.

## Task 5: Incremental-skill test (the core)
**Files:** Create `src/options_lab/research/incremental.py`, `tests/test_incremental.py`.

- [ ] **Step 1 — failing test (synthetic, decisive):** build `y = signal·D + noise` where `D` is a known
  column and `B` is pure noise. Assert `incremental_skill(X_B, X_D, y, folds, task="reg")` reports mean
  out-of-fold ΔR² > 0 with pooled `t` > 3 and sign-consistency = 1.0. Build a second case `y = f(B) +
  noise`, `D` = noise → assert ΔR² ≈ 0 and `|t|` < 2 (D adds nothing). 
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement:** for each fold, fit `M_B` on B and `M_BD` on `concat([B,D])` (Ridge for
  `task="reg"`, LogisticRegression for `task="clf"`; standardize on train only); collect out-of-fold
  predictions; per-fold Δ = skill(M_BD) − skill(M_B) (R²/ AUC); return mean Δ, pooled t-stat across folds
  (`mean/se`), per-fold signs, and the fold count. No fitting on test; no leakage across folds.
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit:** `feat(research): nested-model incremental-skill test`.

## Task 6: Multiple-testing haircut + MDE
**Files:** Create `src/options_lab/research/multiple_testing.py`, `tests/test_multiple_testing.py`.
Read first: `D:\workspace\spx-0dte-pinfly-lab\src\spx_pinfly_lab\research\multiple_testing.py`.

- [ ] **Step 1 — failing test:** `bh_adjust(pvals)` matches a hand-computed Benjamini-Hochberg example;
  `min_detectable_effect(n, alpha=0.05, power=0.8)` returns the expected order of magnitude for a known n.
- [ ] **Step 2 — run, expect fail.** **Step 3 — implement/port** (BH + Bonferroni + MDE; keep PinFly's
  haircut if present). **Step 4 — run, expect pass.** **Step 5 — commit:** `feat(research): MT haircut + MDE`.

## Task 7: Stage-1a orchestrator + decision rule
**Files:** Create `src/options_lab/research/stage1a.py`, `tests/test_stage1a.py`.

- [ ] **Step 1 — failing test:** on a synthetic panel where D genuinely predicts T1 at h=1, `run_stage1a(...)`
  returns a tidy table (rows = target×horizon: `delta, t_stat, t_corrected, mde, sign_consistency,
  verdict`) and an overall verdict `"PASS"`; on a noise panel → `"KILL"`.
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement:** loop targets {T1 low-vol, T2 no-down} × h {1,3,5}; build folds (seal
  `oos_start`, embargo=h); call `incremental_skill`; collect grid; BH-correct across the grid; apply §6:
  PASS if any cell has sign-consistency ≥ 2/3 **and** `t_corrected` |t|>3 **and** delta>MDE; KILL if none;
  else INCONCLUSIVE. Return `(table, verdict)`.
- [ ] **Step 4 — run, expect pass.**
- [ ] **Step 5 — commit:** `feat(research): stage1a orchestrator + pre-registered decision rule`.

## Task 8: CLI + REAL run
**Files:** Modify `src/options_lab/cli.py`; create `tests/test_cli_stage1a.py`.

- [ ] **Step 1 — failing test:** `cli.main(["stage1a","--dry-run"])` returns 0 and prints the grid header.
- [ ] **Step 2 — run, expect fail. Step 3 — implement** `stage1a` subcommand: load real panel (path from
  `--gex-csv`, default the inventory path), run, print the verdict table, write `reports/stage1a_v1/table.csv`
  + a `verdict.md` stamped with dataset row-count + `git rev-parse HEAD` (provenance, integrity rule).
- [ ] **Step 4 — run, expect pass (unit).**
- [ ] **Step 5 — REAL RUN:** `optlab stage1a --train-end 2025-08-29` (seal 2025-09+). Capture the verdict
  table. **Do not** touch OOS. Commit the report: `chore(report): stage1a v1 verdict (<PASS|KILL|INCONCLUSIVE>)`.
- [ ] **Step 6 — write `docs/research/results/2026-06-03-stage1a-v1.md`:** the table, the verdict, the
  honest caveat (semi-crowded GEX/DIX), and the next-step recommendation (v2 vs stop).

---

## Self-review
- **Spec coverage:** §2 universe → Data findings + staging. §3 signals → Tasks 3 (D=gex,dix v1; futures/0DTE
  deferred to v2/v3, matching the spec's Stage-1a/1b split). §4 targets T1/T2 → Task 2 (T3 term-structure is
  Stage-1b, out of scope here, consistent). §5 test design → Tasks 4–6. §6 decision rule → Task 7. §8
  guardrails (no-lookahead, seal, provenance) → Tasks 2/3/4/8. §9 deliverables → Tasks 1–8. GEX-in-Stage-1a
  (owner) → satisfied via the in-hand SqueezeMetrics series (the disciplined "make", zero spend); computed
  0DTE proxy is deferred to v3 as the finer realization. Covered.
- **Placeholder scan:** none — every task has concrete files, code intent, and acceptance.
- **Type consistency:** panel columns `date, spx_close, ret, gex, dix` are used identically in Tasks 1→3→8;
  `incremental_skill(X_B, X_D, y, folds, task)` signature matches between Tasks 5 and 7; `walk_forward_folds`
  params match Tasks 4 and 7.
- **Scope:** v1 only; v2/v3 are explicitly separate plans. Single, runnable deliverable.
