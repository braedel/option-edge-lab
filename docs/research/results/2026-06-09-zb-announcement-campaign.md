# ZB MBO — Macro-announcement edge campaign: comprehensive findings

**Date:** 2026-06-09 · **Branch:** `zb-mbo-taker` · **Mandate:** owner Stop-hook goal — "a decent and reliable
edge, long-term profit, acceptable DD, focused on the large-moving announcements (NFP, FOMC, CPI)."

## Setup
- **Frozen pre-registered calendar** `data/zb_macro_events.csv`: 22 FOMC + 32 NFP + 32 CPI, eligible months
  2023-01..2025-09 (burned/sealed excluded). Sizing confirmed: median 5-min move FOMC 15t / NFP 33.5t / CPI 29t.
- **Execution model:** near-CME, 0.5–1.5 ms latency (NOT colo), $4 RT + spread (~1.13t). We concede the
  sub-second spike to colocated players; every test enters at a latency-achievable point.
- **Infra:** 38.9 GB of L3 staged to a local mirror `D:\TradingData\databento\ZB` (the share is ~13 MB/s,
  Defender-scanned, and stalled under concurrent np.load); loader honors `ZB_DATA_ROOT`; all tests fan months
  across `mp.Pool` (10 workers) — a full 32-month pass runs in ~11 min.

## Angles tested (8, all with controls)
| # | angle (script) | result |
|---|---|---|
| 1 | Continuation, +1–30s entry (c32) | **NULL** — directional info is in the colo spike; +1–5s ≈ coin flip; decays |
| 2 | Slow drift 30min–4hr (c34) | **NULL** — placebo-confirmed noise (ambient trend swamps; placebo |t| up to 2.1) |
| 3 | Pre-CPI drift (c35) + control (c36) + decay (c37) | **Real but DECAYED** — CPI-specific (ordinary mornings flat, excess +3.3t p<0.02) but slope −3.6t/yr, 2023 +6.6t → 2025 −1.0t |
| 4 | Pre-FOMC / pre-NFP drift (c35) | **NULL** |
| 5 | Maker tail-guard: stops/time-stops/blackout (c33) | **NULL** — adverse-selected; every stop *worsens* the mean-reverting book (Kaminski-Lo); base least-bad, 0/9 months positive |
| 6 | Breakout / "straddle the news" (c38) + NFP vet (c39) | NFP-breakout positive but **2023-only** (2024/25 negative); CPI breakout negative (reverts); friction-killed pooled |
| 7 | Intraday post-event mean-reversion fade (c40) | **NULL** — placebo-confirmed noise |
| 8 | **Surprise-conditioned** drift (c41/c42) | **The one promising thread — see below** |

## Two structural walls (the real findings)
1. **The 2023-regime trap.** Every *price-pattern* edge (pre-CPI drift, NFP breakout) is concentrated in
   2023 — the hike→pivot / SVB / big-disinflation-surprise regime where announcements *trended* — and is
   dead or negative in 2024–25. Price-pattern announcement edges are regime artifacts, not stable.
2. **The power wall.** Per-event moves are 15–33t (σ≈27t) and there are only ~30 events/yr/type. A few-tick
   edge therefore needs **~35+ years to reach t>2**. Small announcement edges are *structurally
   unconfirmable* on this data, even if real — significance is impossible here.

## The one thread that survived: the FUNDAMENTAL SURPRISE (c41/c42)
Every price-only test was blind to the actual **actual-vs-consensus surprise** (assembled by deep research
from CNBC/Dow-Jones consensus + BLS, verified). Conditioning on it is the first thing that adds signal:
- **Validation:** the spike goes −sign(surprise) **84% (CPI) / 71% (NFP)** — mechanism confirmed (a beat →
  hawkish → yields up → ZB down).
