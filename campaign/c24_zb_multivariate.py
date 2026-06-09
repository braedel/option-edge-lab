"""Multivariate 'best shot' for the reverse approach: do the 13 features TOGETHER predict the forward
signed move OUT-OF-SAMPLE better than any single feature (~0.06 IC ceiling)?

Fit Ridge + gradient boosting on TRAIN months, test on strictly-later VAL months (true forward OOS).
Report in-sample vs OOS rank-IC of the model prediction, and the taker net if you trade the predicted
sign. If OOS skill stays ~0.06-0.1 and net stays below the ~1.13t cost, the ceiling is confirmed
*multivariately and OOS* -- the strongest honest 'no directional taker edge' statement. A jump in OOS
skill would be a genuine lead to pre-register and confirm on the sealed block.
Run: python campaign/c24_zb_multivariate.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c22_zb_discovery import HORIZON_NS, LAT_NS, build_features, mid_at  # noqa: E402

from options_lab.zb_mbo.labeler import bbo_timeline  # noqa: E402
from options_lab.zb_mbo.loader import NS_PER_DAY, is_eligible, load_events, month_path  # noqa: E402
from options_lab.zb_mbo.stream import TICK, stream_features  # noqa: E402

MAXEV = 6_000_000
COST = 1.0 + 4.0 / 31.25   # 1-tick spread (taker crosses) + $4 fee in ticks


def extract(month: str):
    a = load_events(month_path(month))[:MAXEV]
    tl = bbo_timeline(a)
    snaps = stream_features(a)
    ts = snaps["ts"].astype(np.int64)
    fwd = (mid_at(tl, ts + LAT_NS + HORIZON_NS) - mid_at(tl, ts + LAT_NS)) / TICK
    feats = build_features(snaps)
    day = ts // int(NS_PER_DAY)
    elig = np.array([is_eligible(dt.date(1970, 1, 1) + dt.timedelta(days=int(d))) for d in day])
    ok = np.isfinite(fwd) & feats.notna().all(axis=1).to_numpy() & elig
    return feats[ok].to_numpy(float), fwd[ok].astype(float)


def run(train_months, val_months):
    Xtr, ytr = [], []
    for m in train_months:
        X, y = extract(m)
        Xtr.append(X); ytr.append(y); print(f"  train {m}: {len(y)} obs")
    Xtr, ytr = np.vstack(Xtr), np.concatenate(ytr)
    Xv, yv = [], []
    for m in val_months:
        X, y = extract(m)
        Xv.append(X); yv.append(y); print(f"  val   {m}: {len(y)} obs (forward OOS)")
    Xv, yv = np.vstack(Xv), np.concatenate(yv)
    print(f"  TRAIN n={len(ytr)}  OOS n={len(yv)}")
    for name, model in [("Ridge", Ridge(alpha=1.0)),
                        ("GBR", HistGradientBoostingRegressor(max_depth=3, max_iter=250, learning_rate=0.05))]:
        model.fit(Xtr, ytr)
        ic_is = stats.spearmanr(model.predict(Xtr), ytr)[0]
        pos = model.predict(Xv)
        ic_oos = stats.spearmanr(pos, yv)[0]
        net = np.sign(pos) * yv - COST            # trade the predicted direction, pay spread+fee
        # also: only act on the most-confident decile of |prediction|
        thr = np.percentile(np.abs(pos), 90)
        conf = np.abs(pos) >= thr
        net_conf = (np.sign(pos[conf]) * yv[conf] - COST)
        print(f"  {name:5s} IC_in={ic_is:+.4f}  IC_oos={ic_oos:+.4f}  "
              f"taker_net_oos={net.mean():+.3f}t (win {np.mean(net > 0):.3f})  "
              f"top-decile-conf net={net_conf.mean():+.3f}t n={conf.sum()}")


if __name__ == "__main__":
    run(["2024-05", "2024-06", "2024-07"], ["2025-07", "2025-08"])
