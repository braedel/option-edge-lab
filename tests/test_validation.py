from __future__ import annotations

import pandas as pd
import pytest

from options_lab.research.validation import walk_forward_folds


def test_folds_expanding_chronological():
    dates = pd.bdate_range("2020-01-01", periods=60)
    folds = list(walk_forward_folds(dates, n_splits=4, embargo=0))
    assert len(folds) == 4
    assert len(folds[0][0]) < len(folds[-1][0])  # expanding train
    for tr, te in folds:
        assert max(tr) < min(te)  # no future leak into train


def test_embargo_shortens_train():
    dates = pd.bdate_range("2020-01-01", periods=60)
    f0 = list(walk_forward_folds(dates, n_splits=4, embargo=0))
    f3 = list(walk_forward_folds(dates, n_splits=4, embargo=3))
    assert len(f3[1][0]) == len(f0[1][0]) - 3


def test_oos_seal_raises():
    dates = pd.bdate_range("2025-08-25", periods=10)  # crosses 2025-09-01
    with pytest.raises(ValueError):
        list(walk_forward_folds(dates, n_splits=3, oos_start="2025-09-01"))


def test_no_seal_ok():
    dates = pd.bdate_range("2025-08-25", periods=12)
    assert len(list(walk_forward_folds(dates, n_splits=3, oos_start=None))) >= 1
