"""ZB MBO Phase-0 attestation + (Phase-5) event census. Run with .venv-mbo (numpy-only ops here,
so the main venv also works). Reference: docs/research/{specs,plans}/2026-06-08-zb-mbo-taker-*.

Phase 0 (now): attest the RAW npz on real data BEFORE any dependent engine code (review A1/A2/D1/E):
  - action-code space  (A1): assert clear == 3 present, engine-enum code 1 absent;
  - side-convention oracle (A2/E): on the busiest fill-day, Sum(TRADE qty) ~= Sum(FILL qty) AND
    signed flow via TRADE-aggressor vs FILL-resting agree in sign and track price drift;
  - dtypes / ns magnitude (D1).
Writes reports/zb_taker/attestation.json. Phase 5 extends this into the trigger-episode census.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

from options_lab.zb_mbo.codes import DEPTH_CLEAR, FILL, TRADE, action, signed_flow

SHARE = r"\\10.0.0.13\d_drive\TradingData\databento\ZB"
NS_PER_DAY = np.int64(86_400_000_000_000)
EXPECTED_DTYPE = "[('ev', '<u8'), ('exch_ts', '<i8'), ('local_ts', '<i8'), ('px', '<f8'), " \
                 "('qty', '<f8'), ('order_id', '<u8'), ('ival', '<i8'), ('fval', '<f8')]"


def load_events(path):
    return np.load(path, allow_pickle=False)["data"]


def inspect_month(path) -> dict:
    a = load_events(path)
    ev, exch = a["ev"], a["exch_ts"]
    act = action(ev).astype(np.int64)
    codes, counts = np.unique(act, return_counts=True)
    return {
        "path": str(path),
        "n_events": int(a.size),
        "dtype": str(a.dtype),
        "dtype_ok": str(a.dtype) == EXPECTED_DTYPE,
        "action_hist": {int(c): int(n) for c, n in zip(codes, counts)},
        "clear_count_code3": int((act == DEPTH_CLEAR).sum()),
        "engine_code1_count": int((act == 1).sum()),  # must be 0 in the RAW npz
        "n_utc_days": int(np.unique(exch // NS_PER_DAY).size),
        "exch_ns_max": int(exch.max()),
        "exch_ns_magnitude": f"1e{len(str(int(exch.max()))) - 1}",
        "monotonic_frac": round(float((np.diff(exch) >= 0).mean()), 8),
    }


def attest_side_convention(path) -> dict:
    a = load_events(path)
    ev, exch, qty, px = a["ev"], a["exch_ts"], a["qty"], a["px"]
    act = action(ev).astype(np.int64)
    day = exch // NS_PER_DAY
    fd, fc = np.unique(day[act == FILL], return_counts=True)
    chosen = int(fd[np.argmax(fc)])  # busiest fill-day = a normal active session
    d = day == chosen
    tr, fl = (act == TRADE) & d, (act == FILL) & d
    sf = signed_flow(ev, qty)
    sum_tr, sum_fl = float(qty[tr].sum()), float(qty[fl].sum())
    sg_tr, sg_fl = float(sf[tr].sum()), float(sf[fl].sum())
    etr, ptr = exch[tr], px[tr]
    drift = float(ptr[int(np.argmax(etr))] - ptr[int(np.argmin(etr))])
    ratio = sum_fl / sum_tr if sum_tr else 0.0
    sign_agree = bool(np.sign(sg_tr) == np.sign(sg_fl))
    verdict = "PASS" if (0.90 <= ratio <= 1.10 and sign_agree and 1e4 <= sum_tr <= 5e6) else "FAIL"
    return {
        "oracle_day": dt.datetime.fromtimestamp(chosen * 86400, dt.timezone.utc).date().isoformat(),
        "sum_trade_qty": sum_tr,
        "sum_fill_qty": sum_fl,
        "trade_fill_qty_ratio": round(ratio, 4),
        "signed_trade": sg_tr,
        "signed_fill": sg_fl,
        "sign_agree": sign_agree,
        "price_drift_pts": round(drift, 5),
        "flow_vs_drift_agree": bool(np.sign(sg_tr) == np.sign(drift)),
        "verdict": verdict,
    }


def run_attestation(month: str = "zb_2024-12.npz") -> dict:
    path = Path(SHARE) / month
    rep = {
        "generated_note": "ZB MBO Phase-0 real-data attestation (review A1/A2/D1/E)",
        "source": str(path),
        "schema": inspect_month(path),
        "side_oracle": attest_side_convention(path),
    }
    out_dir = Path("reports/zb_taker")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "attestation.json").write_text(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    month = sys.argv[1] if len(sys.argv) > 1 else "zb_2024-12.npz"
    print(json.dumps(run_attestation(month), indent=2))
