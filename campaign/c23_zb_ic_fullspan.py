"""Full-span robustness of the reverse-discovery ICs (review: do NOT conclude from one month).

For every eligible TRAIN+VALIDATION month, on a comparable ~5-day (6M-event) sample, compute the
per-feature Spearman IC vs the forward signed mid move (1 ms latency, 5 s horizon). Aggregate to
mean IC +/- across-month std and IR = mean/std -- the robust signal-strength measure (process doc
section 2). If a directional feature's IC is consistently ~0.1 with low spread across all regimes,
the ~0.1-tick ceiling is robust; an outlier regime with IC >> 0.1 would be a genuine lead to chase.

Resumable (per-month CSVs are tiny). Run:
  python campaign/c23_zb_ic_fullspan.py process     # heavy: ~30 month-samples, ~70 min
  python campaign/c23_zb_ic_fullspan.py aggregate
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from c22_zb_discovery import HORIZON_NS, LAT_NS, build_features, mid_at  # noqa: E402

from options_lab.zb_mbo.labeler import bbo_timeline  # noqa: E402
from options_lab.zb_mbo.loader import (  # noqa: E402
    BURNED_MONTHS, DEFAULT_SEALED_MONTHS, all_months, load_events, month_path, share_reachable,
)
from options_lab.zb_mbo.stream import TICK, stream_features  # noqa: E402

OUT = Path("reports/zb_taker/ic_fullspan")
MAXEV = 6_000_000
TRAINVAL = [m for m in all_months() if m not in BURNED_MONTHS and m not in DEFAULT_SEALED_MONTHS]


def process_month(month: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"ic_{month}.csv"
    if out.exists():
        print(f"  {month} cached")
        return
    a = load_events(month_path(month))[:MAXEV]
    tl = bbo_timeline(a)
    snaps = stream_features(a)
    ts = snaps["ts"].astype(np.int64)
    fwd = (mid_at(tl, ts + LAT_NS + HORIZON_NS) - mid_at(tl, ts + LAT_NS)) / TICK
    feats = build_features(snaps)
    ok = np.isfinite(fwd) & feats.notna().all(axis=1).to_numpy()
    fe, fw = feats[ok], fwd[ok]
    rows = [{"month": month, "feature": c, "ic": float(stats.spearmanr(fe[c], fw)[0]), "n": int(ok.sum())}
            for c in fe.columns]
    pd.DataFrame(rows).to_csv(out, index=False)
    di = next(r["ic"] for r in rows if r["feature"] == "depth_imb")
    print(f"  {month}: n={int(ok.sum())} depth_imb IC={di:+.3f}")


def process_all() -> None:
    assert share_reachable(), "data share \\\\10.0.0.13 unreachable"
    print(f"IC full-span over {len(TRAINVAL)} eligible months (~5-day samples each)")
    for m in TRAINVAL:
        process_month(m)


def aggregate() -> None:
    files = sorted(OUT.glob("ic_*.csv"))
    if not files:
        print("no per-month files yet")
        return
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    g = df.groupby("feature")["ic"].agg(["mean", "std", "count", "min", "max"])
    g["IR"] = g["mean"] / g["std"]
    g = g.reindex(g["mean"].abs().sort_values(ascending=False).index)
    print(f"\n=== IC robustness across {df['month'].nunique()} eligible months ===")
    print(g.round(4).to_string())
    g.to_csv(OUT / "ic_summary.csv")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "process"
    if cmd == "aggregate":
        aggregate()
    else:
        process_all()
        aggregate()
