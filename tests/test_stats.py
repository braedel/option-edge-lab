"""Numeric-oracle tests for advanced significance / overfitting statistics.

These are not just monotonicity checks: each statistic is pinned to an inline
recomputation (PSR, DSR), a known analytic expectation (PBO ~0.5 on noise),
a calibration experiment (stationary-bootstrap CI coverage), or a hand-worked
example (Holm, uniqueness).
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

from options_lab.research.stats import (
    deflated_sharpe_ratio,
    deflated_sharpe_ratio_from_count,
    holm,
    pbo_cscv,
    probabilistic_sharpe_ratio,
    stationary_bootstrap,
    stationary_bootstrap_ci,
    uniqueness_weights,
)


# --------------------------------------------------------------------------- #
# 1. Probabilistic Sharpe Ratio
# --------------------------------------------------------------------------- #
def test_psr_high_sharpe_near_one():
    assert probabilistic_sharpe_ratio(2.0, 0.0, 250) > 0.99


def test_psr_monotone_in_benchmark():
    # A higher hurdle sr_star must (weakly) lower the probability of beating it.
    # NB: at sr=2.0, n=250 the z-score is ~18, so PSR saturates to exactly 1.0 in
    # float64 for BOTH sr_star=0 and sr_star=1 (1.0 <= 1.0 holds, strict < does not
    # because the difference is far below machine epsilon).
    hi = probabilistic_sharpe_ratio(2.0, 0.0, 250)
    lo = probabilistic_sharpe_ratio(2.0, 1.0, 250)
    assert lo <= hi
    assert hi == pytest.approx(1.0)
    # Strict monotonicity is genuinely observable away from the saturation ceiling:
    assert probabilistic_sharpe_ratio(0.5, 0.25, 250) < probabilistic_sharpe_ratio(0.5, 0.0, 250)
    assert probabilistic_sharpe_ratio(2.0, 2.0, 60) < probabilistic_sharpe_ratio(2.0, 0.0, 60)


def test_psr_inline_oracle():
    # Hand-check against a direct Phi() computation written inline (no library PSR).
    sr, sr_star, n, skew, kurt = 1.3, 0.4, 180, -0.5, 5.0
    z = (sr - sr_star) * math.sqrt(n - 1) / math.sqrt(1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr**2)
    expected = stats.norm.cdf(z)
    assert probabilistic_sharpe_ratio(sr, sr_star, n, skew, kurt) == pytest.approx(expected, rel=1e-12)
    # bounded in [0, 1]
    val = probabilistic_sharpe_ratio(sr, sr_star, n, skew, kurt)
    assert 0.0 <= val <= 1.0


def test_psr_gaussian_default_matches_simple_form():
    # With skew=0, kurt=3 the denominator is sqrt(1 + sr**2/2); pin one value.
    sr, sr_star, n = 2.0, 0.0, 250
    z = (sr - sr_star) * math.sqrt(n - 1) / math.sqrt(1.0 + 0.5 * sr**2)
    assert probabilistic_sharpe_ratio(sr, sr_star, n) == pytest.approx(stats.norm.cdf(z), rel=1e-12)


# --------------------------------------------------------------------------- #
# 2. Deflated Sharpe Ratio
# --------------------------------------------------------------------------- #
def _sr0_inline(v: float, N: int) -> float:
    """Inline expected-max-Sharpe under the null (Bailey & Lopez de Prado 2014)."""
    gamma = 0.5772156649015329
    e = math.e
    return math.sqrt(v) * (
        (1.0 - gamma) * stats.norm.ppf(1.0 - 1.0 / N) + gamma * stats.norm.ppf(1.0 - 1.0 / (N * e))
    )


def test_dsr_more_trials_deflates_more():
    # Use a modest n and a wide trial spread so the deflation is observable and not
    # masked by the PSR saturation ceiling (sr_obs/n chosen so neither end pins to 1).
    rng = np.random.default_rng(7)
    pool = rng.normal(0.0, 1.0, size=100)
    sr_obs = 1.5
    n = 36
    dsr_many = deflated_sharpe_ratio(sr_obs, pool[:100], n)
    dsr_few = deflated_sharpe_ratio(sr_obs, pool[:2], n)
    # More trials -> higher null bar sr0 -> lower deflated probability.
    assert dsr_many < dsr_few
    # Materially lower, not a rounding wobble.
    assert dsr_few - dsr_many > 0.1


def test_dsr_numeric_oracle_vs_inline():
    # Real oracle: recompute sr0 from the trial variance, then PSR, inline.
    rng = np.random.default_rng(123)
    sr_trials = rng.normal(0.0, 0.7, size=50)
    # n kept small so the resulting PSR is strictly inside (0,1) -- a discriminating
    # oracle, not a saturated 1.0 == 1.0 tautology.
    sr_obs, n = 1.2, 40
    v = float(np.var(sr_trials, ddof=1))
    sr0 = _sr0_inline(v, len(sr_trials))
    z = (sr_obs - sr0) * math.sqrt(n - 1) / math.sqrt(1.0 + 0.5 * sr_obs**2)
    expected = stats.norm.cdf(z)
    assert deflated_sharpe_ratio(sr_obs, sr_trials, n) == pytest.approx(expected, rel=1e-12)


def test_dsr_from_count_matches_array_form():
    rng = np.random.default_rng(99)
    sr_trials = rng.normal(0.0, 0.6, size=40)
    sr_obs, n = 1.6, 220
    sr_std = float(np.std(sr_trials, ddof=1))
    from_array = deflated_sharpe_ratio(sr_obs, sr_trials, n)
    from_count = deflated_sharpe_ratio_from_count(sr_obs, len(sr_trials), sr_std, n)
    assert from_count == pytest.approx(from_array, rel=1e-12)


def test_dsr_from_count_more_trials_lower():
    sr_obs, sr_std, n = 1.5, 0.5, 250
    assert deflated_sharpe_ratio_from_count(sr_obs, 100, sr_std, n) < deflated_sharpe_ratio_from_count(
        sr_obs, 2, sr_std, n
    )


# --------------------------------------------------------------------------- #
# 3. PBO via CSCV
# --------------------------------------------------------------------------- #
def test_pbo_on_pure_noise_near_half():
    # CSCV-PBO on i.i.d. noise has no real edge, so the IS winner is a coin-flip
    # OOS -> PBO ~ 0.5. (S is taken large enough that the discrete OOS-rank grid
    # keeps the partition-average tight around 0.5 for this seed.)
    rng = np.random.default_rng(2024)
    T, S = 2000, 100
    noise = rng.normal(0.0, 1.0, size=(T, S))
    pbo = pbo_cscv(noise, n_blocks=12)
    assert 0.35 < pbo < 0.65


def test_pbo_with_genuine_edge_is_low():
    rng = np.random.default_rng(11)
    T, S = 2000, 100
    mat = rng.normal(0.0, 1.0, size=(T, S))
    # Column 0 is a genuine, persistent edge: strong positive mean shift. It wins IS
    # and stays top OOS, so PBO collapses toward 0.
    mat[:, 0] += 0.5
    pbo = pbo_cscv(mat, n_blocks=12)
    assert pbo < 0.2


def test_pbo_in_unit_interval():
    rng = np.random.default_rng(5)
    mat = rng.normal(0.0, 1.0, size=(400, 8))
    pbo = pbo_cscv(mat, n_blocks=8)
    assert 0.0 <= pbo <= 1.0


# --------------------------------------------------------------------------- #
# 4. Stationary bootstrap
# --------------------------------------------------------------------------- #
def test_stationary_bootstrap_shape_and_membership():
    rng = np.random.default_rng(0)
    x = np.arange(50.0)
    boot = stationary_bootstrap(x, mean_block=5, n_boot=100, rng=rng)
    assert boot.shape == (100, 50)
    # Every resampled value is drawn (with wrap-around) from the original series.
    assert np.isin(boot, x).all()


def _ar1(n, phi, sigma, mu, rng):
    e = rng.normal(0.0, sigma, size=n)
    y = np.empty(n)
    y[0] = mu + e[0] / math.sqrt(1 - phi**2)
    for t in range(1, n):
        y[t] = mu + phi * (y[t - 1] - mu) + e[t]
    return y


def test_stationary_bootstrap_ci_calibration_ar1():
    # Nominal 90% CI for the mean of an AR(1); empirical coverage of the TRUE mean
    # should be ~0.90 when the block length respects the autocorrelation.
    rng = np.random.default_rng(2025)
    mu_true, phi, sigma = 0.0, 0.5, 1.0
    n, reps = 250, 400
    # Mean block must respect the AR(1) dependence; a Politis-White-style choice for
    # phi=0.5, n=250 is ~8 (too short under-covers -- see the companion test below).
    block = 8.0
    hits = 0
    for _ in range(reps):
        x = _ar1(n, phi, sigma, mu_true, rng)
        lo, hi = stationary_bootstrap_ci(
            x, np.mean, mean_block=block, n_boot=300, alpha=0.10, rng=rng
        )
        if lo <= mu_true <= hi:
            hits += 1
    coverage = hits / reps
    assert 0.80 <= coverage <= 0.98, coverage


def test_stationary_bootstrap_block_one_undercovers_strong_ar1():
    # mean_block=1 == i.i.d. resampling: ignores autocorrelation, so a 90% CI for
    # the mean of a strongly autocorrelated AR(1) must UNDER-cover (well below 0.90).
    rng = np.random.default_rng(4242)
    mu_true, phi, sigma = 0.0, 0.9, 1.0
    n, reps = 250, 400
    hits = 0
    for _ in range(reps):
        x = _ar1(n, phi, sigma, mu_true, rng)
        lo, hi = stationary_bootstrap_ci(
            x, np.mean, mean_block=1.0, n_boot=300, alpha=0.10, rng=rng
        )
        if lo <= mu_true <= hi:
            hits += 1
    coverage = hits / reps
    assert coverage < 0.80, coverage


# --------------------------------------------------------------------------- #
# 5. Holm-Bonferroni
# --------------------------------------------------------------------------- #
def test_holm_hand_example():
    # p = [0.01, 0.04, 0.03]; sorted: 0.01,0.03,0.04 with multipliers 3,2,1.
    # raw step: 0.03, 0.06, 0.04 -> cummax -> 0.03, 0.06, 0.06.
    # map back to input order -> [0.03, 0.06, 0.06].
    adj = holm([0.01, 0.04, 0.03])
    assert adj == pytest.approx([0.03, 0.06, 0.06], abs=1e-12)


def test_holm_bounds():
    p = np.array([0.001, 0.2, 0.04, 0.5, 0.009])
    adj = holm(p)
    assert (adj >= p - 1e-12).all()  # never below raw p
    assert (adj <= bonf_local(p) + 1e-12).all()  # never above Bonferroni
    assert (adj <= 1.0).all()


def bonf_local(p):
    return np.minimum(np.asarray(p, float) * len(p), 1.0)


# --------------------------------------------------------------------------- #
# 6. Average-uniqueness weights
# --------------------------------------------------------------------------- #
def test_uniqueness_full_overlap_is_half():
    starts = np.array([0, 0])
    ends = np.array([10, 10])
    w = uniqueness_weights(starts, ends, normalize=False)
    assert w == pytest.approx([0.5, 0.5], abs=1e-12)


def test_uniqueness_disjoint_is_one():
    starts = np.array([0, 5])
    ends = np.array([5, 10])
    w = uniqueness_weights(starts, ends, normalize=False)
    assert w == pytest.approx([1.0, 1.0], abs=1e-12)


def test_uniqueness_partial_overlap():
    # [0,10) and [5,15): overlap region [5,10) has c=2, the rest c=1.
    # label 0 span [0,10): 5 steps at 1/1, 5 steps at 1/2 -> mean = (5 + 2.5)/10 = 0.75
    # label 1 span [5,15): same by symmetry -> 0.75
    starts = np.array([0, 5])
    ends = np.array([10, 15])
    w = uniqueness_weights(starts, ends, normalize=False)
    assert w == pytest.approx([0.75, 0.75], abs=1e-12)


def test_uniqueness_normalized_mean_one():
    starts = np.array([0, 0, 8])
    ends = np.array([10, 6, 20])
    w = uniqueness_weights(starts, ends, normalize=True)
    assert np.mean(w) == pytest.approx(1.0, abs=1e-12)
