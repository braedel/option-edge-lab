# ZB MBO Selective-Taker — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.
> **Spec:** `docs/research/specs/2026-06-08-zb-mbo-taker-design.md` (governs; read it first).
> **Reviews:** route engine code to a critical SWE reviewer and the plan/candidates to a critical quant
> reviewer (owner delegation). A clean documented NULL is a valid completion.

**Goal:** Determine — rigorously and leak-free — whether a selective-aggressive (taker) strategy on ZB L3 MBO
clears a net >1.1-tick hurdle often enough to approach Sharpe>2 / win-most-months, or document the honest
ceiling and why.

**Architecture:** A new `src/options_lab/zb_mbo/` engine (causal L3 replay → trigger detectors →
latency-adjusted labels → Stage-1 screen → hftbacktest Stage-2) plus small tested stats extensions in
`src/options_lab/research/`. Cheapest kills first: env/data sanity → **event census** → Stage-1 screen →
probes → Stage-2 → placebo → sealed OOS. Reuses the existing quant process, `validation`/`multiple_testing`
toolkit, `CAMPAIGN.md` trial registry, and `docs/research` layout.

**Tech Stack:** Python 3.12, numpy<2.3, pandas 2.2, numba, `hftbacktest==2.4.4`, scipy/statsmodels, pytest.
Isolated `.venv-mbo` (the main `.venv` numpy 2.4 can't host hftbacktest).

**Data:** `\\10.0.0.13\d_drive\TradingData\databento\ZB\zb_YYYY-MM.npz` (40 mo, 2023-01..2026-04). Record:
`ev,exch_ts,local_ts,px,qty,order_id,ival,fval`. Action=`ev&0xFF` (2 TRADE,3 DEPTH_CLEAR,10 ADD,11 CANCEL,
12 MODIFY,13 FILL). Flags: EXCH 0x80000000, LOCAL 0x40000000, BUY 0x20000000, SELL 0x10000000. tick 0.03125
($31.25). Cost $4 RT. Latency 0.5-1.5 ms (sweep 0.1-5 ms).

---

## v2 — BLOCKING review corrections (apply these; they OVERRIDE the task text below where they conflict)

A critical SWE review (2026-06-08) found defects that could produce silently-wrong results or a false
positive. Apply ALL of the following. Foundation (attestation) first, then leakage/multiple-testing, then
engine fidelity, then feasibility.

**Reuse corrections (verified against the real code):**
- `walk_forward_folds(dates, n_splits, embargo, oos_start)` embargoes by **row count of `dates`**, not time
  (`validation.py:36`). → Pass `dates` = list of **eligible trading DAYS**; `embargo` in **days** =
  ceil(max_H_days)+ceil(cluster_days), min 1. Handle **intraday** label overlap with a separate purge in the
  labeler (drop episodes whose `[t_decision, t_decision+H]` crosses the fold-boundary day).
- **Do NOT reuse `run_stage1a`** — hard-wired to a daily SPX vol panel (`stage1a.py:25-59`). Stage-1 uses
  `walk_forward_folds` + `multiple_testing.*` + a **new** episode aggregator in `screen.py` (mean net ticks vs
  the 1.1-tick hurdle). `incremental_skill` is reserved for the optional, separately-registered
  "MBO-flow-over-price" nested check (off the critical path).
- `multiple_testing.py` has **no Holm, no DSR/PSR/PBO** → add `holm()` + DSR/PSR/PBO/stationary-bootstrap/
  uniqueness-weights in new `research/stats.py` (Phase 4).

**Foundation — attest on REAL data before any dependent code (Task 0.2 = hard gate):**
- **A1 action-code spaces:** raw npz uses databento packing (**3=DEPTH_CLEAR**); the hftbacktest engine's
  processed array uses a DIFFERENT enum (**DEPTH=1**, no 3). `book.py` replays the RAW npz (clear=3); the
  Stage-2 engine path sees the PROCESSED enum. Attest the raw low-byte histogram (assert 3 present; record
  1/2/10/11/12/13) and never conflate. Add a 6.1 probe that the post-`correct_event_order` reset code matches
  what the harness expects.
- **A2 + the killer oracle (E):** do NOT bake the TRADE/FILL side sign into a unit test as truth. ATTEST on a
  real day: **Σ FILL qty == that day's `ohlcv-1d` volume within [0.90,1.10]** (databento §5) AND signed-FILL
  flow sign matches the day's price drift. Validates action-decode, bit-0 avoidance, FILL selection, side
  convention, qty dtype in one shot. Only then is the synthetic `signed_flow` test legitimate. (If `ohlcv-1d`
  isn't on the share, use an order-of-magnitude ZB front-month sanity band + price-drift sign, and document.)
- **D1 dtypes:** assert exact dtypes (`ev` u64, `exch_ts/local_ts` i64 ns ~1e18, `px/qty` float, `order_id`
  u64). Field-name membership is not enough.

**Leakage / multiple-testing / effective-N (false-positive routes):**
- **B4 N_trials wiring:** compute the EXACT integer `N_trials` from the frozen grid + 10 prior nulls + every
  Stage-1-examined cell → `reports/zb_taker/n_trials.json` with the arithmetic; test
  `len(registry)+10 == N_trials` passed to DSR; Task 6.4 fails closed on mismatch.
- **B5 eligible_days() gate:** single loader entry point subtracting {roll buffer, 7 guide exclusions, burned
  months 2026-04/2025-04/2025-10/2026-03, sealed block}; census/Stage-1/Stage-2-dev use ONLY this; test
  `eligible ∩ sealed = ∅` and `∩ burned = ∅`; per-day cache key records the eligibility tag.
- **G2 concurrency/uniqueness weights (spec §10.5):** López de Prado uniqueness per episode; apply to the
  Sharpe estimate, %-pos-months effective-N, and bootstrap block length (≥ cluster length); test two
  fully-overlapping episodes → weight ≈0.5 each.
- **G1 kill-gate table:** finalize K1-K10 numbers + application order + map each to its stats fn (Holm across
  the 3 families; BH within a family's sub-grid; DSR/PSR/PBO) BEFORE Task 5.1.
- **G3 grid pre-registration:** emit + commit `reports/zb_taker/grid.json` + hash at end of Phase 0; every
  campaign script asserts live-grid-hash == committed-hash at startup.

**Engine fidelity (make Stage-2 P&L real, not believable-wrong):**
- **C1** `correct_local_timestamp` THEN `correct_event_order` (both mergesort argsorts), not just the latter.
- **A5** P1 asserts fill PRICE at exact integer-tick equality but TIMESTAMP as
  `submit+L ≤ exch_ts < submit+L+step` (step pinned) + determinism across runs — not exact-point equality.
- **A6** each day's engine array starts at the 00:00 UTC DEPTH_CLEAR; if acting in a sub-window,
  `elapse(session_start − reset_ts)` first (Sample D); probe that a resting order survives the fast-forward.
- **A7** loader keeps the session-open reset row first within its snapshot group while failing every OTHER
  backward `exch_ts` jump; test a hand-built inverted boundary.
- **B6** P2 = touched level cancelled/repriced strictly inside `[submit, submit+L]` → assert fill at the worse
  next level (exact adverse tick) or no fill. K7 hard gate if realized−assumed slippage flips net P&L negative.
- **C3** Task 0.1 guard also asserts the live `Status.FILLED` spelling and `ev` bitflag integers.
- **C4** JIT-parity via a subprocess with `NUMBA_DISABLE_JIT=1` set BEFORE import; assert determinism.
- **C2** harness structurally forbids `modify`; triggers precomputed offline so `last_trades()` isn't needed
  in-engine (else implement the watermark dedup).

**Correctness oracles (kill tautologies):**
- **B1** BookState: price-changing MODIFY (cross-level move), ADD-on-existing-id, MODIFY/CANCEL-on-unknown-id
  (drop-safe, counted) — test each.
- **B2** leak proof perturbs the future event STREAM (delete future ADD/CANCEL, shuffle future order_ids,
  inject future FILLs) and asserts every causal **feature/label** (not just best_bid/ask) at each pre-cut t is
  bit-identical — run this gate downstream of triggers AND labeler.
- **B3** trigger oracles: boundary battery (threshold±ε), an independent-method numeric trace of the
  trailing-window feature, and a causality assert (a future event doesn't change `t_signal`).
- **E** stats numeric oracles: a worked-example DSR value (not just monotonicity) and a bootstrap calibration
  check (nominal 90% CI covers ≈90% over AR(1) draws).
- **D2** roll anchor pinned to the databento §2 calendar rule; test ALL 14 transitions exclude exactly the
  intended window. **D3** test an invalid (`valid==False`) row never reaches a label.
- **G4** `zb_events.csv` windows stored UTC-resolved; test a known FOMC date on both sides of a DST change.

**Feasibility (so a headless run finishes):**
- **F3** every campaign script first asserts `\\10.0.0.13` reachable + target-month file hashes match
  provenance sidecars; fail fast. CONSIDER staging eligible npz to local `D:` (hashed) to remove the SPOF.
- **F1** decide numba for `book.py` UP FRONT (profile one real day; JIT if >~2 min/day); census uses a coarse
  first pass (near-touch depth + sweeps) with full-book reconstruction only inside candidate windows.
- **F2** measure per-day peak RSS; `n_workers = min(cpu−2, floor(mem_headroom/per_day_peak))`;
  `ProcessPoolExecutor(initializer=warm_jit)`.

---

## File structure (created/modified)

```
src/options_lab/zb_mbo/__init__.py          # package
src/options_lab/zb_mbo/codes.py             # action/flag decode, signed-flow (pure, TDD-heavy)
src/options_lab/zb_mbo/book.py              # L3 BookState replay (per-order identity)
src/options_lab/zb_mbo/loader.py            # npz load, day-window, roll-exclusion, valid flags, provenance
src/options_lab/zb_mbo/calendar.py          # roll dates + event schedule (auctions/08:30/FOMC)
src/options_lab/zb_mbo/triggers.py          # A vacuum, B sweep, C event detectors (causal, event-driven)
src/options_lab/zb_mbo/labeler.py           # latency-adjusted forward-move labels
src/options_lab/zb_mbo/screen.py            # Stage-1 driver (uses validation + multiple_testing)
src/options_lab/zb_mbo/backtest.py          # hftbacktest harness (build, run loop, poll, fills)
src/options_lab/zb_mbo/probes.py            # P1-P6 synthetic fill probes + JIT-parity
src/options_lab/research/stats.py           # DSR, PSR(SR*), PBO-CSCV, stationary bootstrap (new)
campaign/c20_zb_census.py                   # event census (cheap kill gate)
campaign/c21_zb_stage1_screen.py            # Stage-1 latency-adjusted screen
campaign/c22_zb_stage2_hftbt.py             # Stage-2 hftbacktest + placebo + sealed OOS
tests/zb_mbo/test_*.py                      # one test module per engine file
tests/test_stats.py                         # tests for research/stats.py
```

**Conventions:** follow existing repo style (type hints, focused functions, pytest). All randomness seeded.
Every result stamps dataset file hashes + row counts + git commit (process doc §7 provenance).

---

## Phase 0 — Environment & data sanity (gate: imports + real-data schema confirmed)

### Task 0.1: Create and verify `.venv-mbo`

**Files:** Create `.venv-mbo/` (gitignored), `requirements-mbo.txt`.

- [ ] **Step 1:** Write `requirements-mbo.txt`:
```text
numpy>=2.0,<2.3
pandas>=2.2,<2.3
scipy>=1.12
statsmodels>=0.14
scikit-learn>=1.4
numba>=0.60
hftbacktest==2.4.4
databento
zstandard
pytest>=8
```
- [ ] **Step 2:** Create venv with a 3.12 base interpreter and install:
Run (PowerShell): `py -3.12 -m venv D:\workspace\options-edge-lab\.venv-mbo`
then `D:\workspace\options-edge-lab\.venv-mbo\Scripts\python.exe -m pip install -r requirements-mbo.txt`
then `…\.venv-mbo\Scripts\python.exe -m pip install -e D:\workspace\options-edge-lab`
Expected: all install; if no `hftbacktest` cp312 wheel, retry venv with `py -3.11`/`py -3.13` and record which works.
- [ ] **Step 3:** Constant-drift guard test `tests/zb_mbo/test_env.py`:
```python
def test_hftbacktest_constants():
    from hftbacktest import GTC, LIMIT, MARKET, GTX
    assert (GTC, LIMIT, MARKET, GTX) == (0, 0, 1, 1)  # verify vs installed version; update if drift
def test_numpy_compat():
    import numpy as np; assert np.__version__ < "2.3"
```
- [ ] **Step 4:** Run: `…\.venv-mbo\Scripts\python.exe -m pytest tests/zb_mbo/test_env.py -v` → PASS.
- [ ] **Step 5:** Add `.venv-mbo/` to `.gitignore`; commit `requirements-mbo.txt` + test.
```bash
git add requirements-mbo.txt tests/zb_mbo/test_env.py .gitignore
git commit -m "build: isolated .venv-mbo for hftbacktest engine + constant guard"
```

### Task 0.2: Real-data schema attestation (grounds the loader)

**Files:** Create `campaign/c20_zb_census.py` (stub `inspect_month()`), `tests/zb_mbo/test_loader_smoke.py`.

- [ ] **Step 1:** Write `inspect_month(npz_path)` that `np.load`s one file, returns dtype field names, an
  action-code histogram via `(ev & 0xFF)`, count of DEPTH_CLEAR per UTC day, and min/max `exch_ts`.
- [ ] **Step 2:** Smoke test (uses the smallest real file, `zb_2024-12.npz`):
```python
def test_npz_schema_and_actions():
    info = inspect_month(r"\\10.0.0.13\d_drive\TradingData\databento\ZB\zb_2024-12.npz")
    assert set(["ev","exch_ts","local_ts","px","qty","order_id"]).issubset(info["fields"])
    h = info["action_hist"]
    assert h.get(13,0) > 0 and h.get(2,0) > 0 and h.get(10,0) > 0   # FILL, TRADE, ADD present
    assert info["depth_clear_days"] >= 18                            # ~daily resets in the month
```
- [ ] **Step 3:** Run it (`.venv-mbo` python) → PASS. If schema differs from the spec, STOP and reconcile
  (do not proceed on assumed fields). Record the true dtype in a comment.
- [ ] **Step 4:** Commit `inspect_month` + test.
```bash
git add campaign/c20_zb_census.py tests/zb_mbo/test_loader_smoke.py
git commit -m "feat(zb): npz schema attestation on real data"
```

---

## Phase 1 — Causal L3 replay (gate: book correctness + leak-free proof)

### Task 1.1: Action/flag decode + signed-flow (`codes.py`)

- [ ] **Step 1:** Failing tests `tests/zb_mbo/test_codes.py`:
```python
import numpy as np
from options_lab.zb_mbo.codes import action, is_buy, is_sell, signed_flow, ACT
def test_action_low_byte():
    assert action(np.uint64(0x80000000 | 13)) == 13   # not the bit-0 trap
def test_bit0_trap_guard():
    # action 11 (CANCEL) has bit0 set, action 2 (TRADE) does not — prove we don't use ev&1
    assert action(np.uint64(11)) == 11 and action(np.uint64(2)) == 2
def test_signed_flow_trade_vs_fill_opposite():
    BUY, SELL = np.uint64(0x20000000), np.uint64(0x10000000)
    # TRADE(2): flag = aggressor. BUY-aggressor -> +qty
    assert signed_flow(np.uint64(2) | BUY, 5.0) == +5.0
    # FILL(13): flag = resting (opposite). SELL resting hit -> buy aggressor -> +qty
    assert signed_flow(np.uint64(13) | SELL, 5.0) == +5.0
```
- [ ] **Step 2:** Run → FAIL (module missing).
- [ ] **Step 3:** Implement `codes.py`:
```python
import numpy as np
ACT = {"TRADE":2, "CLEAR":3, "ADD":10, "CANCEL":11, "MODIFY":12, "FILL":13}
BUY_BIT, SELL_BIT = np.uint64(0x20000000), np.uint64(0x10000000)
def action(ev): return int(ev) & 0xFF
def is_buy(ev):  return bool(int(ev) & int(BUY_BIT))
def is_sell(ev): return bool(int(ev) & int(SELL_BIT))
def signed_flow(ev, qty):
    a = action(ev)
    if a == ACT["TRADE"]:   return  qty if is_buy(ev)  else -qty   # flag = aggressor
    if a == ACT["FILL"]:    return  qty if is_sell(ev) else -qty   # flag = resting (opposite)
    return 0.0
```
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit.

### Task 1.2: L3 `BookState` replay (`book.py`)

**Interface (define here, TDD the body):**
```python
class BookState:
    def __init__(self): ...
    def apply(self, ev, px, qty, order_id) -> None: ...   # ADD/CANCEL/MODIFY/CLEAR mutate; TRADE/FILL no-op
    def best_bid(self) -> float | None
    def best_ask(self) -> float | None
    def depth(self, side: str, levels: int) -> list[tuple[float,int]]   # [(px, qty), ...] top N
    def n_orders(self) -> int
```

- [ ] **Step 1:** Failing test `tests/zb_mbo/test_book.py` — replay a hand-built event list and assert state:
```python
def test_add_cancel_modify_and_touch():
    b = BookState()
    b.apply(ev_add_bid, 110.00, 7, oid=1)      # ADD bid 7 @110.00
    b.apply(ev_add_bid, 110.00, 3, oid=2)      # ADD bid 3 @110.00  -> depth 10
    b.apply(ev_add_ask, 110.03125, 4, oid=3)
    assert b.best_bid() == 110.00 and b.best_ask() == 110.03125
    assert b.depth("bid",1) == [(110.00, 10)]
    b.apply(ev_modify, 110.00, 2, oid=1)       # MODIFY oid1 qty 7->2 -> depth 5
    assert b.depth("bid",1) == [(110.00, 5)]
    b.apply(ev_cancel, 110.00, 0, oid=2)       # CANCEL oid2 -> depth 2
    assert b.depth("bid",1) == [(110.00, 2)]
    n = b.n_orders()
    b.apply(ev_trade, 110.00, 1, oid=0)        # TRADE: no book mutation
    b.apply(ev_fill,  110.00, 1, oid=1)        # FILL: no direct mutation (matching CANCEL does it)
    assert b.n_orders() == n
def test_depth_clear_resets():
    b = BookState(); b.apply(ev_add_bid, 110, 5, 1); b.apply(ev_clear, 0,0,0)
    assert b.best_bid() is None and b.n_orders() == 0
```
(`ev_*` are `np.uint64` action|side constants defined at top of the test.)
- [ ] **Step 2:** Run → FAIL.
- [ ] **Step 3:** Implement `BookState` (dict `orders[oid]=(side,px,qty)`; `bids/asks` price→qty aggregates;
  MODIFY = full-qty replacement; CLEAR resets; TRADE/FILL are no-ops). Keep it pure-Python first (numba later
  only if Phase-5 profiling needs it).
- [ ] **Step 4:** Run → PASS.
- [ ] **Step 5:** Commit.

### Task 1.3: Month loader + day-window + roll-exclusion (`loader.py`, `calendar.py`)

- [ ] **Step 1:** `calendar.py` — `is_excluded_roll_day(date, contract_meta)` implementing **expiration −3..+1**
  with the pinned anchor (spec §13 open item: choose last-trade-day anchor; document). Failing test asserts a
  known roll month excludes the right 5-day window and keeps the rest.
- [ ] **Step 2:** `loader.iter_days(npz_paths, start, end)` yielding `(date, events_array)` clipped to the
  day's UTC window, stable-sorted by `exch_ts`, with `valid` flag (two-sided book exists) and `event_source`
  tag; skips excluded/roll days. Test on a 3-day slice asserting day boundaries + exclusion.
- [ ] **Step 3:** Run → PASS.
- [ ] **Step 4:** Commit.

### Task 1.4: Leak-free / causality proof (the non-negotiable, mirrors `c11_clean_verify`)

- [ ] **Step 1:** Test `tests/zb_mbo/test_causal.py`: build book state series over a day; corrupt the LAST 1%
  of events (×5 px); re-replay; assert book state at every t before the corruption window is **bit-identical**
  (max abs diff 0.0). This proves no future event leaks into past state.
```python
def test_future_events_do_not_change_past_state():
    states = replay_states(events)
    ev2 = events.copy(); ev2["px"][-k:] *= 5
    states2 = replay_states(ev2)
    cut = len(events) - k - 1
    assert max_abs_state_diff(states[:cut], states2[:cut]) == 0.0
```
- [ ] **Step 2:** Run → PASS (fix replay if not). - [ ] **Step 3:** Commit.

---

## Phase 2 — Trigger detectors (gate: each fires on a designed positive, silent on a negative)

### Task 2.1: Vacuum (A), Task 2.2: Sweep (B), Task 2.3: Event (C) — `triggers.py`

For each family (one task each, same shape):
- [ ] **Step 1:** Failing test in `tests/zb_mbo/test_triggers.py` — a hand-built event stream that SHOULD fire
  (e.g., A: near-touch depth drops to <50% of its trailing median then an aggressive order arrives; B: a
  marketable order consuming ≥K levels within W ms; C: timestamp inside a scheduled event window) and a
  matched control that should NOT fire. Assert `t_signal` equals the last causal event and that the detector
  emits `(t_signal, side, family, threshold)`.
- [ ] **Step 2:** Run → FAIL. - [ ] **Step 3:** Implement the detector (causal: state/features from events
  with `exch_ts ≤ t_signal` only; thresholds are the ≤3 frozen economic levels from the spec grid). - [ ]
  **Step 4:** Run → PASS. - [ ] **Step 5:** Commit.
- [ ] **Event calendar (within 2.3):** build `calendar.event_windows(date)` from a small committed data file
  `data/zb_events.csv` (auction times, 08:30 releases, FOMC dates 2023-2026). Test it returns the right windows
  for a known date. Source dates from public schedules; record provenance in the CSV header.

---

## Phase 3 — Latency-adjusted labeler (gate: leak checks for the move measurement)

### Task 3.1: `labeler.forward_move(events, t_signal, latency_ns, horizon_ns, side)`

- [ ] **Step 1:** Failing tests `tests/zb_mbo/test_labeler.py`:
```python
def test_move_measured_from_t_decision_not_t_signal():
    # construct a stream where mid jumps between t_signal and t_signal+latency;
    # the labeled move must NOT include that jump.
    m = forward_move(events, t_signal, latency_ns=1_000_000, horizon_ns=H, side="buy")
    assert m == expected_from_decision_time
def test_trigger_own_prints_excluded():
    # the defining sweep prints occur at t_signal; forward window must start strictly after them
    assert label_window_start(events, t_signal) > t_last_trigger_event(events, t_signal)
def test_taker_entry_is_far_touch():
    # buy enters at best_ask at t_decision (crosses), not mid
    assert entry_price == best_ask_at(t_signal + latency_ns)
```
- [ ] **Step 2:** Run → FAIL. - [ ] **Step 3:** Implement (entry = far touch at `t_decision`; exit = touch
  crossed to flatten at `t_decision+H`; net ticks = (exit−entry)/tick·side − cost_ticks; exclude prints ≤
  `t_signal`). - [ ] **Step 4:** Run → PASS. - [ ] **Step 5:** Commit.

---

## Phase 4 — Stats extensions (gate: match textbook values)

### Task 4.1 DSR, 4.2 PSR(SR*), 4.3 PBO-CSCV, 4.4 stationary bootstrap — `research/stats.py`

- [ ] **Step 1:** Failing tests `tests/test_stats.py` with known-value checks:
```python
def test_psr_benchmark():
    # PSR(SR*=0) of a clearly-positive series ~ high; PSR(SR*=1.0) lower
    assert probabilistic_sharpe_ratio(sr=2.0, sr_star=0.0, n=250, skew=0, kurt=3) > 0.99
    assert probabilistic_sharpe_ratio(sr=2.0, sr_star=1.0, n=250, skew=0, kurt=3) < \
           probabilistic_sharpe_ratio(sr=2.0, sr_star=0.0, n=250, skew=0, kurt=3)
def test_dsr_penalizes_trials():
    assert deflated_sharpe_ratio(sr=2.0, n_trials=1, ...) > deflated_sharpe_ratio(sr=2.0, n_trials=100, ...)
def test_pbo_random_is_half():
    # CSCV on pure-noise return matrix -> PBO ~ 0.5
    assert 0.35 < pbo_cscv(noise_matrix, S=8) < 0.65
def test_stationary_bootstrap_ci_covers_mean():
    lo, hi = stationary_bootstrap_ci(pnl, block_len=20, stat=np.mean, n=500)
    assert lo < pnl.mean() < hi
```
- [ ] **Step 2:** Run → FAIL. - [ ] **Step 3:** Implement per Bailey-López de Prado (DSR/PSR) and
  Politis-Romano (stationary bootstrap); PBO via CSCV over S blocks. - [ ] **Step 4:** Run → PASS. - [ ] **Step
  5:** Commit.

---

## Phase 5 — Census + Stage-1 screen (GATE: cheapest kills; CHECKPOINT to owner)

### Task 5.1: Event census `campaign/c20_zb_census.py` — **first real compute**

- [ ] **Step 1:** Implement `census()` that, per month (parallel per-file, `.venv-mbo`), replays the book,
  runs all three detectors at their frozen thresholds, and counts **independent episodes** (de-duplicated by a
  refractory window so one move ≠ many episodes) per family, per year, per session bucket, on
  train-eligible days only (exclude roll/burned/sealed). Cache per-day episode tables to
  `data/zb_mbo_cache/dt=YYYY-MM-DD.parquet` to avoid re-reading 60 GB later.
- [ ] **Step 2:** Run over the **train+validation span only** (never the sealed block). Output a census table
  + `reports/zb_taker/census.json`.
- [ ] **Step 3:** **KILL GATE K3:** if any family has < ~50 independent in-sample episodes, mark it
  power-dead. If all three are power-dead → write the underpowered-null memo and STOP. **Post a progress note.**
- [ ] **Step 4:** Commit census script + report.

### Task 5.2: Stage-1 screen `campaign/c21_zb_stage1_screen.py` (TRAIN folds only)

- [ ] **Step 1:** Using `validation.walk_forward_folds` (purge = max horizon; embargo ≥ max(H, cluster len)),
  for each surviving family × ≤3 thresholds × ≤3 horizons, compute the **latency-adjusted net move**
  distribution at latency ∈ {0.5,1.0,1.5} ms on **train folds only**; report mean net ticks ± SE, t-stat,
  sign-stability across folds, episode count, and the fraction of episodes clearing the 1.1-tick hurdle.
- [ ] **Step 2:** Apply **K1** (net E[move] < 1.1 ticks → drop), **K2** (sign flips across folds → drop),
  **K3** (<50 episodes → drop). Log every examined config to the trial registry (feeds DSR `N_trials`).
- [ ] **Step 3:** Write `reports/zb_taker/stage1.json` + a short results note. If no survivor → Stage-1 NULL
  memo (confirms the prior). **Post a progress note.**
- [ ] **Step 4:** Commit.

---

## Phase 6 — hftbacktest Stage-2 (survivors only) + verdict

### Task 6.1: Probe suite `probes.py` — MUST pass before any Stage-2 fill is trusted

- [ ] **Step 1:** Implement P1–P6 (spec §9) as pytest tests with hand-built L3 arrays through
  `correct_event_order()` and the **same** `BacktestAsset` chain production uses (`.l3_fifo_queue_model()`,
  `.no_partial_fill_exchange()`, `.constant_order_latency(L,L)`, `tick_size=0.03125`). Assert exact
  integer-tick fill price and `exch_ts == submit + latency`; P2 (cancel-in-latency → adverse fill); P3
  (TRADE alone doesn't fill); P4 (`rc∉{0,1}` raises + final sweep); P5 (no tick-as-price); P6 (side round-trip).
- [ ] **Step 2:** Run → must PASS. If any fail, STOP and fix the harness before trusting it (engine "fails by
  producing wrong-but-believable P&L"). - [ ] **Step 3:** JIT-parity: run a sample with `NUMBA_DISABLE_JIT=1`
  and assert equal P&L. - [ ] **Step 4:** Commit.

### Task 6.2: Stage-2 backtest `backtest.py` + `campaign/c22_zb_stage2_hftbt.py`

- [ ] **Step 1:** Harness: build asset, run loop (poll, `rc∉{0,1}` raises, final fill sweep), submit a
  marketable order on each surviving trigger at `t_decision`, exit on horizon/target/time-stop; return
  trade-level P&L with fills. - [ ] **Step 2:** Run survivors walk-forward, **latency swept 0.1–5 ms**; emit
  per-trade P&L, the **slippage/adverse-selection distribution**, and edge-vs-latency. Reconcile vs Stage-1
  (spec §8.4). - [ ] **Step 3:** Commit.

### Task 6.3: Placebo control + Task 6.4: stats, sealed OOS, verdict

- [ ] **Step 1:** Placebo: re-run Stage-2 on time-shuffled + sign-flipped triggers (matched count/time-of-day);
  the real trigger must beat placebo after deflation (else NULL — mechanical/leak).
- [ ] **Step 2:** Compute headline stats on validation folds: DSR(`N_trials`), PSR(SR*=1.0), PBO-CSCV,
  block-bootstrap CIs, %-pos-months on effective N, maxDD. Apply **K4–K8**.
- [ ] **Step 3:** **Sealed-OOS one-shot** (unburned last months): one evaluation, no iteration (K10). Apply
  **K5/K6/K9**.
- [ ] **Step 4:** Write `docs/research/results/2026-06-08-zb-mbo-taker-<verdict>.md` (census, Stage-1 table,
  Stage-2 tearsheet + latency curve, placebo, DSR/PSR/PBO, kill decisions, deflated-prior accounting). Add
  `CAMPAIGN.md` entries (per family + study verdict). Independent re-verification if a survivor. Commit.

---

## Run sequence & kill gates (summary)

`0.1 venv → 0.2 schema → 1.x replay+leak proof → 2.x triggers → 3 labeler → 4 stats → 5.1 CENSUS (K3 gate,
checkpoint) → 5.2 STAGE-1 (K1-K3, checkpoint) → 6.1 PROBES (must pass) → 6.2 STAGE-2 + latency sweep →
6.3 placebo → 6.4 stats + SEALED one-shot (K4-K10) → verdict + writeup + registry`.

Heavy compute (census, Stage-1 replay, Stage-2) runs only after the prior gate passes. Census/Stage-1 cache
per-day parquet so Stage-2 and re-runs don't re-read the 60 GB tapes.

---

## Self-review

- **Spec coverage:** §2 triggers→Ph2; §4 data/codes/splits→Ph0-1 + calendar; §5 ordering→Run sequence; §6
  multiple-testing→4.x stats + trial registry in 5.2/6.4; §7 leakage→1.4/3.1/2.x causal; §8 fill realism→6.1-6.2;
  §9 probes→6.1; §10 significance/kill→4.x + 6.3-6.4. All covered.
- **Placeholders:** thresholds intentionally frozen as "≤3 economic levels" + finalized exact numbers in the
  trial-registry step before running (spec §13) — not stray TODOs. `<verdict>` is a filename template.
- **Type consistency:** `action()/signed_flow()` (codes) used by book/triggers; `BookState` API stable;
  `forward_move(...)` signature stable; stats fn names match tests. OK.
- **Open items inherited from spec §13** (exact K-thresholds, frozen-grid hash, roll-anchor, sealed months,
  hftbacktest wheel/Python) are each pinned in the task that first needs them (0.1, 1.3, 5.2).
