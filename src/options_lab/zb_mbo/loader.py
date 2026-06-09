"""npz loading + the eligible-days gate (review B5) + share preflight (review F3).

`eligible_days()` is the ONLY day-source the census / Stage-1 / Stage-2-development paths may use; it
subtracts {roll buffer, guide exclusions, burned months, sealed months} so sealed/burned data can never
leak into discovery. Burned months are the prior baseline's train/test windows; sealed months are the
most-recent UNBURNED block reserved for the single final OOS look.
"""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import numpy as np

from .calendar import excluded_roll_days

# Data root: the network share by default; override with ZB_DATA_ROOT to read a local mirror (much faster --
# the share's reads are Defender-scanned and choke under concurrent np.load). month_path() reads this.
SHARE = Path(os.environ.get("ZB_DATA_ROOT", r"\\10.0.0.13\d_drive\TradingData\databento\ZB"))
NS_PER_DAY = np.int64(86_400_000_000_000)
DATA_START = dt.date(2023, 1, 1)
DATA_END = dt.date(2026, 4, 30)

# Burned by the prior ZB micro-signal baseline (its train+test windows) -> cannot be sealed OOS (review §2.4).
BURNED_MONTHS = frozenset({"2025-04", "2025-10", "2026-03", "2026-04"})
# Most-recent UNBURNED block reserved as the single sealed final-OOS look. 4 months (a documented
# reduction from ~6, since 2026-03/2026-04 are burned) -- spec section 4 / review §2.4.
DEFAULT_SEALED_MONTHS = frozenset({"2025-11", "2025-12", "2026-01", "2026-02"})
# Guide's legitimate exclusions (Good Friday holidays are NO_DATA and self-exclude; the 5 supplier-degraded
# days are populated here once identified from per-day attestation). Spec section 13 open item.
GUIDE_EXCLUDED: frozenset[dt.date] = frozenset()

_ROLL_EXCLUDED: set[dt.date] | None = None


def _roll_excluded() -> set[dt.date]:
    global _ROLL_EXCLUDED
    if _ROLL_EXCLUDED is None:
        _ROLL_EXCLUDED = excluded_roll_days(DATA_START, DATA_END)
    return _ROLL_EXCLUDED


def month_key(d: dt.date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def all_months() -> list[str]:
    out, y, m = [], 2023, 1
    while (y, m) <= (2026, 4):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def month_path(month: str) -> Path:
    return SHARE / f"zb_{month}.npz"


def share_reachable() -> bool:
    try:
        return SHARE.exists()
    except OSError:
        return False


def is_eligible(d: dt.date, sealed_months: frozenset[str] = DEFAULT_SEALED_MONTHS) -> bool:
    """True if day `d` may be used for census/Stage-1/Stage-2 development."""
    if not (DATA_START <= d <= DATA_END):
        return False
    mk = month_key(d)
    return (mk not in BURNED_MONTHS and mk not in sealed_months
            and d not in GUIDE_EXCLUDED and d not in _roll_excluded())


def eligible_days(present_days, sealed_months: frozenset[str] = DEFAULT_SEALED_MONTHS) -> list[dt.date]:
    """Filter `present_days` (UTC days that actually carry data) to the eligible set, sorted."""
    return sorted(d for d in present_days if is_eligible(d, sealed_months))


def sealed_days(present_days, sealed_months: frozenset[str] = DEFAULT_SEALED_MONTHS) -> list[dt.date]:
    """The sealed-OOS days (touched once, at the very end): in a sealed month, not roll/guide excluded."""
    return sorted(d for d in present_days
                  if month_key(d) in sealed_months and d not in GUIDE_EXCLUDED and d not in _roll_excluded())


def load_events(path) -> np.ndarray:
    """Load a month's structured MBO event array (key 'data')."""
    return np.load(path, allow_pickle=False)["data"]


def utc_day(exch_ts) -> np.ndarray:
    return np.asarray(exch_ts, dtype=np.int64) // NS_PER_DAY


def present_days(events) -> list[dt.date]:
    """Distinct UTC calendar days carrying events in `events`."""
    days = np.unique(utc_day(events["exch_ts"]))
    return [dt.date(1970, 1, 1) + dt.timedelta(days=int(x)) for x in days]
