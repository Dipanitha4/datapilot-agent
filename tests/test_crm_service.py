"""
tests/test_crm_service.py
Tests for CRM service functions.
Run with: pytest tests/test_crm_service.py -v
"""

import pytest
from sqlalchemy import text
from database.connection import get_db
from services.crm_service import (
    get_customer_profile,
    get_loyalty_tier,
    get_booking_history,
    update_loyalty_points,
    update_customer_profile,
    search_customers,
    verify_passport,
    add_booking_to_profile,
    move_booking_to_history,
)


def get_first_customer_id() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT id FROM customers LIMIT 1")).fetchone()
        return str(result.id)


def get_first_booking_for_customer(customer_id: str) -> str:
    with get_db() as db:
        result = db.execute(
            text("SELECT id FROM bookings WHERE customer_id = :cid LIMIT 1"),
            {"cid": customer_id}
        ).fetchone()
        return str(result.id) if result else None


# ─── get_customer_profile ─────────────────────────────────────────────────────

def test_get_customer_profile_success():
    customer_id = get_first_customer_id()
    result = get_customer_profile(customer_id)
    assert "error" not in result
    assert "email" in result
    assert "first_name" in result
    assert "loyalty_tier" in result
    assert "passport_expiry_date" in result
    assert "preferences" in result
    assert "payment_methods" in result


def test_get_customer_profile_not_found():
    result = get_customer_profile("00000000-0000-0000-0000-000000000000")
    assert "error" in result


# ─── get_loyalty_tier ────────────────────────────────────────────────────────

def test_get_loyalty_tier_success():
    customer_id = get_first_customer_id()
    result = get_loyalty_tier(customer_id)
    assert "error" not in result
    assert "loyalty_tier" in result
    assert "loyalty_points" in result
    assert "benefits" in result
    assert isinstance(result["benefits"], list)
    assert len(result["benefits"]) > 0


def test_get_loyalty_tier_platinum_has_no_next_tier():
    with get_db() as db:
        result = db.execute(
            text("SELECT id FROM customers WHERE loyalty_tier = 'PLATINUM'::loyaltytier LIMIT 1")
        ).fetchone()
        if result:
            tier_info = get_loyalty_tier(str(result.id))
            assert tier_info["points_to_next_tier"] is None
            assert tier_info["next_tier"] is None



# ─── get_booking_history ─────────────────────────────────────────────────────

def test_get_booking_history_success():
    customer_id = get_first_customer_id()
    result = get_booking_history(customer_id)
    assert "error" not in result
    assert "active_bookings" in result
    assert "booking_history" in result
    assert isinstance(result["active_bookings"], list)
    assert isinstance(result["booking_history"], list)


# ─── update_loyalty_points ───────────────────────────────────────────────────

def test_update_loyalty_points_earn():
    customer_id = get_first_customer_id()
    before = get_loyalty_tier(customer_id)["loyalty_points"]
    result = update_loyalty_points(customer_id, 100, "test earn")
    assert "error" not in result
    assert result["points_after"] == before + 100
    # restore
    update_loyalty_points(customer_id, -100, "test restore")


def test_update_loyalty_points_cannot_go_below_zero():
    customer_id = get_first_customer_id()
    result = update_loyalty_points(customer_id, -9999999, "test overdraft")
    assert result["points_after"] >= 0
    # restore
    before_points = get_loyalty_tier(customer_id)["loyalty_points"]
    update_loyalty_points(customer_id, 9999999 - before_points, "restore")


# ─── update_customer_profile ─────────────────────────────────────────────────

def test_update_customer_profile_allowed_field():
    customer_id = get_first_customer_id()
    result = update_customer_profile(customer_id, {"phone": "+1-555-9999"})
    assert "error" not in result
    assert "phone" in result["updated_fields"]


def test_update_customer_profile_restricted_field():
    customer_id = get_first_customer_id()
    result = update_customer_profile(customer_id, {"loyalty_points": 999999})
    assert "error" in result


# ─── search_customers ────────────────────────────────────────────────────────

def test_search_customers_by_name():
    result = search_customers(name="John")
    assert "error" not in result
    assert result["count"] >= 1
    assert any("John" in r["full_name"] for r in result["results"])


def test_search_customers_by_tier():
    result = search_customers(tier="platinum")
    assert "error" not in result
    assert result["count"] >= 1
    assert all(r["loyalty_tier"] == "platinum" for r in result["results"])


def test_search_customers_no_results():
    result = search_customers(name="XYZ_NONEXISTENT_NAME_999")
    assert result["count"] == 0


# ─── verify_passport ─────────────────────────────────────────────────────────

def test_verify_passport_valid():
    with get_db() as db:
        result = db.execute(
            text("SELECT id FROM customers WHERE passport_expiry_date > '2029-01-01' LIMIT 1")
        ).fetchone()
        if result:
            check = verify_passport(str(result.id), "2026-09-01")
            assert check["is_valid"] is True


def test_verify_passport_invalid():
    with get_db() as db:
        result = db.execute(
            text("SELECT id FROM customers WHERE passport_expiry_date < '2027-01-01' LIMIT 1")
        ).fetchone()
        if result:
            check = verify_passport(str(result.id), "2026-08-18")
            assert "warning" in check


# ─── add_booking_to_profile ──────────────────────────────────────────────────

def test_add_booking_to_profile_success():
    customer_id = get_first_customer_id()
    booking_id = get_first_booking_for_customer(customer_id)
    if booking_id:
        result = add_booking_to_profile(customer_id, booking_id)
        assert "error" not in result
        assert result["booking_id"] == booking_id


def test_add_booking_to_profile_wrong_customer():
    with get_db() as db:
        customers = db.execute(text("SELECT id FROM customers LIMIT 2")).fetchall()
        bookings = db.execute(
            text("SELECT id, customer_id FROM bookings LIMIT 1")
        ).fetchone()
        if bookings and len(customers) > 1:
            wrong_customer = [str(c.id) for c in customers if str(c.id) != str(bookings.customer_id)][0]
            result = add_booking_to_profile(wrong_customer, str(bookings.id))
            assert "error" in result