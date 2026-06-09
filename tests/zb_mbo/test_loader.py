"""Eligibility-gate tests (review B5): sealed/burned/roll days can never enter discovery."""
import datetime as dt

from options_lab.zb_mbo import loader


def test_normal_day_is_eligible():
    assert loader.is_eligible(dt.date(2024, 6, 17))      # ordinary mid-quarter Monday


def test_burned_month_day_not_eligible():
    assert not loader.is_eligible(dt.date(2025, 4, 15))  # 2025-04 is burned


def test_sealed_month_day_not_eligible_by_default():
    assert not loader.is_eligible(dt.date(2025, 12, 10))  # 2025-12 is a default sealed month


def test_roll_buffer_day_not_eligible():
    assert not loader.is_eligible(dt.date(2024, 11, 27))  # the Dec-2024 roll date


def test_out_of_span_not_eligible():
    assert not loader.is_eligible(dt.date(2022, 12, 31))
    assert not loader.is_eligible(dt.date(2026, 5, 1))


def test_eligible_days_disjoint_from_sealed_and_burned():
    # one representative day per month across the whole span
    present = [dt.date(y, m, 15) for y in (2023, 2024, 2025, 2026) for m in range(1, 13)
               if dt.date(y, m, 15) <= loader.DATA_END]
    elig = set(loader.eligible_days(present))
    sealed = {d for d in present if loader.month_key(d) in loader.DEFAULT_SEALED_MONTHS}
    burned = {d for d in present if loader.month_key(d) in loader.BURNED_MONTHS}
    assert elig.isdisjoint(sealed)
    assert elig.isdisjoint(burned)
    assert dt.date(2024, 6, 15) in elig


def test_sealed_days_are_in_sealed_months_only():
    present = [dt.date(2025, 11, 10), dt.date(2025, 12, 10), dt.date(2026, 2, 10), dt.date(2024, 6, 10)]
    sd = set(loader.sealed_days(present))
    assert sd == {dt.date(2025, 11, 10), dt.date(2025, 12, 10), dt.date(2026, 2, 10)}


def test_share_reachable_returns_bool():
    assert isinstance(loader.share_reachable(), bool)
