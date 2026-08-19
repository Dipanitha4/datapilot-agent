"""
services/payment_service.py
Payment service — transactions, refunds, charges, and loyalty redemption.
Called by the Financial MCP Server.
Business rule: refund > APPROVAL_THRESHOLD_USD requires supervisor approval.
This rule is enforced here in code — not left to the LLM.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from database.connection import get_db
from database.models import Payment, Booking, Customer, PaymentStatus, BookingType
from utils.calculator import calculate_loyalty_points_value, points_required_for_discount
from utils.date_utils import calculate_refund_expected_date, format_date
from config import settings

logger = logging.getLogger(__name__)


# ─── 1. get_payment_methods ───────────────────────────────────────────────────

def get_payment_methods(customer_id: str) -> dict:
    """Return customer's saved payment methods. Identifies the default one."""
    with get_db() as db:
        customer = db.query(Customer).filter(
            Customer.id == uuid.UUID(customer_id)
        ).first()

        if not customer:
            return {"error": f"Customer {customer_id} not found"}

        methods = customer.payment_methods or []
        default = next((m for m in methods if m.get("is_default")), None)

        return {
            "customer_id": customer_id,
            "payment_methods": methods,
            "default_method": default,
            "count": len(methods),
        }


# ─── 2. get_payment_status ────────────────────────────────────────────────────

def get_payment_status(transaction_id: str) -> dict:
    """Return status and details of a specific transaction."""
    with get_db() as db:
        payment = db.query(Payment).filter(
            Payment.transaction_id == transaction_id
        ).first()

        if not payment:
            return {"error": f"Transaction {transaction_id} not found"}

        return {
            "transaction_id": payment.transaction_id,
            "payment_id": str(payment.id),
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status.value,
            "payment_method": payment.payment_method,
            "refund_amount": payment.refund_amount,
            "refund_reason": payment.refund_reason,
            "requires_approval": payment.requires_approval,
            "approved_by": payment.approved_by,
            "created_at": payment.created_at.strftime("%Y-%m-%d %H:%M"),
        }


# ─── 3. get_customer_transactions ─────────────────────────────────────────────

def get_customer_transactions(
    customer_id: str,
    transaction_type: Optional[str] = None,
    booking_type: Optional[str] = None,
) -> dict:
    """
    Return transaction history for a customer.
    transaction_type: 'payment', 'refund', or None for all
    booking_type: 'flight', 'hotel', 'car', or None for all
    """
    with get_db() as db:
        query = db.query(Payment).filter(
            Payment.customer_id == uuid.UUID(customer_id)
        )

        payments = query.order_by(Payment.created_at.desc()).all()

        # Filter by transaction type
        if transaction_type == "refund":
            payments = [p for p in payments if p.status == PaymentStatus.REFUNDED]
        elif transaction_type == "payment":
            payments = [p for p in payments if p.status == PaymentStatus.COMPLETED]

        # Filter by booking type
        if booking_type:
            booking_ids = [p.booking_id for p in payments]
            bookings = db.query(Booking).filter(Booking.id.in_(booking_ids)).all()
            booking_type_map = {b.id: b.booking_type.value for b in bookings}
            payments = [p for p in payments if booking_type_map.get(p.booking_id) == booking_type.lower()]

        total_spent = sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED)
        total_refunded = sum(p.refund_amount or 0 for p in payments)

        return {
            "customer_id": customer_id,
            "transactions": [
                {
                    "transaction_id": p.transaction_id,
                    "amount": p.amount,
                    "currency": p.currency,
                    "status": p.status.value,
                    "payment_method": p.payment_method,
                    "refund_amount": p.refund_amount,
                    "created_at": p.created_at.strftime("%Y-%m-%d"),
                }
                for p in payments
            ],
            "summary": {
                "total_transactions": len(payments),
                "total_spent": round(total_spent, 2),
                "total_refunded": round(total_refunded, 2),
                "net_spent": round(total_spent - total_refunded, 2),
            },
        }


# ─── 4. process_refund ────────────────────────────────────────────────────────

