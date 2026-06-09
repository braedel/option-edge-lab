"""ZB (CME Treasury) contract-roll calendar + roll-buffer exclusion.

Active-contract rule (databento handling guide section 2 -- calendar-deterministic and leak-free):
the contract rolls **2 business days before the last business day of the month preceding the
delivery month**. ZB delivery months are quarterly: Mar, Jun, Sep, Dec.

To stay clear of the transition zone we exclude [roll - 3 business days, roll + 1 business day]
(the owner's "expiration -3..+1" buffer, operationalized on the section-2 roll date per review D2).
Business days are Mon-Fri via numpy busday; the +/- buffer absorbs exchange-holiday slippage so an
exact holiday calendar is not required for the exclusion to stay clear of the roll.
"""
from __future__ import annotations

import datetime as dt

import numpy as np

DELIVERY_MONTHS = (3, 6, 9, 12)


def _d64(d: dt.date) -> np.datetime64:
    return np.datetime64(d, "D")


def _to_date(d64: np.datetime64) -> dt.date:
    return d64.astype("datetime64[D]").astype(dt.date)


def _last_business_day(year: int, month: int) -> np.datetime64:
    """Last Mon-Fri business day of (year, month)."""
    nm = dt.date(year + 1, 1, 1) if month == 12 else dt.date(year, month + 1, 1)
    return np.busday_offset(_d64(nm), -1, roll="forward")  # day before first-of-next-month


def roll_date(year: int, delivery_month: int) -> dt.date:
    """Roll date for the contract delivering in (year, delivery_month)."""
    if delivery_month == 1:
        pm_year, pm_month = year - 1, 12
    else:
        pm_year, pm_month = year, delivery_month - 1
    last_bd = _last_business_day(pm_year, pm_month)
    return _to_date(np.busday_offset(last_bd, -2, roll="backward"))


def roll_dates(start: dt.date, end: dt.date) -> list[dt.date]:
    """All quarterly roll dates falling within [start, end]."""
    out = []
    for y in range(start.year - 1, end.year + 2):
        for m in DELIVERY_MONTHS:
            r = roll_date(y, m)
            if start <= r <= end:
                out.append(r)
    return sorted(out)


def excluded_roll_days(start: dt.date, end: dt.date, before: int = 3, after: int = 1) -> set[dt.date]:
    """Calendar dates within [roll - `before` BD, roll + `after` BD] for every roll in [start, end]
    (weekend days inside the span are included too, since the tapes carry Globex weekend sessions)."""
    days: set[dt.date] = set()
    for r in roll_dates(start, end):
        lo = np.busday_offset(_d64(r), -before, roll="backward")
        hi = np.busday_offset(_d64(r), after, roll="forward")
        d = lo
        while d <= hi:
            days.add(_to_date(d))
            d = d + np.timedelta64(1, "D")
    return days
