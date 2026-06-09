"""The frozen pre-registered grid: trial count (incl. prior nulls) and hash stability (review B4/G3)."""
from options_lab.zb_mbo import grid


def test_n_cells_and_trials():
    # families A,B: (3 + 3) thresholds x 3 horizons x 3 latencies = 54 cells; + 10 prior nulls = 64.
    assert grid.n_cells() == 54
    assert grid.n_trials(include_prior=False) == 54
    assert grid.n_trials(include_prior=True) == 64


def test_grid_hash_is_deterministic_16hex():
    h = grid.grid_hash()
    assert h == grid.grid_hash()
    assert len(h) == 16 and all(c in "0123456789abcdef" for c in h)