def process_refund(
    customer_id: str,
    booking_id: str,
    amount: float,
    reason: str,
    refund_method: Optional[str] = None,
) -> dict:
    """
    Initiate a refund for a booking.
    BUSINESS RULE (enforced in code):
    Amounts above APPROVAL_THRESHOLD_USD are flagged for supervisor approval.
    This is NOT left to the LLM to remember.
    """
    with get_db() as db:
        # Find the original payment
        original_payment = db.query(Payment).filter(
            Payment.booking_id == uuid.UUID(booking_id),
            Payment.customer_id == uuid.UUID(customer_id),
            Payment.status == PaymentStatus.COMPLETED,
        ).first()

        if not original_payment:
            return {"error": f"No completed payment found for booking {booking_id}"}

        if amount > original_payment.amount:
            return {
                "error": f"Refund amount ${amount} exceeds original payment ${original_payment.amount}"
            }

        # Business rule enforced here — not relying on LLM
        requires_approval = amount > settings.APPROVAL_THRESHOLD_USD

        refund_transaction = Payment(
            id=uuid.uuid4(),
            transaction_id=f"REF{str(uuid.uuid4())[:12].upper()}",
            customer_id=uuid.UUID(customer_id),
            booking_id=uuid.UUID(booking_id),
            amount=amount,
            currency=original_payment.currency,
            status=PaymentStatus.PENDING if requires_approval else PaymentStatus.REFUNDED,
            payment_method=refund_method or original_payment.payment_method,
            refund_amount=amount,
            refund_reason=reason,
            requires_approval=requires_approval,
        )
        db.add(refund_transaction)

        # Update original payment refund tracking
        original_payment.refund_amount = amount
        original_payment.refund_reason = reason
        original_payment.requires_approval = requires_approval
        if not requires_approval:
            original_payment.status = PaymentStatus.REFUNDED

        db.flush()

        expected_date = calculate_refund_expected_date(datetime.utcnow(), 7)

        return {
            "refund_id": str(refund_transaction.id),
            "transaction_id": refund_transaction.transaction_id,
            "booking_id": booking_id,
            "refund_amount": amount,
            "currency": original_payment.currency,
            "refund_method": refund_transaction.payment_method,
            "status": "pending_approval" if requires_approval else "initiated",
            "requires_supervisor_approval": requires_approval,
            "approval_threshold": settings.APPROVAL_THRESHOLD_USD,
            "expected_completion_date": format_date(expected_date),
            "message": (
                f"Refund of ${amount} requires supervisor approval (exceeds ${settings.APPROVAL_THRESHOLD_USD} threshold)."
                if requires_approval
                else f"Refund of ${amount} initiated. Expected by {format_date(expected_date)}."
            ),
        }


# ─── 5. get_refund_status ────────────────────────────────────────────────────

def get_refund_status(refund_id: str) -> dict:
    """Return current status of a refund transaction."""
    with get_db() as db:
        payment = db.query(Payment).filter(
            Payment.id == uuid.UUID(refund_id)
        ).first()

        if not payment:
            return {"error": f"Refund {refund_id} not found"}

        status_description = {
            PaymentStatus.PENDING: "Awaiting supervisor approval",
            PaymentStatus.COMPLETED: "Refund completed",
            PaymentStatus.REFUNDED: "Refund processed successfully",
            PaymentStatus.FAILED: "Refund failed — contact support",
        }

        return {
            "refund_id": str(payment.id),
            "transaction_id": payment.transaction_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status.value,
            "status_description": status_description.get(payment.status, "Unknown"),
            "requires_approval": payment.requires_approval,
            "approved_by": payment.approved_by,
            "reason": payment.refund_reason,
            "created_at": payment.created_at.strftime("%Y-%m-%d %H:%M"),
        }


# ─── 6. approve_refund ───────────────────────────────────────────────────────

def approve_refund(refund_id: str, approved_by: str) -> dict:
    """
    Supervisor approves a pending refund.
    Changes status from pending to refunded so it processes.
    Only callable from supervisor dashboard — not by customer-facing agents.
    """
    with get_db() as db:
        payment = db.query(Payment).filter(
            Payment.id == uuid.UUID(refund_id),
            Payment.requires_approval == True
        ).first()

        if not payment:
            return {"error": f"Pending refund {refund_id} not found"}

        if payment.status != PaymentStatus.PENDING:
            return {"error": f"Refund is not in pending state (current: {payment.status.value})"}

        payment.status = PaymentStatus.REFUNDED
        payment.approved_by = approved_by
        db.flush()

        return {
            "refund_id": str(payment.id),
            "transaction_id": payment.transaction_id,
            "amount": payment.amount,
            "approved_by": approved_by,
            "status": "refunded",
            "message": f"Refund of ${payment.amount} approved by {approved_by} and processed.",
        }


