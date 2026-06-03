"""Purged & embargoed expanding walk-forward folds (generalized from the PinFly lab).

Unlike the PinFly original, the OOS-seal date is a PARAMETER (default ``None`` = no seal). ``embargo``
drops the last ``embargo`` train rows before each test block, purging an h-day label horizon so a
forward target cannot leak from train into the adjacent test fold.
"""
from __future__ import annotations

from typing import Iterator, Optional, Sequence

import pandas as pd


def walk_forward_folds(
    dates: Sequence,
    n_splits: int = 5,
    embargo: int = 0,
    oos_start: Optional[str] = None,
) -> Iterator[tuple[list, list]]:
    """Yield ``(train_dates, test_dates)`` expanding-window folds, chronological.

    Raises ``ValueError`` if ``oos_start`` is set and any input date is on/after it (keeps the sealed
    OOS block a single, separate final event).
    """
    d = sorted(pd.to_datetime(list(dates)))
    if oos_start is not None:
        cut = pd.to_datetime(oos_start)
        if any(x >= cut for x in d):
            raise ValueError(f"walk-forward must exclude sealed OOS dates (>= {oos_start})")
    n = len(d)
    if n_splits < 1 or n < n_splits + 1:
        return
    fold = n // (n_splits + 1)
    for i in range(1, n_splits + 1):
        cut = i * fold
        train = d[: max(0, cut - embargo)]
        test = d[cut : cut + fold]
        if train and test:
            yield train, test
