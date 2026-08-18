"""
utils/date_utils.py
Deterministic date and time utilities for the Travel AI Agent.
Never let the LLM calculate dates or durations — use these functions.
"""

from datetime import datetime, timedelta, date
from typing import Optional


def days_between(start_date: datetime, end_date: datetime) -> int:
    """Return number of days between two dates. Always positive."""
    delta = end_date.date() - start_date.date()
    return abs(delta.days)


def hours_between(start_dt: datetime, end_dt: datetime) -> float:
    """Return number of hours between two datetimes. Always positive."""
    delta = end_dt - start_dt
    return abs(delta.total_seconds() / 3600)


def add_days(start_date: datetime, days: int) -> datetime:
    """Add N days to a date."""
    return start_date + timedelta(days=days)


def subtract_days(start_date: datetime, days: int) -> datetime:
    """Subtract N days from a date."""
    return start_date - timedelta(days=days)


def add_business_days(start_date: datetime, business_days: int) -> datetime:
    """Add N business days (Mon-Fri) to a date, skipping weekends."""
    current = start_date
    days_added = 0
    while days_added < business_days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # 0=Monday, 4=Friday
            days_added += 1
    return current


def calculate_rental_duration(pickup_date: datetime, return_date: datetime) -> int:
    """
    Calculate number of rental days for a car booking.
    Always rounds up — partial day counts as full day.
    """
    hours = hours_between(pickup_date, return_date)
    days = int(hours / 24)
    if hours % 24 > 0:
        days += 1
    return max(days, 1)


def calculate_hotel_nights(check_in: datetime, check_out: datetime) -> int:
    """Calculate number of hotel nights between check-in and check-out."""
    return days_between(check_in, check_out)


def calculate_refund_expected_date(
    refund_initiated: datetime,
    processing_business_days: int = 7
) -> datetime:
    """
    Calculate expected refund completion date.
    Default: 7 business days from initiation.
    """
    return add_business_days(refund_initiated, processing_business_days)


def is_passport_valid_for_travel(
    passport_expiry: datetime,
    travel_date: datetime,
    required_validity_months: int = 6
) -> dict:
    """
    Check if passport is valid for travel.
    Most countries require 6 months validity beyond travel date.
    Returns status dict with details.
    """
    required_expiry = add_days(travel_date, required_validity_months * 30)
    days_valid_after_travel = days_between(travel_date, passport_expiry)
    is_valid = passport_expiry >= required_expiry

    return {
        "is_valid": is_valid,
        "passport_expiry": passport_expiry.strftime("%Y-%m-%d"),
        "travel_date": travel_date.strftime("%Y-%m-%d"),
        "days_valid_after_travel": days_valid_after_travel,
        "minimum_required_days": required_validity_months * 30,
        "warning": None if is_valid else (
            f"Passport expires {days_valid_after_travel} days after travel date. "
            f"Minimum {required_validity_months * 30} days required."
        )
    }


def get_hours_until_travel(travel_datetime: datetime) -> float:
    """
    Calculate hours remaining until travel/departure.
    Returns negative if travel is in the past.
    """
    now = datetime.utcnow()
    delta = travel_datetime - now
    return round(delta.total_seconds() / 3600, 2)


def get_days_until_checkin(checkin_date: datetime) -> float:
    """
    Calculate days remaining until hotel check-in.
    Returns negative if check-in is in the past.
    """
    now = datetime.utcnow()
    delta = checkin_date - now
    return round(delta.total_seconds() / 86400, 2)


def format_date(dt: datetime) -> str:
    """Format datetime to readable string: '18 Aug 2026'"""
    return dt.strftime("%d %b %Y")


def format_datetime(dt: datetime) -> str:
    """Format datetime to readable string: '18 Aug 2026, 14:30'"""
    return dt.strftime("%d %b %Y, %H:%M")


def parse_date(date_string: str) -> datetime:
    """
    Parse date string to datetime.
    Accepts: 'YYYY-MM-DD' or 'DD/MM/YYYY' or 'DD Mon YYYY'
    """
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d %b %Y", "%d-%m-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_string}. Use YYYY-MM-DD format.")


def is_date_in_past(dt: datetime) -> bool:
    """Check if a datetime is in the past."""
    return dt < datetime.utcnow()


def is_date_in_future(dt: datetime) -> bool:
    """Check if a datetime is in the future."""
    return dt > datetime.utcnow()


