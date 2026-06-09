"""Conditional-on-fill gate (review P1 / K-cond + K-fill) -- the cheap, decisive maker test on OFFLINE
data, BEFORE any hftbacktest build.

A passive maker's fills are adversely selected by construction (you fill when aggressive flow hits your
resting quote). So an UNCONDITIONAL signal IC says little about a maker edge -- what matters is whether the
signal survives FILL-CONDITIONING and whether the post-fill move is favorable. This simulates selective
passive quoting with a queue-aware fill PROXY (coarse but honest; cheaper than hftbacktest) and measures:
  - fill rate / fills-per-day (capacity, K-fill);
  - IC_uncond vs IC_fill (does the signal survive on the fill subset?);
  - post-fill drift in ticks (the adverse-selection-adjusted directional value per fill);
  - estimated maker net/fill (passive entry earns ~half-spread; exit at mid [optimistic] or by crossing
    [conservative]; minus fee).
GATES (per review): K-cond = IC_fill >= 0.5*IC_uncond AND maker net/fill > 0 (optimistic). K-fill =
implied fills/day high enough to matter. A FAIL here = maker null, no engine needed. A PASS graduates to
the real hftbacktest harness (which only makes fills HARDER, never easier).

NOTE: coarse proxy -- queue cleared by aggressor volume reaching the displayed touch size; ignores
hidden/iceberg, partials, exact latency. Optimistic on fills by design (if it FAILS even optimistically,
the real engine surely fails). Run after c24. Run: python campaign/c25_zb_maker_fillgate.py [val_month]
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c22_zb_discovery import LAT_NS, build_features, mid_at  # noqa: E402
from c24_zb_multivariate import extract  # noqa: E402  (TRAIN feature/label extractor)

from options_lab.zb_mbo.labeler import bbo_timeline  # noqa: E402
from options_lab.zb_mbo.loader import load_events, month_path  # noqa: E402
from options_lab.zb_mbo.stream import TICK, stream_features  # noqa: E402

TRAIN = ["2024-05", "2024-06", "2024-07"]   # GBR train (same as c24)
VAL = "2025-09"                             # eligible, forward, NOT a signal-certification month
MAXEV = 6_000_000
H_FILL_NS = 2_000_000_000     # 2 s to get filled at the touch
H_HOLD_NS = 5_000_000_000     # 5 s markout horizon
QUOTE_Q = 0.75                # quote only the top-quartile |signal| (selective MM)
MAX_SCAN = 600                # cap forward trades scanned per quote
HALF_SPREAD = 0.5             # ticks earned posting passive at a 1-tick-wide touch
FEE_T = 4.0 / 31.25           # $4 RT in ticks


def fit_signal():
    Xtr, ytr = [], []
    for m in TRAIN:
        X, y = extract(m)
        Xtr.append(X); ytr.append(y)
    g = HistGradientBoostingRegressor(max_depth=3, max_iter=250, learning_rate=0.05)
    g.fit(np.vstack(Xtr), np.concatenate(ytr))
    return g


def main(val=VAL):
    g = fit_signal()
    a = load_events(month_path(val))[:MAXEV]
    tl = bbo_timeline(a)
    snaps = stream_features(a)
    feats = build_features(snaps)
    ok = feats.notna().all(axis=1).to_numpy()
    snaps, feats = snaps[ok], feats[ok].to_numpy()
    ts = snaps["ts"].astype(np.int64)
    sig = g.predict(feats)
    fwd = (mid_at(tl, ts + LAT_NS + H_HOLD_NS) - mid_at(tl, ts + LAT_NS)) / TICK
    fok = np.isfinite(fwd)
    ic_uncond = float(stats.spearmanr(sig[fok], fwd[fok])[0])

    side = np.sign(sig).astype(int)
    quote = np.abs(sig) >= np.quantile(np.abs(sig), QUOTE_Q)
    bb, ba, bid1, ask1 = snaps["best_bid"], snaps["best_ask"], snaps["bid1"], snaps["ask1"]
    tpx, tqty, tsign = snaps["trade_px"], np.abs(snaps["trade_signed"]), np.sign(snaps["trade_signed"])
    N = len(ts)

    filled = np.zeros(N, bool); fill_ts = np.zeros(N, np.int64); fill_px = np.zeros(N)
    for i in np.flatnonzero(quote):
        if side[i] > 0:
            P, need = bb[i], bid1[i]      # resting bid; sell-aggressors at px<=P clear the queue
        elif side[i] < 0:
            P, need = ba[i], ask1[i]      # resting ask; buy-aggressors at px>=P clear the queue
        else:
            continue
        cum = 0.0
        tend = ts[i] + H_FILL_NS
        j = i + 1
        scanned = 0
        while j < N and ts[j] <= tend and scanned < MAX_SCAN:
            if side[i] > 0 and tsign[j] < 0 and tpx[j] <= P + 1e-9:
                cum += tqty[j]
            elif side[i] < 0 and tsign[j] > 0 and tpx[j] >= P - 1e-9:
                cum += tqty[j]
            if cum >= need:
                filled[i], fill_ts[i], fill_px[i] = True, ts[j], P
                break
            j += 1
            scanned += 1

    nq, nf = int(quote.sum()), int(filled.sum())
    days = max(int(np.unique(ts // 86_400_000_000_000).size), 1)
    fill_mid = mid_at(tl, fill_ts[filled])
    exit_mid = mid_at(tl, fill_ts[filled] + H_HOLD_NS)
    drift = ((exit_mid - fill_mid) / TICK) * side[filled]      # post-fill move in your favor (<0 = adverse)
    d = drift[np.isfinite(drift)]
    fsel = filled & fok
    ic_fill = float(stats.spearmanr(sig[fsel], fwd[fsel])[0]) if fsel.sum() > 50 else float("nan")
    net_opt = HALF_SPREAD + d.mean() - FEE_T        # exit at mid (optimistic)
    net_con = d.mean() - FEE_T                       # exit by crossing (conservative)

    print(f"=== conditional-on-fill gate: train={TRAIN} -> VAL {val} ({days} days) ===")
    print(f"snaps={N}  IC_uncond={ic_uncond:+.4f}")
    print(f"quotes(top{int((1-QUOTE_Q)*100)}% |sig|)={nq}  fills={nf}  fill_rate={nf/max(nq,1):.3f}  fills/day~{nf/days:.0f}")
    print(f"IC_fill={ic_fill:+.4f}  (IC_fill/IC_uncond={ic_fill/ic_uncond if ic_uncond else float('nan'):+.2f})")
    print(f"post-fill drift/fill: mean={d.mean():+.3f}t  median={np.median(d):+.3f}t  frac_favorable={np.mean(d>0):.3f}")
    print(f"maker net/fill: optimistic(mid exit)={net_opt:+.3f}t   conservative(cross exit)={net_con:+.3f}t")
    kcond = (np.isfinite(ic_fill) and ic_fill >= 0.5 * ic_uncond and net_opt > 0)
    kfill = (nf / days) >= 10
    print(f"K-cond (IC_fill>=0.5*IC_uncond AND optimistic net>0): {'PASS' if kcond else 'FAIL'}")
    print(f"K-fill (>=~10 fills/day): {'PASS' if kfill else 'FAIL'}")
    print("[coarse offline proxy, optimistic on fills; a FAIL here = maker null without hftbacktest]")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else VAL)
