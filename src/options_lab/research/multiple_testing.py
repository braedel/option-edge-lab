"""Honest multiple-testing correction + minimum detectable effect (spec sections 3 & 5).

Stage-1a needs BH/Bonferroni over the (target x horizon) grid and an MDE floor for underpowered
cells. The deflated-Sharpe / PBO haircut (for a strategy Sharpe) belongs to Stage-2 and is not ported
here.
"""
from __future__ import annotations

import numpy as np
from scipy import stats


def bonferroni(pvals) -> np.ndarray:
    p = np.asarray(pvals, float)
    return np.minimum(p * len(p), 1.0)


def bh_adjust(pvals) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (step-up, monotone)."""
    p = np.asarray(pvals, float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / (np.arange(n) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]  # enforce monotonicity over sorted p
    out = np.empty(n)
    out[order] = np.minimum(ranked, 1.0)
    return out


def t_to_p(t: float, two_sided: bool = True) -> float:
    """Large-sample normal-approx p-value for a t-stat."""
    if two_sided:
        return float(2 * stats.norm.sf(abs(t)))
    return float(stats.norm.sf(t))


def min_detectable_effect(se: float, alpha: float = 0.05, power: float = 0.8,
                          two_sided: bool = True) -> float:
    """Smallest mean effect detectable at ``alpha``/``power`` given standard error ``se``."""
    z_a = stats.norm.ppf(1 - alpha / 2) if two_sided else stats.norm.ppf(1 - alpha)
    z_b = stats.norm.ppf(power)
    return (z_a + z_b) * se
