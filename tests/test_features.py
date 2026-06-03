from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from options_lab.research.features import baseline_features, differentiated_features


def _panel(n=300):
    dates = pd.bdate_range("2020-01-01", periods=n)
    rng = np.random.default_rng(0)
    ret = rng.normal(0, 0.01, n)
    ret[0] = np.nan
    close = 100 * np.cumprod(1 + np.nan_to_num(ret))
    gex = rng.normal(2e9, 5e8, n)
    dix = rng.uniform(0.35, 0.45, n)
    return pd.DataFrame({"date": dates, "spx_close": close, "ret": ret, "gex": gex, "dix": dix})


def test_baseline_cols_and_asof():
    p = _panel()
    feats, cols = baseline_features(p)
    assert {"rv_5", "rv_10", "rv_21", "ret_5d", "dow_0"} <= set(cols)
    p2 = p.copy()
    p2.loc[200, "ret"] = 5.0  # perturb a future ret
    f2, _ = baseline_features(p2)
    assert feats["rv_5"].iloc[100] == pytest.approx(f2["rv_5"].iloc[100])  # earlier row unaffected


def test_differentiated_lagged():
    p = _panel()
    feats, cols = differentiated_features(p)
    assert "gex_lag1" in cols and "dix_lag1" in cols and "gex_z" in cols
    assert feats["gex_lag1"].iloc[10] == pytest.approx(p["gex"].iloc[9])  # row t uses gex[t-1]
    assert not np.isclose(feats["gex_lag1"].iloc[10], p["gex"].iloc[10])  # no same-day leak