- **Trade the fundamental direction post-spike (enter t+5min):** CPI +4.45t at 60–120min (%pos 0.68);
  NFP *big* surprises +5.54t at 30min (%pos 0.78, t=2.21, n=9); **divergence cases revert** (when the
  reaction opposed the fundamental, continuing it = −8.3t, t=−1.82 — i.e. fade the fakeout, the data wins).
- **Crucially, positive in ALL THREE years** (big-surprise drift 2023 +6.3 → 2024 +2.7 → 2025 +1.6) —
  declining, but *not* 2023-only-then-dead like the price-pattern leads.

Consolidated strategy (c42): "enter t+5min in the −sign(surprise) direction, hold 30–60min" — rides
agreements, fades divergences. **The edge is in BIG surprises only** (|surprise| ≥ ~median):
- BIG-surprise, hold 30min: +2.05t, %pos 0.61, **Sharpe ~0.82**, maxDD 31t ($978).
- BIG-surprise, hold 60min: +3.69t, %pos 0.46 (winner-driven), **Sharpe ~1.04**, maxDD 31t ($958).
- CPI leg cleanest: 60min +4.45t, **Sharpe ~1.25**, maxDD 24t ($735), persists to 120min.
- ~9–12 trades/yr. Positive in all 3 years on the BIG subset (2023 +6.3 / 2024 +2.7 / 2025 +1.6).
- **The ALL-surprise version is 2024-NEGATIVE** (−3.1t): small surprises are noise — trade only big ones.

### Honest status of the surprise thread
- It is the **best and only positive-in-all-3-years** result of the campaign, with a **coherent mechanism**
  (validated 84%/71% consistency; the fundamental direction wins, including fading divergent reactions).
- But it is **~Sharpe 1, not the Sharpe>2 originally sought** — it lands exactly on the independently
  verified ~1–1.5 ceiling. Samples are tiny (big-surprise n=28, ~9/yr), t-stats are ns (1.3–1.6) at the
  multiple-testing floor, and the 60min cell is winner-driven (%pos 0.46). **It cannot be certified
  in-sample**, and the sealed block (~8 events) is too small to certify either. **The legitimate validation
  is forward paper trading** (which accumulates the events the power wall demands).

## Conclusion & forks (need owner input — resource/constraint decisions)
The **price-pattern** announcement space is exhausted (regime + power walls): continuation, drift, pre-drift,
breakout, maker, and intraday-MR are all NULL or 2023-regime artifacts. The **one real, coherent edge** is
the **fundamental-surprise-direction trade on BIG CPI/NFP surprises** (~Sharpe 1, low DD ~$1k, ~9–12/yr,
positive all 3 years). It is a genuine "decent edge" — but it is **NOT Sharpe>2** (it matches the verified
~1–1.5 ceiling), and it is **power-limited** (ns; ~9 events/yr cannot certify on history).

This means the original Sharpe>2 target is not reachable on ZB futures alone at near-CME latency — the same
conclusion the broader Study-2 reached, now confirmed from the announcement side. Paths forward, each a
resource/constraint decision:
1. **Forward paper-trade the big-surprise-direction strategy** — accept ~Sharpe 1 / low-DD as a "decent
   edge," and validate it forward (the only honest way past the power wall; CPI leg first, it's cleanest).
2. **Cross-instrument curve RV / lead-lag (ZN/ZF/ES)** — highest economic prior, NOT announcement-specific,
   needs other-contract data (modest spend).
3. **Colocate** — to capture the sub-second spike where the directional info actually lives (infra change).
4. **Options data** — to harvest the one reliable announcement signal (vol), which futures can't monetize
   cleanly (data spend; and short-vol carries the catastrophic-tail profile already flagged).

**Recommendation:** (1) is the only no-new-spend path that yields a tradeable result — forward-paper the
CPI/NFP big-surprise-direction trade (Sharpe ~1, DD ~$1k) and let live events certify it; meanwhile (2)
(curve RV) has the strongest prior if a data spend is authorized.
