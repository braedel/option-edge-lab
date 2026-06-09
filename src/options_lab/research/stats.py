"""Advanced significance / overfitting statistics for Stage-2 strategy evaluation.

Where ``multiple_testing.py`` corrects the Stage-1a feature-screening grid, these
estimators judge a *strategy's* Sharpe once a configuration has been selected from
many trials, and quantify how much of an apparent edge is selection luck.

References (cited per-function in the docstrings):
  * Bailey & Lopez de Prado (2012), "The Sharpe Ratio Efficient Frontier",
    Journal of Risk 15(2) -- Probabilistic Sharpe Ratio.
  * Bailey & Lopez de Prado (2014), "The Deflated Sharpe Ratio",
    Journal of Portfolio Management 40(5) -- Deflated Sharpe Ratio.
  * Bailey, Borwein, Lopez de Prado & Zhu (2017), "The Probability of Backtest
    Overfitting", Journal of Computational Finance 20(4) -- CSCV / PBO.
  * Politis & Romano (1994), "The Stationary Bootstrap", JASA 89(428).
  * Holm (1979), "A Simple Sequentially Rejective Multiple Test Procedure".
  * Lopez de Prado (2018), "Advances in Financial Machine Learning", ch. 4
    -- average-uniqueness / concurrency weights.

Style mirrors ``multiple_testing.py``: plain numpy/scipy, simple functions,
returning ``np.ndarray`` or ``float``.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
from scipy import stats

# Euler-Mascheroni constant (used by the Deflated Sharpe expected-maximum).
_EULER_GAMMA = 0.5772156649015329


# --------------------------------------------------------------------------- #
# Probabilistic & Deflated Sharpe Ratio
# --------------------------------------------------------------------------- #
def probabilistic_sharpe_ratio(
    sr: float, sr_star: float, n: int, skew: float = 0.0, kurt: float = 3.0
) -> float:
    """Probabilistic Sharpe Ratio -- Bailey & Lopez de Prado (2012).

    Probability that the true Sharpe exceeds a benchmark ``sr_star`` given an
    observed Sharpe ``sr`` from ``n`` observations, adjusting for non-normal
    returns via ``skew`` and ``kurt`` (kurtosis, 3 == Gaussian)::

        PSR = Phi( (sr - sr_star) * sqrt(n - 1)
                   / sqrt(1 - skew*sr + ((kurt - 1)/4) * sr**2) )

    ``sr`` and ``sr_star`` must be in the *same* per-observation units. Returns
    a probability in ``[0, 1]`` (``scipy.stats.norm.cdf``).
    """
    denom = np.sqrt(1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr**2)
    z = (sr - sr_star) * np.sqrt(n - 1.0) / denom
    return float(stats.norm.cdf(z))


def _expected_max_sharpe(sr_std: float, n_trials: int) -> float:
    """Expected maximum of ``n_trials`` i.i.d. null Sharpes (Bailey & LdP 2014).

        sr0 = sr_std * ( (1 - gamma) * Phi^-1(1 - 1/N)
                         + gamma     * Phi^-1(1 - 1/(N*e)) )

    where ``gamma`` is Euler-Mascheroni and ``N`` is the number of trials. This
    is the false-discovery hurdle the observed Sharpe must clear.
    """
    if n_trials < 2:
        # With <2 trials there is no selection effect; the hurdle is zero.
        return 0.0
    n = float(n_trials)
    z1 = stats.norm.ppf(1.0 - 1.0 / n)
    z2 = stats.norm.ppf(1.0 - 1.0 / (n * np.e))
    return float(sr_std * ((1.0 - _EULER_GAMMA) * z1 + _EULER_GAMMA * z2))


def deflated_sharpe_ratio(
    sr: float, sr_trials, n: int, skew: float = 0.0, kurt: float = 3.0
) -> float:
    """Deflated Sharpe Ratio -- Bailey & Lopez de Prado (2014).

    PSR re-benchmarked against the *expected maximum* Sharpe under the null,
    given ``N = len(sr_trials)`` configurations that were tried. ``v`` is the
    cross-trial variance of the Sharpes (``ddof=1``)::

        sr0 = sqrt(v) * ((1 - gamma) * Phi^-1(1 - 1/N)
                         + gamma     * Phi^-1(1 - 1/(N*e)))
        DSR = probabilistic_sharpe_ratio(sr, sr0, n, skew, kurt)

    ``gamma`` = Euler-Mascheroni. Higher ``N`` or a wider trial spread raises the
    bar ``sr0`` and so lowers the deflated probability.
    """
    trials = np.asarray(sr_trials, float)
    n_trials = trials.size
    v = float(np.var(trials, ddof=1)) if n_trials > 1 else 0.0
    sr0 = _expected_max_sharpe(np.sqrt(v), n_trials)
    return probabilistic_sharpe_ratio(sr, sr0, n, skew, kurt)


def deflated_sharpe_ratio_from_count(
    sr: float, n_trials: int, sr_std: float, n: int, skew: float = 0.0, kurt: float = 3.0
) -> float:
    """Deflated Sharpe Ratio from summary stats (Bailey & LdP 2014).

    Identical to :func:`deflated_sharpe_ratio` but takes the trial count
    ``n_trials`` (= N) and the cross-trial Sharpe standard deviation ``sr_std``
    directly, for studies that know the breadth and spread of their search but
    not every individual trial Sharpe.
    """
    sr0 = _expected_max_sharpe(float(sr_std), int(n_trials))
    return probabilistic_sharpe_ratio(sr, sr0, n, skew, kurt)


# --------------------------------------------------------------------------- #
# Probability of Backtest Overfitting (CSCV)
# --------------------------------------------------------------------------- #
def _sharpe_cols(r: np.ndarray) -> np.ndarray:
    """Per-column (per-config) Sharpe of a (rows, S) return block.

    Mean / std across rows; configs with zero variance get Sharpe 0.
    """
    mu = r.mean(axis=0)
    sd = r.std(axis=0, ddof=0)
    out = np.zeros_like(mu)
    nz = sd > 0
    out[nz] = mu[nz] / sd[nz]
    return out


def pbo_cscv(returns_matrix, n_blocks: int = 10) -> float:
    """Probability of Backtest Overfitting via CSCV -- Bailey et al. (2017).

    ``returns_matrix`` is shape ``(T, S)``: per-period returns of ``S`` strategy
    configurations over ``T`` periods. The ``T`` rows are split into ``n_blocks``
    contiguous blocks; for every combination that assigns half the blocks to the
    in-sample (IS) set (the complement is out-of-sample, OOS):

      1. choose the IS-best config by Sharpe;
      2. compute its OOS performance rank among the ``S`` configs, mapped to
         ``w in (0, 1)`` with ``1 == best`` (clamped off the endpoints);
      3. ``logit = ln(w / (1 - w))``.

    PBO is the fraction of partitions whose ``logit <= 0`` -- i.e. the IS winner
    lands at or below the OOS median. ~0.5 means the selection is no better than
    chance (overfit); near 0 means the IS winner generalises.
    """
    r = np.asarray(returns_matrix, float)
    T, S = r.shape
    if n_blocks % 2 != 0:
        raise ValueError("n_blocks must be even so blocks split into equal IS/OOS halves")
    if n_blocks > T:
        raise ValueError("n_blocks cannot exceed the number of rows T")

    # Contiguous (near-)equal blocks of row indices.
    block_idx = np.array_split(np.arange(T), n_blocks)
    half = n_blocks // 2
    all_blocks = range(n_blocks)

    logits = []
    for is_blocks in combinations(all_blocks, half):
        is_set = set(is_blocks)
        is_rows = np.concatenate([block_idx[b] for b in range(n_blocks) if b in is_set])
        oos_rows = np.concatenate([block_idx[b] for b in range(n_blocks) if b not in is_set])

        sr_is = _sharpe_cols(r[is_rows])
        sr_oos = _sharpe_cols(r[oos_rows])

        best = int(np.argmax(sr_is))
        # Rank of the IS-best config among all S OOS Sharpes, in (0, 1], 1 = best.
        # Average-rank handles ties symmetrically.
        order = np.argsort(sr_oos)
        ranks = np.empty(S, float)
        ranks[order] = np.arange(1, S + 1)  # 1 = worst ... S = best
        # ties -> mean rank
        _assign_mean_ranks(sr_oos, ranks)
        w = ranks[best] / (S + 1.0)  # in (0, 1), never hits the endpoints
        w = min(max(w, 1e-6), 1.0 - 1e-6)
        logits.append(np.log(w / (1.0 - w)))

    logits = np.asarray(logits, float)
    return float(np.mean(logits <= 0.0))


def _assign_mean_ranks(values: np.ndarray, ranks: np.ndarray) -> None:
    """In-place: replace ranks of tied ``values`` with their group mean rank."""
    order = np.argsort(values, kind="mergesort")
    sv = values[order]
    i = 0
    n = len(sv)
    while i < n:
        j = i
        while j + 1 < n and sv[j + 1] == sv[i]:
            j += 1
        if j > i:
            grp = order[i : j + 1]
            ranks[grp] = ranks[grp].mean()
        i = j + 1


# --------------------------------------------------------------------------- #
# Stationary bootstrap (Politis & Romano 1994)
# --------------------------------------------------------------------------- #
def stationary_bootstrap(x, mean_block: float, n_boot: int, rng) -> np.ndarray:
    """Stationary bootstrap resamples -- Politis & Romano (1994).

    Generates ``n_boot`` resampled series each of length ``len(x)`` using random
    blocks of geometrically-distributed length with mean ``mean_block``. Starting
    from a uniformly random index, at each step with probability ``p = 1/mean_block``
    a fresh random start index is drawn (new block); otherwise the index advances
    by one with wrap-around. Preserves short-range dependence (autocorrelation),
    unlike the i.i.d. bootstrap.

    ``rng`` is a ``numpy.random.Generator`` supplied by the caller (seed it in
    tests for determinism). Returns an array of shape ``(n_boot, len(x))``.
    """
    x = np.asarray(x)
    T = x.shape[0]
    if T == 0:
        return np.empty((n_boot, 0), dtype=x.dtype)
    p = 1.0 / float(mean_block)

    out = np.empty((n_boot, T), dtype=x.dtype)
    # Vectorise across draws: pre-roll the "new block?" decisions and fresh starts.
    new_block = rng.random((n_boot, T)) < p
    new_block[:, 0] = True  # always start a block at t=0
    fresh_starts = rng.integers(0, T, size=(n_boot, T))

    idx = np.empty((n_boot, T), dtype=np.int64)
    cur = np.empty(n_boot, dtype=np.int64)
    for t in range(T):
        starts = new_block[:, t]
        if t == 0:
            cur = fresh_starts[:, 0].copy()
        else:
            # advance previous index with wrap-around
            cur = (cur + 1) % T
            # where a new block begins, jump to a fresh random start
            cur = np.where(starts, fresh_starts[:, t], cur)
        idx[:, t] = cur
    out = x[idx]
    return out


def stationary_bootstrap_ci(
    x, stat, mean_block: float, n_boot: int, alpha: float, rng
) -> tuple[float, float]:
    """Percentile CI for ``stat`` via the stationary bootstrap (Politis & Romano 1994).

    Resamples ``x`` ``n_boot`` times (see :func:`stationary_bootstrap`), applies
    the scalar statistic ``stat`` (e.g. ``np.mean``) to each resample, and returns
    the ``(alpha/2, 1 - alpha/2)`` percentile two-sided CI as ``(lo, hi)``.

    ``stat`` is called per-resample on a 1-D array. ``alpha=0.10`` -> nominal 90%
    CI. A ``mean_block`` matched to the data's dependence gives correct coverage;
    ``mean_block=1`` collapses to the i.i.d. bootstrap and under-covers serially
    correlated data.
    """
    boot = stationary_bootstrap(x, mean_block, n_boot, rng)
    vals = np.array([float(stat(boot[b])) for b in range(boot.shape[0])])
    lo = float(np.percentile(vals, 100.0 * (alpha / 2.0)))
    hi = float(np.percentile(vals, 100.0 * (1.0 - alpha / 2.0)))
    return lo, hi


# --------------------------------------------------------------------------- #
# Holm-Bonferroni
# --------------------------------------------------------------------------- #
def holm(pvals) -> np.ndarray:
    """Holm-Bonferroni step-down adjusted p-values -- Holm (1979).

    Controls the family-wise error rate. Sort p ascending; the k-th smallest
    (0-indexed ``i``) is multiplied by ``(m - i)``; the adjusted sequence is made
    monotone non-decreasing (running maximum) and capped at 1. Returned in the
    *input* order. Always ``>=`` the raw p-values and ``<=`` Bonferroni.
    """
    p = np.asarray(pvals, float)
    m = p.size
    order = np.argsort(p)
    ranked = p[order] * (m - np.arange(m))  # multiplier m, m-1, ..., 1
    ranked = np.maximum.accumulate(ranked)  # step-down monotonicity
    out = np.empty(m)
    out[order] = np.minimum(ranked, 1.0)
    return out


# --------------------------------------------------------------------------- #
# Average-uniqueness weights (Lopez de Prado, AFML ch. 4)
# --------------------------------------------------------------------------- #
def uniqueness_weights(starts, ends, normalize: bool = True) -> np.ndarray:
    """Average-uniqueness label weights -- Lopez de Prado (2018), ch. 4.

    For labels spanning half-open integer index windows ``[start, end)``, the
    concurrency ``c(t)`` is the number of labels overlapping bar ``t``. A label's
    average uniqueness is the mean of ``1 / c(t)`` over the bars in its own span.
    Fully overlapping labels share weight (each ~``1/k``); disjoint labels are
    fully unique (weight 1).

    With ``normalize=True`` the weights are rescaled to mean 1 (so they sum to the
    number of labels), which is the usual form for sample-weighting an estimator.
    Returns one weight per label, in input order.
    """
    s = np.asarray(starts, dtype=np.int64)
    e = np.asarray(ends, dtype=np.int64)
    if s.shape != e.shape:
        raise ValueError("starts and ends must have the same shape")
    if np.any(e <= s):
        raise ValueError("each end must be strictly greater than its start (half-open [start, end))")

    lo = int(s.min())
    hi = int(e.max())
    # Concurrency via a difference array over [lo, hi).
    diff = np.zeros(hi - lo + 1, dtype=np.int64)
    for a, b in zip(s, e):
        diff[a - lo] += 1
        diff[b - lo] -= 1
    conc = np.cumsum(diff)[:-1]  # c(t) for t in [lo, hi)

    w = np.empty(s.shape[0], dtype=float)
    inv = 1.0 / conc  # concurrency >= 1 on any covered bar
    for i, (a, b) in enumerate(zip(s, e)):
        w[i] = inv[a - lo : b - lo].mean()

    if normalize:
        w = w / w.mean()
    return w
