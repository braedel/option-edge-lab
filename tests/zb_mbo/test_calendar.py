"""ZB roll-calendar tests (review D2): the section-2 rule and the roll-buffer exclusion."""
import datetime as dt

from options_lab.zb_mbo import calendar as cal


def test_known_roll_date_dec2024_contract():
    # Dec-2024 delivery: preceding month Nov-2024, last business day Fri Nov 29, minus 2 BD = Wed Nov 27.
    assert cal.roll_date(2024, 12) == dt.date(2024, 11, 27)


def test_known_roll_date_mar2025_contract():
    # Mar-2025 delivery: preceding month Feb-2025, last business day Fri Feb 28, minus 2 BD = Wed Feb 26.
    assert cal.roll_date(2025, 3) == dt.date(2025, 2, 26)


def test_roll_count_over_data_span():
    rd = cal.roll_dates(dt.date(2023, 1, 1), dt.date(2026, 4, 30))
    assert 13 <= len(rd) <= 14            # databento guide: 14 transitions across the ~3.3yr span
    assert dt.date(2024, 11, 27) in rd
    assert rd == sorted(rd)


def test_exclusion_window_around_roll():
    ex = cal.excluded_roll_days(dt.date(2024, 11, 1), dt.date(2024, 12, 1))
    # roll Wed 2024-11-27 -> exclude [27 - 3BD = Fri Nov 22, 27 + 1BD = Thu Nov 28], weekends included
    assert dt.date(2024, 11, 27) in ex and dt.date(2024, 11, 28) in ex
    assert dt.date(2024, 11, 22) in ex
    assert dt.date(2024, 11, 23) in ex and dt.date(2024, 11, 24) in ex   # weekend inside span
    assert dt.date(2024, 11, 21) not in ex                              # roll - 4 BD: outside
    assert dt.date(2024, 12, 2) not in ex                               # well outside
