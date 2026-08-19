"""
tests/test_insurance_service.py
Tests for insurance service functions.
Run with: pytest tests/test_insurance_service.py -v
"""

import pytest
from sqlalchemy import text
from database.connection import get_db
from services.insurance_service import (
    get_insurance_policy,
    get_policy_by_booking,
    get_policies_by_customer,
    check_coverage,
    check_cancellation_coverage,
    file_claim,
    get_claim_status,
    cancel_insurance,
    update_insurance_travel_dates,
    compare_plans,
)


def get_first_policy_id() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT id FROM insurance_policies WHERE is_active = true LIMIT 1")).fetchone()
        return str(result.id) if result else None


def get_first_booking_with_insurance() -> str:
    with get_db() as db:
        result = db.execute(
            text("SELECT booking_id FROM insurance_policies LIMIT 1")
        ).fetchone()
        return str(result.booking_id) if result else None


def get_first_customer_id() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT id FROM customers LIMIT 1")).fetchone()
        return str(result.id)


def get_existing_claim() -> dict:
    with get_db() as db:
        result = db.execute(text("SELECT id, policy_id FROM claims LIMIT 1")).fetchone()
        if result:
            return {"claim_id": str(result.id), "policy_id": str(result.policy_id)}
        return {}


# ─── get_insurance_policy ─────────────────────────────────────────────────────

def test_get_insurance_policy_success():
    policy_id = get_first_policy_id()
    if policy_id:
        result = get_insurance_policy(policy_id)
        assert "error" not in result
        assert "policy_number" in result
        assert "coverage_amount" in result
        assert "claims" in result


def test_get_insurance_policy_not_found():
    result = get_insurance_policy("00000000-0000-0000-0000-000000000000")
    assert "error" in result


# ─── get_policy_by_booking ────────────────────────────────────────────────────

def test_get_policy_by_booking_with_insurance():
    booking_id = get_first_booking_with_insurance()
    if booking_id:
        result = get_policy_by_booking(booking_id)
        assert result["has_insurance"] is True
        assert "policy_number" in result


def test_get_policy_by_booking_without_insurance():
    with get_db() as db:
        result = db.execute(
            text("""
                SELECT b.id FROM bookings b
                LEFT JOIN insurance_policies p ON p.booking_id = b.id
                WHERE p.id IS NULL LIMIT 1
            """)
        ).fetchone()
        if result:
            check = get_policy_by_booking(str(result.id))
            assert check["has_insurance"] is False


# ─── get_policies_by_customer ─────────────────────────────────────────────────

def test_get_policies_by_customer():
    customer_id = get_first_customer_id()
    result = get_policies_by_customer(customer_id)
    assert "error" not in result
    assert "policies" in result
    assert isinstance(result["policies"], list)


# ─── check_coverage ──────────────────────────────────────────────────────────

def test_check_coverage_covered_type():
    policy_id = get_first_policy_id()
    if policy_id:
        result = check_coverage(policy_id, "trip_cancellation")
        assert "error" not in result
        assert "is_covered" in result
        assert "claim_type" in result


def test_check_coverage_not_found():
    result = check_coverage("00000000-0000-0000-0000-000000000000", "medical")
    assert "error" in result


# ─── check_cancellation_coverage ─────────────────────────────────────────────

def test_check_cancellation_coverage_illness():
    policy_id = get_first_policy_id()
    if policy_id:
        result = check_cancellation_coverage(policy_id, "illness")
        assert "error" not in result
        assert "is_covered" in result
        assert result["is_covered"] is True


def test_check_cancellation_coverage_not_covered():
    policy_id = get_first_policy_id()
    if policy_id:
        result = check_cancellation_coverage(policy_id, "change of mind")
        assert result["is_covered"] is False


# ─── file_claim ───────────────────────────────────────────────────────────────

def test_file_claim_success():
    policy_id = get_first_policy_id()
    if policy_id:
        result = file_claim(
            policy_id=policy_id,
            claim_type="baggage_delay",
            amount_requested=200.0,
            description="Bag delayed 15 hours",
            incident_date="2026-08-01",
        )
        assert "error" not in result
        assert "claim_reference" in result
        assert result["status"] == "filed"


def test_file_claim_capped_at_policy_maximum():
    policy_id = get_first_policy_id()
    if policy_id:
        result = file_claim(
            policy_id=policy_id,
            claim_type="trip_cancellation",
            amount_requested=9999999.0,
            description="Very expensive trip",
            incident_date="2026-08-01",
        )
        if "error" not in result:
            assert result["was_capped"] is True
            assert result["amount_requested"] <= result["original_amount_requested"]


# ─── get_claim_status ─────────────────────────────────────────────────────────

def test_get_claim_status_success():
    existing = get_existing_claim()
    if existing:
        result = get_claim_status(existing["policy_id"], existing["claim_id"])
        assert "error" not in result
        assert "status" in result
        assert "claim_type" in result


# ─── update_insurance_travel_dates ───────────────────────────────────────────

def test_update_insurance_travel_dates():
    policy_id = get_first_policy_id()
    if policy_id:
        result = update_insurance_travel_dates(
            policy_id=policy_id,
            new_start_date="2026-09-01",
            new_end_date="2026-09-15",
        )
        assert "error" not in result
        assert result["new_start_date"] == "2026-09-01"


# ─── compare_plans ───────────────────────────────────────────────────────────

def test_compare_plans():
    result = compare_plans()
    assert "plans" in result
    assert result["count"] == 3
    for plan in result["plans"]:
        assert "plan_id" in plan
        assert "coverages" in plan
        assert "premium_percent" in plan