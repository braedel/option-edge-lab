# ZB MBO — Macro-event continuation: NULL (Stage-1, zero-spread)

**Date:** 2026-06-09 · **Branch:** `zb-mbo-taker` · **Status:** CLOSED — documented NULL, quant-concurred.

## Thesis (owner's)
Scheduled macro announcements (FOMC 14:00 ET, NFP/CPI 08:30 ET) produce large, *tradeable*
post-release **continuation** moves — "a famous thing traders talk about."

## What we built
- **Frozen, pre-registered calendar** `data/zb_macro_events.csv` (committed `2df0d58`): 86 events over
  32 eligible months 2023-01..2025-09 (burned/sealed excluded). 22 FOMC (authoritative Fed dates,
  21/22 spike-validated, c30); 32 NFP (first-Friday + 08:30 spike-verify, 31/32 confirmed — the miss is
  2025-07-04, an Independence-Day holiday misfire flagged for re-pin to Jul-3); 32 CPI (dominant mid-month
  Mon–Thu 08:30 spike; **12/32 flagged contaminated** = comparable PPI/retail spike within ±2 days;
  CPI(clean) = the 20 unflagged).
- **Sizing already confirmed (MFE):** FOMC 15t / NFP 33.5t / CPI 29t median 5-min move. Moves are real
  and large — the only question is harvestable *directional* edge net of ~1 ms latency.

## Stage-1 test (`campaign/c32_event_continuation.py`) — mid-based, ZERO spread
Maximally generous: if it fails at zero spread, the real widened spread only worsens it.
- direction = sign of trade-price move over `[t, t+reaction_delay]` (we do NOT use the release number);
- ENTER at `t + reaction_delay + 1ms` (uniform, schedule-relative, **strictly after** the direction
  window → no conditioning leak);
- `continuation = (exit-entry)/tick * direction`, exit at entry+H;
- 12 pre-registered cells: reaction_delay ∈ {1,5,30}s × H ∈ {120,600}s.
- **Pre-registered KILL gate:** pooled mean < ~2t, OR %continued ≈ 0.50, OR leave-one-out sign-flips.

## Result — KILL (all three criteria tripped)
At the only realistic entry (≥5 s), every pool sits at ≈0t with %cont ≈ 0.50 and |t| < 0.7:

| cell | NFP | CPI(clean) | POOL(NFP+CPIclean) | FOMC |
|---|---|---|---|---|
| 5s/120s | +0.26t (t.09) | +1.65t (t.42) | **+0.80t (t.36)** | −3.56t (t−1.87) |
| 5s/600s | +2.16t (t.78) | +0.55t (t.13) | **+1.53t (t.66)** | −3.78t (t−1.56) |
| 30s/600s | +1.42t (t.77) | +0.75t (t.24) | **+1.16t (t.71)** | −0.84t (t−.47) |

- **LOO** (5s/600s, all types incl FOMC): mean +0.14t, range [−0.38,+0.71], **sign-unstable (FRAGILE)**.
- The only signal lives at **+1 s entry** and is **incoherent**: NFP *continues* (+8t, t≈1.5, ns) while
  CPI *reverses* (−9 to −13t, t≈−1.9) — opposite directions, no unified rule — and **both decay to ~0 by
  +5 s**. That t≈−1.9 is one of 12 cells; best-of-12 multiple-testing floor ≈ |t|2.3. It is the
  sub-second/colo window our 0.5–1.5 ms latency concedes we cannot capture.

## Quant sign-off (independent review)
**CONCUR with KILL.** Steelman found no look-ahead/leakage/power problem that could *falsely* null a real
edge: trade-price-as-mid *inflates* continuation (can't hide one); per-type disaggregation doesn't rescue
it; MFE is look-ahead not a missed exit; not underpowered against a 2t effect that isn't there at tradeable
delays. **The +1s flickers are DISMISSED** — re-litigating them as new same-data cells would repeat the
PinFly death-by-variants failure. Do NOT spend Stage 2 (widened spread).

## The NULL claim (exact scope)
> On 32 sealed-out months 2023-01..2025-09, scheduled-macro (FOMC/NFP/CPI) **post-release continuation**
> shows **no tradeable directional edge** at realistic (≥5 s, ~1 ms-latency) entry, mid-based / zero-spread:
> pooled ≈0t, %cont ≈0.50, LOO sign-unstable. Moves are large (MFE 15–33t) but **not directionally
> harvestable post-spike at our latency.**

## Genuinely untested (do NOT claim dead)
- **Forward live/paper TCA** with real fills + real widened spread (execution reality).
- A **level/number-based** signal (vs price-direction) — not attempted.
- **Reaction / mean-reversion fade** as its *own* pre-registered thesis on **unspent** data — not the +1s
  same-data re-litigation, which is forbidden.

## Infra note (this run)
Data lives on a Defender-scanned SMB share (`\\10.0.0.13`) delivering only **~13 MB/s sustained**; 10
concurrent `np.load`s of 1–2 GB months stalled it (13/32 then dead). **Staged a full local mirror to
`D:\TradingData\databento\ZB` (38.9 GB, robocopy)**; loader now honors `ZB_DATA_ROOT`. Local rerun finished
32/32 in 652 s. Residual cost is CPU (decompress + `action()` decode of *entire* months to read ~3 event
windows) — pre-extracting per-month trade arrays would cut it to seconds. Future ZB passes read the local
mirror.

## Standing
Family C (events) closes NULL — the **third** ZB near-CME angle to do so after taker micro-edge and maker
passive. Consistent with the deflated prior for a non-colo, retail-latency participant in ZB.
