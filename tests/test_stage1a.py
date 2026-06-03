from __future__ import annotations

import numpy as np
import pandas as pd

from options_lab.research.stage1a import run_stage1a


def _noise_panel(n=1500, seed=3):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-01", periods=n)
    ret = rng.normal(0, 0.01, n)
    ret[0] = np.nan
    close = 100 * np.cumprod(1 + np.nan_to_num(ret))
    gex = rng.normal(2e9, 5e8, n)
    dix = rng.uniform(0.35, 0.45, n)
    return pd.DataFrame({"date": dates, "spx_close": close, "ret": ret, "gex": gex, "dix": dix})


def _signal_panel(n=1500, seed=11):
    """gex[k] encodes hidden vol hv[k+2]; so gex_lag1[t] = hv[t+1] predicts fwd_rv[t] at h=1."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-01", periods=n)
    hv = rng.choice([0.004, 0.025], size=n)  # i.i.d. hidden daily vol (baseline can't predict it)
    ret = rng.standard_normal(n) * hv
    ret[0] = np.nan
    close = 100 * np.cumprod(1 + np.nan_to_num(ret))
    gex = np.full(n, np.nan)
    gex[:-2] = hv[2:]
    gex[-2:] = hv.mean()
    dix = rng.uniform(0.35, 0.45, n)
    return pd.DataFrame({"date": dates, "spx_close": close, "ret": ret, "gex": gex, "dix": dix})


def test_table_structure_and_kill_on_noise():
    table, verdict = run_stage1a(_noise_panel(), oos_start="2025-09-01")
    assert {"target", "h", "delta", "t_stat", "sign_consistency", "mde", "verdict"}.issubset(table.columns)
    assert len(table) == 6  # 2 targets x 3 horizons
    assert verdict == "KILL"


def test_pass_on_injected_signal():
    table, verdict = run_stage1a(_signal_panel(), oos_start="2025-09-01")
    assert verdict == "PASS"
    # the win should be on forward realized vol at the short horizon
    passing = table[table["verdict"] == "PASS"]
    assert (passing["target"] == "fwd_rv").any()
