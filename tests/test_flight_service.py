"""
tests/test_flight_service.py
Tests for flight service functions.
Run with: pytest tests/test_flight_service.py -v
"""

import pytest
from sqlalchemy import text
from database.connection import get_db
from services.flight_service import (
    search_flights,
    search_flexible_dates,
    get_flight_details,
    get_flight_booking,
    book_flight,
    cancel_flight,
    check_cancellation_terms,
    get_bookings_by_customer,
)


def get_first_flight_id(cabin_class: str = "economy") -> str:
    with get_db() as db:
        result = db.execute(
            text(f"SELECT id FROM flights WHERE cabin_class = '{cabin_class.upper()}'::cabinclass LIMIT 1")
        ).fetchone()
        return str(result.id) if result else None


def get_first_customer_id() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT id FROM customers LIMIT 1")).fetchone()
        return str(result.id)


def get_confirmed_flight_booking_id() -> str:
    with get_db() as db:
        result = db.execute(
            text("SELECT id FROM bookings WHERE booking_type = 'FLIGHT'::bookingtype AND status = 'CONFIRMED'::bookingstatus LIMIT 1")
        ).fetchone()
        return str(result.id) if result else None


# ─── search_flights ───────────────────────────────────────────────────────────

def test_search_flights_valid_route():
    with get_db() as db:
        flight = db.execute(text("SELECT origin, destination, departure_time FROM flights LIMIT 1")).fetchone()
        travel_date = flight.departure_time.strftime("%Y-%m-%d")
        result = search_flights(flight.origin, flight.destination, travel_date)
        assert "error" not in result
        assert "results" in result
        assert result["count"] >= 0


def test_search_flights_invalid_date():
    result = search_flights("JFK", "LHR", "not-a-date")
    assert "error" in result


def test_search_flights_no_results():
    result = search_flights("XXX", "YYY", "2026-09-01")
    assert result["count"] == 0


# ─── search_flexible_dates ────────────────────────────────────────────────────

def test_search_flexible_dates():
    with get_db() as db:
        flight = db.execute(text("SELECT origin, destination, departure_time FROM flights LIMIT 1")).fetchone()
        date1 = flight.departure_time.strftime("%Y-%m-%d")
        result = search_flexible_dates(flight.origin, flight.destination, [date1, "2030-01-01"])
        assert "results_by_date" in result
        assert "recommendation" in result
        assert date1 in result["results_by_date"]


# ─── get_flight_details ───────────────────────────────────────────────────────

def test_get_flight_details_success():
    flight_id = get_first_flight_id()
    if flight_id:
        result = get_flight_details(flight_id)
        assert "error" not in result
        assert "flight_number" in result
        assert "cancellation_policy" in result
        assert "departure_time" in result


def test_get_flight_details_not_found():
    result = get_flight_details("00000000-0000-0000-0000-000000000000")
    assert "error" in result


# ─── get_flight_booking ───────────────────────────────────────────────────────

def test_get_flight_booking_success():
    booking_id = get_confirmed_flight_booking_id()
    if booking_id:
        result = get_flight_booking(booking_id)
        assert "error" not in result
        assert "booking_reference" in result
        assert "flight" in result
        assert "cancellation_eligibility" in result


def test_get_flight_booking_not_found():
    result = get_flight_booking("00000000-0000-0000-0000-000000000000")
    assert "error" in result


# ─── book_flight ──────────────────────────────────────────────────────────────

def test_book_flight_success():
    flight_id = get_first_flight_id("economy")
    customer_id = get_first_customer_id()
    if flight_id and customer_id:
        result = book_flight(
            flight_id=flight_id,
            customer_id=customer_id,
            cabin_class="economy",
            passengers=1,
        )
        assert "error" not in result
        assert "booking_reference" in result
        assert result["status"] == "confirmed"
        assert result["loyalty_points_earned"] > 0


def test_book_flight_wrong_cabin():
    flight_id = get_first_flight_id("economy")
    customer_id = get_first_customer_id()
    if flight_id and customer_id:
        result = book_flight(
            flight_id=flight_id,
            customer_id=customer_id,
            cabin_class="business",
        )
        assert "error" in result


# ─── check_cancellation_terms ─────────────────────────────────────────────────

def test_check_cancellation_terms_confirmed_booking():
    booking_id = get_confirmed_flight_booking_id()
    if booking_id:
        result = check_cancellation_terms(booking_id)
        assert "error" not in result
        assert "if_cancelled_now" in result
        assert "refund_amount" in result["if_cancelled_now"]
        assert "requires_supervisor_approval" in result["if_cancelled_now"]


# ─── cancel_flight ────────────────────────────────────────────────────────────

def test_cancel_flight_success():
    # Book a new flight first to have a fresh confirmed booking to cancel
    flight_id = get_first_flight_id("economy")
    customer_id = get_first_customer_id()
    if flight_id and customer_id:
        booked = book_flight(
            flight_id=flight_id,
            customer_id=customer_id,
            cabin_class="economy",
        )
        if "booking_id" in booked:
            result = cancel_flight(booked["booking_id"], reason="Test cancellation")
            assert "error" not in result
            assert result["status"] == "cancelled"
            assert "refund_amount" in result
            assert "requires_supervisor_approval" in result


def test_cancel_already_cancelled():
    with get_db() as db:
        result_row = db.execute(
            text("SELECT id FROM bookings WHERE booking_type = 'FLIGHT'::bookingtype AND status = 'CANCELLED'::bookingstatus LIMIT 1")
        ).fetchone()
        if result_row:
            result = cancel_flight(str(result_row.id), reason="test")
            assert "error" in result


# ─── get_bookings_by_customer ─────────────────────────────────────────────────

def test_get_bookings_by_customer():
    customer_id = get_first_customer_id()
    result = get_bookings_by_customer(customer_id)
    assert "error" not in result
    assert "active_flights" in result
    assert "cancelled_flights" in result
    assert isinstance(result["active_flights"], list)