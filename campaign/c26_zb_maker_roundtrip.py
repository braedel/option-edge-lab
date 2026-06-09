"""Round-trip maker proxy (offline) -- resolve the ONE thing that makes the fill-gate straddle zero:
the EXIT-passive fill rate. c25 modeled entry + mark-at-mid (so net was +0.255 optimistic / -0.245
conservative depending entirely on whether you exit passively). This simulates the full round-trip:
passive entry fill -> post a passive EXIT on the opposite side -> if it fills within H_EXIT capture the
full spread, else FORCE a cross-exit (pay the spread). Realized round-trip net per fill, %positive, the
exit-passive rate, and the worst-case tail. Still a coarse proxy (optimistic on fills); if even THIS is
net-negative, the maker is null without hftbacktest. Run after c25.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c22_zb_discovery import build_features  # noqa: E402
from c24_zb_multivariate import extract  # noqa: E402

from options_lab.zb_mbo.labeler import bbo_timeline  # noqa: E402
from options_lab.zb_mbo.loader import load_events, month_path  # noqa: E402
from options_lab.zb_mbo.stream import TICK, stream_features  # noqa: E402

TRAIN = ["2024-05", "2024-06", "2024-07"]
VAL = "2025-09"
MAXEV = 6_000_000
H_FILL = 600        # max snaps to scan for entry fill
H_EXIT = 1200       # max snaps to scan for passive exit before forcing a cross
QUOTE_Q = 0.75
FEE_T = 4.0 / 31.25


def fit_signal():
    Xtr, ytr = [], []
    for m in TRAIN:
        X, y = extract(m); Xtr.append(X); ytr.append(y)
    g = HistGradientBoostingRegressor(max_depth=3, max_iter=250, learning_rate=0.05)
    g.fit(np.vstack(Xtr), np.concatenate(ytr)); return g


def main(val=VAL):
    g = fit_signal()
    a = load_events(month_path(val))[:MAXEV]
    tl = bbo_timeline(a); snaps = stream_features(a)
    feats = build_features(snaps)
    ok = feats.notna().all(axis=1).to_numpy()
    snaps, feats = snaps[ok], feats[ok].to_numpy()
    ts = snaps["ts"].astype(np.int64)
    sig = g.predict(feats)
    side = np.sign(sig).astype(int)
    quote = np.abs(sig) >= np.quantile(np.abs(sig), QUOTE_Q)
    bb, ba, bid1, ask1 = snaps["best_bid"], snaps["best_ask"], snaps["bid1"], snaps["ask1"]
    tpx, tqty, tsign = snaps["trade_px"], np.abs(snaps["trade_signed"]), np.sign(snaps["trade_signed"])
    N = len(ts)

    def fill_passive(start, P, need, want_sell_aggressor, maxscan):
        """Scan forward from `start`; return the snap index where aggressor vol clears `need`, else -1."""
        cum = 0.0
        j = start + 1
        end = min(N, start + maxscan + 1)
        while j < end:
            if want_sell_aggressor and tsign[j] < 0 and tpx[j] <= P + 1e-9:
                cum += tqty[j]
            elif (not want_sell_aggressor) and tsign[j] > 0 and tpx[j] >= P - 1e-9:
                cum += tqty[j]
            if cum >= need:
                return j
            j += 1
        return -1

    nets, hold, exit_pass = [], [], []
    n_entry = 0
    for i in np.flatnonzero(quote):
        s = side[i]
        if s == 0:
            continue
        if s > 0:   # LONG: passive bid entry, passive ask exit
            ej = fill_passive(i, bb[i], bid1[i], True, H_FILL)
            if ej < 0:
                continue
            n_entry += 1
            entry_px = bb[i]
            xj = fill_passive(ej, ba[i], ask1[i], False, H_EXIT)
            if xj >= 0:
                exit_px, passive = ba[i], True
            else:
                k = min(ej + H_EXIT, N - 1)
                exit_px, passive = bb[k], False     # forced: cross down to the bid to sell
        else:       # SHORT: passive ask entry, passive bid exit
            ej = fill_passive(i, ba[i], ask1[i], False, H_FILL)
            if ej < 0:
                continue
            n_entry += 1
            entry_px = ba[i]
            xj = fill_passive(ej, bb[i], bid1[i], True, H_EXIT)
            if xj >= 0:
                exit_px, passive = bb[i], True
            else:
                k = min(ej + H_EXIT, N - 1)
                exit_px, passive = ba[k], False     # forced: cross up to the ask to cover
        net = (exit_px - entry_px) * s / TICK - FEE_T
        nets.append(net); exit_pass.append(passive)
        hold.append((ts[(xj if xj >= 0 else min(ej + H_EXIT, N - 1))] - ts[ej]) / 1e9)

    nets = np.array(nets); exit_pass = np.array(exit_pass); hold = np.array(hold)
    days = max(int(np.unique(ts // 86_400_000_000_000).size), 1)
    print(f"=== round-trip maker proxy: train={TRAIN} -> VAL {val} ({days} days) ===")
    print(f"quotes={int(quote.sum())} entry_fills={n_entry} round_trips={len(nets)} entry_fill_rate={n_entry/max(int(quote.sum()),1):.3f}")
    if len(nets):
        print(f"exit_passive_rate={exit_pass.mean():.3f}  mean_hold={hold.mean():.1f}s")
        print(f"round-trip net/fill: mean={nets.mean():+.3f}t  median={np.median(nets):+.3f}t  "
              f"%positive={np.mean(nets > 0):.3f}  worst5={np.sort(nets)[:5].round(2)}")
        ann = nets.mean() * len(nets) / days * 252 * 31.25   # $/yr/contract, very rough
        print(f"~$/contract/day={nets.mean()*len(nets)/days*31.25:+.1f}  (1 lot; coarse, optimistic on fills)")
        print(f"VERDICT: {'net-positive even before realistic-fill haircut -> harness worth building' if nets.mean()>0 else 'NET-NEGATIVE even optimistic -> maker null without needing hftbacktest'}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else VAL)
