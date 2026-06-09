"""Reverse / outcome-first edge DISCOVERY (TRAIN-only, exploratory) -- per owner suggestion.

Instead of pre-specifying triggers and testing them, MAP where favorable taker moves occur and
reverse-analyse their precursors:
  1. Build causal pre-move microstructure features at every trade (derived from the feature stream).
  2. Label each with the forward signed MID move (gross ticks) at production latency/horizon.
  3. (a) IC (Spearman) of each feature vs the forward move;
     (b) 5-bucket map of the strongest feature -> mean move, directional-taker NET, n;
     (c) the "edge-location" signature: feature means in the top-decile |move| vs overall.
Anything predictive here is a CANDIDATE to pre-register and confirm OOS -- selecting precursors on the
outcome is the #1 overfitting trap, so this is discovery on TRAIN data, never a result.

Run: python campaign/c22_zb_discovery.py [month] [max_events]
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy import stats

from options_lab.zb_mbo.labeler import bbo_timeline
from options_lab.zb_mbo.loader import NS_PER_DAY, load_events, month_path
from options_lab.zb_mbo.stream import TICK, stream_features

LAT_NS = 1_000_000          # 1 ms
HORIZON_NS = 5_000_000_000  # 5 s
FLOW_W = 50
SIZE_W = 100
COST_TICKS = 4.0 / 31.25    # round-turn fee in ticks (spread paid separately below)


def mid_at(timeline, t):
    """Vectorised mid active at each time in array t (nan before the first touch)."""
    j = np.searchsorted(timeline["ts"], np.asarray(t, dtype=np.int64), side="right") - 1
    ok = j >= 0
    jj = np.clip(j, 0, len(timeline) - 1)
    mid = (timeline["bid"][jj] + timeline["ask"][jj]) / 2.0
    mid[~ok] = np.nan
    return mid


def build_features(snaps):
    """Causal pre-move microstructure features (all known at the trade; trailing stats use .shift(1))."""
    bb, ba = snaps["best_bid"], snaps["best_ask"]
    bid1, ask1 = snaps["bid1"], snaps["ask1"]
    bid3, ask3 = snaps["bid3"], snaps["ask3"]
    mid = snaps["mid"]
    sgn = pd.Series(snaps["trade_signed"])
    asz = sgn.abs()
    micro = (bb * ask1 + ba * bid1) / (bid1 + ask1)          # size-weighted microprice
    midret = pd.Series(mid).diff() / TICK
    di = pd.Series((bid3 - ask3) / (bid3 + ask3))
    dt_ms = pd.Series(snaps["ts"].astype("int64")).diff().clip(lower=0) / 1e6
    feats = pd.DataFrame({
        "depth_imb": di.to_numpy(),
        "top1_imb": (bid1 - ask1) / (bid1 + ask1),
        "micro_dev": (micro - mid) / TICK,
        "flow_10": sgn.rolling(10).sum().shift(1).to_numpy(),
        "flow_50": sgn.rolling(FLOW_W).sum().shift(1).to_numpy(),
        "flow_200": sgn.rolling(200).sum().shift(1).to_numpy(),
        "size_z": (asz / asz.rolling(SIZE_W).median().shift(1)).to_numpy(),
        "rv_100": midret.rolling(100).std().shift(1).to_numpy(),                 # realized vol (ticks)
        "vpin_50": (sgn.rolling(50).sum().abs() / asz.rolling(50).sum()).shift(1).to_numpy(),  # flow toxicity
        "di_change": (di - di.shift(20)).to_numpy(),                            # book tilting
        "top_conc": (bid1 / bid3 - ask1 / ask3),                               # top-of-book concentration
        "log_dt": np.log1p(dt_ms.to_numpy()),                                  # log ms since last trade
        "spread_ticks": snaps["spread_ticks"].astype(float),
    })
    return feats


def main(month="zb_2024-06.npz", max_events=6_000_000):
    a = load_events(month_path(month.replace("zb_", "").replace(".npz", "")) if month.startswith("zb_") else month_path(month))
    sl = a[:max_events]
    tl = bbo_timeline(sl)
    snaps = stream_features(sl)
    ts = snaps["ts"].astype(np.int64)
    fwd = (mid_at(tl, ts + LAT_NS + HORIZON_NS) - mid_at(tl, ts + LAT_NS)) / TICK   # signed gross ticks
    feats = build_features(snaps)
    ok = np.isfinite(fwd) & feats.notna().all(axis=1).to_numpy()
    ts_ok = ts[ok]
    feats, fwd = feats[ok].reset_index(drop=True), fwd[ok]
    n = len(fwd)
    print(f"{month}: snaps={len(snaps)} usable={n} days={int(np.unique(ts[ok]//86_400_000_000_000).size)} "
          f"| fwd move ticks: std={fwd.std():.2f} p10/50/90={np.percentile(fwd,[10,50,90]).round(2)}")

    print("\n=== (a) IC: Spearman(feature, forward signed move) ===")
    ics = {}
    for c in feats.columns:
        rho, p = stats.spearmanr(feats[c], fwd)
        ics[c] = rho
        print(f"  {c:12s} IC={rho:+.4f}  p={p:.1e}")
    top = max(ics, key=lambda k: abs(ics[k]))

    print(f"\n=== (b) 5-bucket map of strongest feature '{top}' (IC={ics[top]:+.4f}) ===")
    q = pd.qcut(feats[top], 5, labels=False, duplicates="drop")
    for b in sorted(pd.unique(q[~pd.isna(q)])):
        m = q == b
        mv = fwd[m.to_numpy()]
        # directional taker: trade in the sign of the feature; net = sign(feat)*move - spread(1t) - fee
        net = np.sign(feats[top][m.to_numpy()]) * mv - 1.0 - COST_TICKS
        print(f"  bucket {int(b)} feat[{feats[top][m.to_numpy()].min():+.2f},{feats[top][m.to_numpy()].max():+.2f}] "
              f"n={m.sum():5d} mean_move={mv.mean():+.3f} dir_taker_net={net.mean():+.3f} frac_net>0={np.mean(net>0):.3f}")

    print("\n=== (c) edge-location signature: feature z vs overall at top-decile |forward move| ===")
    big = np.abs(fwd) >= np.percentile(np.abs(fwd), 90)
    for c in feats.columns:
        z = (feats[c][big].mean() - feats[c].mean()) / (feats[c].std() + 1e-12)
        print(f"  {c:12s} mean_z_at_big_moves={z:+.3f}")
    print(f"\n=== (d) horizon sweep on strongest feature '{top}': can a longer hold clear the ~1.13t cost? ===")
    last_ts = int(tl["ts"][-1])
    feat = feats[top].to_numpy()
    hi = feat >= np.percentile(feat, 80)
    lo = feat <= np.percentile(feat, 20)
    for Hs in (5, 30, 120, 300, 900, 1800):
        H = Hs * 1_000_000_000
        tdec = ts_ok + LAT_NS
        texit = tdec + H
        mv = (mid_at(tl, texit) - mid_at(tl, tdec)) / TICK
        v = ((ts_ok // int(NS_PER_DAY)) == (texit // int(NS_PER_DAY))) & (texit <= last_ts) & np.isfinite(mv)
        if v.sum() < 50:
            print(f"  H={Hs:>4}s n={int(v.sum())} (too few)")
            continue
        ic = stats.spearmanr(feat[v], mv[v])[0]
        nl = mv[v & hi].mean() - 1 - COST_TICKS          # long the bid-heavy top quintile
        ns = (-mv[v & lo]).mean() - 1 - COST_TICKS        # short the ask-heavy bottom quintile
        print(f"  H={Hs:>4}s n={int(v.sum()):5d} IC={ic:+.3f} move_std={mv[v].std():5.2f} "
              f"net_long_top20%={nl:+.3f} net_short_bot20%={ns:+.3f}")

    print("\n[TRAIN-only discovery; any signature here must be frozen and confirmed OOS with deflation]")


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "zb_2024-06.npz"
    me = int(sys.argv[2]) if len(sys.argv) > 2 else 6_000_000
    main(m, me)
