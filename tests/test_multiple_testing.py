from __future__ import annotations

import numpy as np
import pytest

from options_lab.research.multiple_testing import bh_adjust, bonferroni, min_detectable_effect


def test_bonferroni():
    assert bonferroni([0.01, 0.5])[0] == pytest.approx(0.02)
    assert bonferroni([0.6, 0.6])[0] == pytest.approx(1.0)  # capped at 1


def test_bh_known_example():
    p = [0.001, 0.008, 0.039, 0.041, 0.042]
    adj = bh_adjust(p)
    assert adj[0] == pytest.approx(0.005, abs=1e-9)  # 0.001 * 5 / 1
    assert (adj <= 1.0).all()
    assert (np.diff(adj) >= -1e-9).all()  # monotone non-decreasing over sorted p


def test_mde_positive():
    # z_{.975} + z_{.8} ~= 1.95996 + 0.84162
    assert min_detectable_effect(se=1.0) == pytest.approx(2.80158, abs=1e-3)
