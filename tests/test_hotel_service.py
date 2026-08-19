"""
tests/test_hotel_service.py
Tests for hotel service functions.
Run with: pytest tests/test_hotel_service.py -v
"""

import pytest
from sqlalchemy import text
from database.connection import get_db
from services.hotel_service import (
    search_hotels,
    get_hotel_details,
    get_hotel_booking,
    book_hotel,
    cancel_hotel,
    modify_hotel_booking,
    get_bookings_by_customer,
)


def get_first_hotel_id() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT id FROM hotels LIMIT 1")).fetchone()
        return str(result.id)


def get_first_customer_id() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT id FROM customers LIMIT 1")).fetchone()
        return str(result.id)


def get_confirmed_hotel_booking_id() -> str:
    with get_db() as db:
        result = db.execute(
            text("SELECT id FROM bookings WHERE booking_type = 'HOTEL'::bookingtype AND status = 'CONFIRMED'::bookingstatus LIMIT 1")
        ).fetchone()
        return str(result.id) if result else None


def get_hotel_city() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT city FROM hotels LIMIT 1")).fetchone()
        return result.city


# ─── search_hotels ────────────────────────────────────────────────────────────

def test_search_hotels_success():
    city = get_hotel_city()
    result = search_hotels(city, "2026-10-01", "2026-10-05")
    assert "error" not in result
    assert "results" in result
    assert result["nights"] == 4


def test_search_hotels_invalid_dates():
    result = search_hotels("London", "bad-date", "2026-10-05")
    assert "error" in result


def test_search_hotels_checkout_before_checkin():
    result = search_hotels("London", "2026-10-10", "2026-10-05")
    assert "error" in result


def test_search_hotels_by_star_rating():
    city = get_hotel_city()
    result = search_hotels(city, "2026-10-01", "2026-10-05", min_star_rating=5)
    assert "error" not in result
    for hotel in result["results"]:
        assert hotel["star_rating"] >= 5


def test_search_hotels_no_results():
    result = search_hotels("NONEXISTENTCITY999", "2026-10-01", "2026-10-05")
    assert result["count"] == 0


# ─── get_hotel_details ────────────────────────────────────────────────────────

def test_get_hotel_details_success():
    hotel_id = get_first_hotel_id()
    result = get_hotel_details(hotel_id)
    assert "error" not in result
    assert "name" in result
    assert "room_types" in result
    assert "meal_plans" in result
    assert "cancellation_policy" in result


def test_get_hotel_details_not_found():
    result = get_hotel_details("00000000-0000-0000-0000-000000000000")
    assert "error" in result


# ─── get_hotel_booking ────────────────────────────────────────────────────────

def test_get_hotel_booking_success():
    booking_id = get_confirmed_hotel_booking_id()
    if booking_id:
        result = get_hotel_booking(booking_id)
        assert "error" not in result
        assert "booking_reference" in result
        assert "hotel" in result
        assert "check_in" in result
        assert "cancellation_terms" in result


# ─── book_hotel ───────────────────────────────────────────────────────────────

def test_book_hotel_success():
    hotel_id = get_first_hotel_id()
    customer_id = get_first_customer_id()
    details = get_hotel_details(hotel_id)
    room_type = list(details["room_types"].keys())[0] if details.get("room_types") else "standard"

    result = book_hotel(
        hotel_id=hotel_id,
        customer_id=customer_id,
        room_type=room_type,
        check_in="2026-10-01",
        check_out="2026-10-04",
        adults=2,
    )
    assert "error" not in result
    assert result["status"] == "confirmed"
    assert result["nights"] == 3
    assert result["loyalty_points_earned"] > 0


def test_book_hotel_invalid_room_type():
    hotel_id = get_first_hotel_id()
    customer_id = get_first_customer_id()
    result = book_hotel(
        hotel_id=hotel_id,
        customer_id=customer_id,
        room_type="nonexistent_room_xyz",
        check_in="2026-10-01",
        check_out="2026-10-04",
    )
    assert "error" in result


# ─── cancel_hotel ─────────────────────────────────────────────────────────────

def test_cancel_hotel_success():
    hotel_id = get_first_hotel_id()
    customer_id = get_first_customer_id()
    details = get_hotel_details(hotel_id)
    room_type = list(details["room_types"].keys())[0] if details.get("room_types") else "standard"

    booked = book_hotel(
        hotel_id=hotel_id,
        customer_id=customer_id,
        room_type=room_type,
        check_in="2026-10-15",
        check_out="2026-10-18",
    )
    if "booking_id" in booked:
        result = cancel_hotel(booked["booking_id"], reason="Change of plans")
        assert "error" not in result
        assert result["status"] == "cancelled"
        assert "refund_amount" in result
        assert "requires_supervisor_approval" in result


# ─── modify_hotel_booking ─────────────────────────────────────────────────────

def test_modify_hotel_booking_add_special_request():
    booking_id = get_confirmed_hotel_booking_id()
    if booking_id:
        result = modify_hotel_booking(
            booking_id=booking_id,
            add_special_request="Extra pillows please",
        )
        assert "error" not in result
        assert "changes" in result
        assert len(result["changes"]) > 0


# ─── get_bookings_by_customer ─────────────────────────────────────────────────

def test_get_hotel_bookings_by_customer():
    customer_id = get_first_customer_id()
    result = get_bookings_by_customer(customer_id)
    assert "error" not in result
    assert "hotel_bookings" in result
    assert isinstance(result["hotel_bookings"], list)