from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from options_lab.research.targets import (
    TRADING_DAYS,
    forward_max_drawdown,
    forward_realized_vol,
    low_vol_label,
    no_down_label,
)


def test_forward_rv_window_and_nan_tail():
    ret = pd.Series([np.nan, 0.01, -0.01, 0.02, -0.02, 0.0])
    fv = forward_realized_vol(ret, h=2)
    expected = np.sqrt(np.mean(np.array([-0.01, 0.02]) ** 2)) * np.sqrt(TRADING_DAYS)  # ret[2..3] t=1
    assert fv.iloc[1] == pytest.approx(expected)
    assert np.isnan(fv.iloc[-1]) and np.isnan(fv.iloc[-2])


def test_forward_rv_no_lookahead():
    ret = pd.Series([np.nan, 0.01, -0.01, 0.02, -0.02, 0.03, 0.01])
    base = forward_realized_vol(ret, h=2)
    ret2 = ret.copy()
    ret2.iloc[5] = 99.0  # perturb a future point
    pert = forward_realized_vol(ret2, h=2)
    assert pert.iloc[1] == pytest.approx(base.iloc[1])  # window ret[2..3] unaffected
    assert not np.isclose(pert.iloc[3], base.iloc[3])  # window ret[4..5] changed


def test_forward_drawdown():
    close = pd.Series([100.0, 101.0, 99.0, 98.0, 105.0])
    dd = forward_max_drawdown(close, h=2)
    assert dd.iloc[0] == pytest.approx(-0.01)  # min(101,99)=99 -> 99/100-1
    assert dd.iloc[2] == pytest.approx(98 / 99 - 1)  # min(98,105)=98 -> 98/99-1
    assert np.isnan(dd.iloc[-1])


def test_labels():
    fv = pd.Series([0.1, 0.2, 0.3, np.nan])
    lab = low_vol_label(fv, q=0.5)
    assert lab.iloc[0] == 1.0 and lab.iloc[2] == 0.0 and np.isnan(lab.iloc[3])
    dd = pd.Series([-0.01, -0.05, np.nan])
    nd = no_down_label(dd, thr=-0.02)
    assert nd.iloc[0] == 1.0 and nd.iloc[1] == 0.0 and np.isnan(nd.iloc[2])
