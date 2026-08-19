"""
tests/test_payment_service.py
Tests for payment service functions.
Run with: pytest tests/test_payment_service.py -v
"""

import pytest
from sqlalchemy import text
from database.connection import get_db
from services.payment_service import (
    get_payment_methods,
    get_payment_status,
    get_customer_transactions,
    process_refund,
    get_refund_status,
    approve_refund,
    charge_customer,
    redeem_points_for_discount,
    get_refunds_by_booking,
)


def get_first_customer_id() -> str:
    with get_db() as db:
        result = db.execute(text("SELECT id FROM customers LIMIT 1")).fetchone()
        return str(result.id)


def get_customer_with_points() -> dict:
    with get_db() as db:
        result = db.execute(
            text("SELECT id, loyalty_points FROM customers WHERE loyalty_points > 100 LIMIT 1")
        ).fetchone()
        return {"customer_id": str(result.id), "points": result.loyalty_points} if result else {}


def get_completed_payment() -> dict:
    with get_db() as db:
        result = db.execute(
            text("SELECT id, transaction_id, booking_id, customer_id, amount FROM payments WHERE status = 'COMPLETED'::paymentstatus LIMIT 1")
        ).fetchone()
        if result:
            return {
                "payment_id": str(result.id),
                "transaction_id": result.transaction_id,
                "booking_id": str(result.booking_id),
                "customer_id": str(result.customer_id),
                "amount": result.amount,
            }
        return {}


def get_booking_with_payment() -> dict:
    with get_db() as db:
        result = db.execute(
            text("SELECT booking_id, customer_id FROM payments WHERE status = 'COMPLETED'::paymentstatus LIMIT 1")
        ).fetchone()
        if result:
            return {"booking_id": str(result.booking_id), "customer_id": str(result.customer_id)}
        return {}


# ─── get_payment_methods ──────────────────────────────────────────────────────

def test_get_payment_methods_success():
    customer_id = get_first_customer_id()
    result = get_payment_methods(customer_id)
    assert "error" not in result
    assert "payment_methods" in result
    assert "default_method" in result
    assert isinstance(result["payment_methods"], list)


def test_get_payment_methods_not_found():
    result = get_payment_methods("00000000-0000-0000-0000-000000000000")
    assert "error" in result


# ─── get_payment_status ───────────────────────────────────────────────────────

def test_get_payment_status_success():
    payment = get_completed_payment()
    if payment:
        result = get_payment_status(payment["transaction_id"])
        assert "error" not in result
        assert result["status"] == "completed"
        assert "amount" in result


def test_get_payment_status_not_found():
    result = get_payment_status("TXN_NONEXISTENT_999")
    assert "error" in result


# ─── get_customer_transactions ────────────────────────────────────────────────

def test_get_customer_transactions_all():
    customer_id = get_first_customer_id()
    result = get_customer_transactions(customer_id)
    assert "error" not in result
    assert "transactions" in result
    assert "summary" in result
    assert "total_spent" in result["summary"]


def test_get_customer_transactions_refunds_only():
    customer_id = get_first_customer_id()
    result = get_customer_transactions(customer_id, transaction_type="refund")
    assert "error" not in result
    for t in result["transactions"]:
        assert t["status"] == "refunded"


# ─── process_refund ───────────────────────────────────────────────────────────

def test_process_refund_below_threshold():
    info = get_booking_with_payment()
    if info:
        result = process_refund(
            customer_id=info["customer_id"],
            booking_id=info["booking_id"],
            amount=50.0,
            reason="Test refund below threshold",
        )
        if "error" not in result:
            assert result["requires_supervisor_approval"] is False
            assert result["status"] == "initiated"


def test_process_refund_above_threshold_requires_approval():
    info = get_booking_with_payment()
    if info:
        result = process_refund(
            customer_id=info["customer_id"],
            booking_id=info["booking_id"],
            amount=600.0,
            reason="Large refund test",
        )
        if "error" not in result:
            assert result["requires_supervisor_approval"] is True
            assert result["status"] == "pending_approval"


# ─── charge_customer ──────────────────────────────────────────────────────────

def test_charge_customer_success():
    info = get_booking_with_payment()
    if info:
        result = charge_customer(
            customer_id=info["customer_id"],
            booking_id=info["booking_id"],
            amount=50.0,
            reason="Upgrade fee test",
        )
        assert "error" not in result
        assert result["status"] == "completed"
        assert result["amount"] == 50.0


# ─── redeem_points_for_discount ───────────────────────────────────────────────

def test_redeem_points_success():
    info = get_customer_with_points()
    if info:
        result = redeem_points_for_discount(info["customer_id"], 100)
        assert "error" not in result
        assert result["discount_amount"] == 25.0  # 100 * 0.25
        assert result["points_redeemed"] == 100
        # Restore points
        from services.crm_service import update_loyalty_points
        update_loyalty_points(info["customer_id"], 100, "test restore")


def test_redeem_points_insufficient():
    with get_db() as db:
        # Get customer's actual balance and request more than they have
        result = db.execute(
            text("SELECT id, loyalty_points FROM customers ORDER BY loyalty_points ASC LIMIT 1")
        ).fetchone()
        if result:
            over_limit = result.loyalty_points + 1000
            check = redeem_points_for_discount(str(result.id), over_limit)
            assert "error" in check


# ─── get_refunds_by_booking ───────────────────────────────────────────────────

def test_get_refunds_by_booking():
    with get_db() as db:
        result = db.execute(
            text("SELECT booking_id FROM payments WHERE refund_amount > 0 LIMIT 1")
        ).fetchone()
        if result:
            refunds = get_refunds_by_booking(str(result.booking_id))
            assert "error" not in refunds
            assert "refunds" in refunds
            assert "total_refunded" in refunds