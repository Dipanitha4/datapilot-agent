"""
tests/test_car_service.py
Tests for car rental service functions.
Run with: pytest tests/test_car_service.py -v
"""

import pytest
from sqlalchemy import text
from database.connection import get_db
from services.car_service import (
    search_cars,
    get_car_details,
    get_car_booking,
    book_car,
    cancel_car,
    extend_rental,
    change_pickup_location,
    get_bookings_by_customer,
)


def get_first_car_id() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT id FROM cars LIMIT 1")).fetchone()
        return str(result.id)


def get_available_car_id() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT id FROM cars WHERE available = true LIMIT 1")).fetchone()
        return str(result.id) if result else None


def get_first_customer_id() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT id FROM customers LIMIT 1")).fetchone()
        return str(result.id)


def get_car_city() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT city FROM cars LIMIT 1")).fetchone()
        return result.city


def get_confirmed_car_booking() -> dict:
    with get_db() as db:
        result = db.execute(
            text("SELECT id, customer_id FROM bookings WHERE booking_type = 'CAR'::bookingtype AND status = 'CONFIRMED'::bookingstatus LIMIT 1")
        ).fetchone()
        if result:
            return {"booking_id": str(result.id), "customer_id": str(result.customer_id)}
        return {}


# ─── search_cars ──────────────────────────────────────────────────────────────

def test_search_cars_success():
    city = get_car_city()
    result = search_cars(city, "2026-10-01", "2026-10-05")
    assert "error" not in result
    assert "results" in result
    assert result["rental_days"] == 4


def test_search_cars_invalid_dates():
    result = search_cars("New York", "bad-date", "2026-10-05")
    assert "error" in result


def test_search_cars_return_before_pickup():
    result = search_cars("New York", "2026-10-10", "2026-10-05")
    assert "error" in result


def test_search_cars_no_results():
    result = search_cars("NONEXISTENTCITY999", "2026-10-01", "2026-10-05")
    assert result["count"] == 0


# ─── get_car_details ──────────────────────────────────────────────────────────

def test_get_car_details_success():
    car_id = get_first_car_id()
    result = get_car_details(car_id)
    assert "error" not in result
    assert "make" in result
    assert "model" in result
    assert "cancellation_policy" in result


def test_get_car_details_not_found():
    result = get_car_details("00000000-0000-0000-0000-000000000000")
    assert "error" in result


# ─── book_car ─────────────────────────────────────────────────────────────────

def test_book_car_success():
    car_id = get_available_car_id()
    customer_id = get_first_customer_id()
    if car_id and customer_id:
        result = book_car(
            car_id=car_id,
            customer_id=customer_id,
            pickup_location="City Center",
            pickup_date="2026-10-01",
            pickup_time="09:00",
            return_location="City Center",
            return_date="2026-10-05",
            return_time="18:00",
        )
        assert "error" not in result
        assert result["status"] == "confirmed"
        assert result["rental_days"] == 4
        assert result["loyalty_points_earned"] > 0


def test_book_car_unavailable():
    with get_db() as db:
        unavailable = db.execute(
            text("SELECT id FROM cars WHERE available = false LIMIT 1")
        ).fetchone()
        if unavailable:
            customer_id = get_first_customer_id()
            result = book_car(
                car_id=str(unavailable.id),
                customer_id=customer_id,
                pickup_location="Airport",
                pickup_date="2026-10-01",
                pickup_time="09:00",
                return_location="Airport",
                return_date="2026-10-05",
                return_time="18:00",
            )
            assert "error" in result


# ─── cancel_car ───────────────────────────────────────────────────────────────

def test_cancel_car_success():
    car_id = get_available_car_id()
    customer_id = get_first_customer_id()
    if car_id and customer_id:
        booked = book_car(
            car_id=car_id,
            customer_id=customer_id,
            pickup_location="Airport",
            pickup_date="2026-10-10",
            pickup_time="10:00",
            return_location="Airport",
            return_date="2026-10-15",
            return_time="10:00",
        )
        if "booking_id" in booked:
            result = cancel_car(booked["booking_id"], reason="Plans changed")
            assert "error" not in result
            assert result["status"] == "cancelled"
            assert "refund_amount" in result
            assert "requires_supervisor_approval" in result


# ─── change_pickup_location ───────────────────────────────────────────────────

def test_change_pickup_location():
    car_id = get_available_car_id()
    customer_id = get_first_customer_id()
    if car_id and customer_id:
        booked = book_car(
            car_id=car_id,
            customer_id=customer_id,
            pickup_location="City Center",
            pickup_date="2026-11-01",
            pickup_time="09:00",
            return_location="City Center",
            return_date="2026-11-05",
            return_time="18:00",
        )
        if "booking_id" in booked:
            result = change_pickup_location(booked["booking_id"], "Airport Terminal 2")
            assert "error" not in result
            assert result["new_pickup_location"] == "Airport Terminal 2"
            # cleanup
            cancel_car(booked["booking_id"], "test cleanup")


# ─── get_bookings_by_customer ─────────────────────────────────────────────────

def test_get_car_bookings_by_customer():
    customer_id = get_first_customer_id()
    result = get_bookings_by_customer(customer_id)
    assert "error" not in result
    assert "car_bookings" in result
    assert isinstance(result["car_bookings"], list)
