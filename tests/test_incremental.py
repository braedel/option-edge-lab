from __future__ import annotations

import numpy as np

from options_lab.research.incremental import incremental_skill


def _expanding_folds(n, n_splits):
    fold = n // (n_splits + 1)
    out = []
    for i in range(1, n_splits + 1):
        cut = i * fold
        out.append((np.arange(0, cut), np.arange(cut, cut + fold)))
    return out


def test_incremental_detects_real_signal():
    rng = np.random.default_rng(1)
    n = 800
    B = rng.normal(0, 1, (n, 3))            # baseline = noise
    D = rng.normal(0, 1, (n, 1))            # differentiated = the real signal
    y = 1.5 * D[:, 0] + rng.normal(0, 1.0, n)
    r = incremental_skill(B, D, y, _expanding_folds(n, 5), task="reg")
    assert r["delta"] > 0.05
    assert r["t_stat"] > 3
    assert r["sign_consistency"] >= 0.8


def test_incremental_rejects_noise_D():
    rng = np.random.default_rng(2)
    n = 800
    B = rng.normal(0, 1, (n, 3))
    y = 1.2 * B[:, 0] + rng.normal(0, 1.0, n)  # signal lives in B
    D = rng.normal(0, 1, (n, 2))               # D = pure noise
    r = incremental_skill(B, D, y, _expanding_folds(n, 5), task="reg")
    assert abs(r["t_stat"]) < 3
    assert r["delta"] < 0.02