# ─── 7. charge_customer ──────────────────────────────────────────────────────

def charge_customer(
    customer_id: str,
    booking_id: str,
    amount: float,
    reason: str,
) -> dict:
    """
    Charge customer's default payment method.
    Used for upgrade fees, reschedule fees, extra rental days, etc.
    """
    with get_db() as db:
        customer = db.query(Customer).filter(
            Customer.id == uuid.UUID(customer_id)
        ).first()

        if not customer:
            return {"error": f"Customer {customer_id} not found"}

        methods = customer.payment_methods or []
        default_method = next((m for m in methods if m.get("is_default")), None)

        if not default_method:
            return {"error": "No default payment method on file"}

        payment = Payment(
            id=uuid.uuid4(),
            transaction_id=f"CHG{str(uuid.uuid4())[:12].upper()}",
            customer_id=uuid.UUID(customer_id),
            booking_id=uuid.UUID(booking_id),
            amount=amount,
            currency="USD",
            status=PaymentStatus.COMPLETED,
            payment_method=default_method.get("type", "credit_card"),
            refund_amount=0.0,
            requires_approval=False,
            payment_metadata={"reason": reason, "card_last4": default_method.get("last4")},
        )
        db.add(payment)
        db.flush()

        return {
            "transaction_id": payment.transaction_id,
            "amount": amount,
            "currency": "USD",
            "payment_method": default_method.get("type"),
            "card_last4": default_method.get("last4"),
            "status": "completed",
            "reason": reason,
            "message": f"${amount} charged successfully for: {reason}",
        }


# ─── 8. redeem_points_for_discount ───────────────────────────────────────────

def redeem_points_for_discount(customer_id: str, points_to_redeem: int) -> dict:
    """
    Convert loyalty points to a discount amount.
    Rate: 4 points = $1 (0.25 per point).
    Deducts points from customer balance.
    """
    with get_db() as db:
        customer = db.query(Customer).filter(
            Customer.id == uuid.UUID(customer_id)
        ).first()

        if not customer:
            return {"error": f"Customer {customer_id} not found"}

        if points_to_redeem > customer.loyalty_points:
            return {
                "error": f"Insufficient points. Available: {customer.loyalty_points}, Requested: {points_to_redeem}"
            }

        discount_amount = calculate_loyalty_points_value(
            points_to_redeem,
            rate=settings.POINTS_TO_USD_RATE
        )

        customer.loyalty_points -= points_to_redeem
        db.flush()

        return {
            "customer_id": customer_id,
            "points_redeemed": points_to_redeem,
            "discount_amount": discount_amount,
            "points_remaining": customer.loyalty_points,
            "rate": f"4 points = $1 (${settings.POINTS_TO_USD_RATE} per point)",
            "message": f"Redeemed {points_to_redeem} points for ${discount_amount} discount",
        }


# ─── 9. get_refunds_by_booking ────────────────────────────────────────────────

def get_refunds_by_booking(booking_id: str) -> dict:
    """Return all refunds associated with a specific booking."""
    with get_db() as db:
        payments = db.query(Payment).filter(
            Payment.booking_id == uuid.UUID(booking_id),
            Payment.refund_amount > 0,
        ).all()

        return {
            "booking_id": booking_id,
            "refunds": [
                {
                    "refund_id": str(p.id),
                    "transaction_id": p.transaction_id,
                    "refund_amount": p.refund_amount,
                    "currency": p.currency,
                    "status": p.status.value,
                    "reason": p.refund_reason,
                    "requires_approval": p.requires_approval,
                    "approved_by": p.approved_by,
                    "created_at": p.created_at.strftime("%Y-%m-%d"),
                }
                for p in payments
            ],
            "total_refunded": round(sum(p.refund_amount or 0 for p in payments), 2),
        }