"""
tests/test_date_utils.py
Tests for date utility functions.
Run with: pytest tests/test_date_utils.py -v
"""

import pytest
from datetime import datetime, timedelta
from utils.date_utils import (
    days_between,
    hours_between,
    add_days,
    subtract_days,
    add_business_days,
    calculate_rental_duration,
    calculate_hotel_nights,
    calculate_refund_expected_date,
    is_passport_valid_for_travel,
    get_hours_until_travel,
    get_days_until_checkin,
    format_date,
    format_datetime,
    parse_date,
    is_date_in_past,
    is_date_in_future,
)


def test_days_between():
    start = datetime(2026, 8, 1)
    end = datetime(2026, 8, 15)
    assert days_between(start, end) == 14
    assert days_between(end, start) == 14  # always positive


def test_hours_between():
    start = datetime(2026, 8, 1, 10, 0)
    end = datetime(2026, 8, 1, 16, 0)
    assert hours_between(start, end) == 6.0


def test_add_days():
    dt = datetime(2026, 8, 1)
    result = add_days(dt, 14)
    assert result == datetime(2026, 8, 15)


def test_subtract_days():
    dt = datetime(2026, 8, 15)
    result = subtract_days(dt, 14)
    assert result == datetime(2026, 8, 1)


def test_add_business_days_skips_weekends():
    # 2026-08-21 is a Friday
    friday = datetime(2026, 8, 21)
    result = add_business_days(friday, 1)
    # Next business day should be Monday 2026-08-24
    assert result.weekday() == 0  # Monday


def test_calculate_rental_duration():
    pickup = datetime(2026, 8, 20, 10, 0)
    returndt = datetime(2026, 8, 27, 10, 0)
    assert calculate_rental_duration(pickup, returndt) == 7

    # Partial day rounds up
    pickup2 = datetime(2026, 8, 20, 10, 0)
    returndt2 = datetime(2026, 8, 27, 18, 0)
    assert calculate_rental_duration(pickup2, returndt2) == 8


def test_calculate_hotel_nights():
    checkin = datetime(2026, 8, 20)
    checkout = datetime(2026, 8, 25)
    assert calculate_hotel_nights(checkin, checkout) == 5


def test_calculate_refund_expected_date():
    start = datetime(2026, 8, 18)  # Tuesday
    result = calculate_refund_expected_date(start, processing_business_days=7)
    # 7 business days from Tuesday Aug 18 = Wednesday Aug 27
    assert result > start
    assert result.weekday() < 5  # Must land on a weekday


def test_passport_valid():
    # Passport expires well after 6 months from travel date
    result = is_passport_valid_for_travel(
        passport_expiry=datetime(2030, 1, 1),
        travel_date=datetime(2026, 8, 18)
    )
    assert result["is_valid"] is True
    assert result["warning"] is None


def test_passport_invalid():
    # Passport expires too soon after travel date
    result = is_passport_valid_for_travel(
        passport_expiry=datetime(2026, 10, 1),
        travel_date=datetime(2026, 8, 18)
    )
    assert result["is_valid"] is False
    assert result["warning"] is not None


def test_get_hours_until_travel():
    future = datetime.utcnow() + timedelta(hours=48)
    hours = get_hours_until_travel(future)
    assert 47 < hours < 49


def test_get_days_until_checkin():
    future = datetime.utcnow() + timedelta(days=10)
    days = get_days_until_checkin(future)
    assert 9 < days < 11


def test_format_date():
    dt = datetime(2026, 8, 18)
    assert format_date(dt) == "18 Aug 2026"


def test_format_datetime():
    dt = datetime(2026, 8, 18, 14, 30)
    assert format_datetime(dt) == "18 Aug 2026, 14:30"


def test_parse_date():
    assert parse_date("2026-08-18") == datetime(2026, 8, 18)
    assert parse_date("18/08/2026") == datetime(2026, 8, 18)
    assert parse_date("18 Aug 2026") == datetime(2026, 8, 18)


def test_is_date_in_past():
    past = datetime.utcnow() - timedelta(days=1)
    assert is_date_in_past(past) is True


def test_is_date_in_future():
    future = datetime.utcnow() + timedelta(days=1)
    assert is_date_in_future(future) is True
