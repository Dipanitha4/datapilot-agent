"""
services/crm_service.py
CRM service — all customer-related database operations.
Called by the Customer MCP Server. Never called directly by agents.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Customer, Booking, LoyaltyTier, BookingStatus
from utils.date_utils import is_passport_valid_for_travel

logger = logging.getLogger(__name__)

# ─── Loyalty tier thresholds ──────────────────────────────────────────────────
LOYALTY_THRESHOLDS = {
    LoyaltyTier.BRONZE:   0,
    LoyaltyTier.SILVER:   5000,
    LoyaltyTier.GOLD:     15000,
    LoyaltyTier.PLATINUM: 40000,
}

def _get_tier_for_points(points: int) -> LoyaltyTier:
    if points >= 40000:
        return LoyaltyTier.PLATINUM
    elif points >= 15000:
        return LoyaltyTier.GOLD
    elif points >= 5000:
        return LoyaltyTier.SILVER
    return LoyaltyTier.BRONZE

def _points_to_next_tier(points: int, current_tier: LoyaltyTier) -> Optional[int]:
    tier_order = [LoyaltyTier.BRONZE, LoyaltyTier.SILVER, LoyaltyTier.GOLD, LoyaltyTier.PLATINUM]
    current_index = tier_order.index(current_tier)
    if current_index == len(tier_order) - 1:
        return None  # already platinum
    next_tier = tier_order[current_index + 1]
    return LOYALTY_THRESHOLDS[next_tier] - points


# ─── 1. get_customer_profile ──────────────────────────────────────────────────

def get_customer_profile(customer_id: str) -> dict:
    """Return full customer profile including preferences and payment methods."""
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == uuid.UUID(customer_id)).first()
        if not customer:
            return {"error": f"Customer {customer_id} not found"}
        return {
            "customer_id": str(customer.id),
            "email": customer.email,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "full_name": f"{customer.first_name} {customer.last_name}",
            "phone": customer.phone,
            "nationality": customer.nationality,
            "passport_number": customer.passport_number,
            "passport_expiry_date": customer.passport_expiry_date.strftime("%Y-%m-%d") if customer.passport_expiry_date else None,
            "date_of_birth": customer.date_of_birth.strftime("%Y-%m-%d") if customer.date_of_birth else None,
            "loyalty_tier": customer.loyalty_tier.value,
            "loyalty_points": customer.loyalty_points,
            "preferences": customer.preferences or {},
            "payment_methods": customer.payment_methods or [],
        }


# ─── 2. get_loyalty_tier ──────────────────────────────────────────────────────

def get_loyalty_tier(customer_id: str) -> dict:
    """Return loyalty tier details, points balance, benefits, and points to next tier."""
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == uuid.UUID(customer_id)).first()
        if not customer:
            return {"error": f"Customer {customer_id} not found"}

        tier_benefits = {
            LoyaltyTier.BRONZE:   ["Standard check-in", "1 point per $1 spent"],
            LoyaltyTier.SILVER:   ["Priority check-in", "1.25x points", "Free seat selection"],
            LoyaltyTier.GOLD:     ["Lounge access", "1.5x points", "Free upgrades when available", "Priority boarding"],
            LoyaltyTier.PLATINUM: ["Unlimited lounge access", "2x points", "Guaranteed upgrades", "Dedicated support line", "Free baggage"],
        }

        points_to_next = _points_to_next_tier(customer.loyalty_points, customer.loyalty_tier)
        return {
            "customer_id": str(customer.id),
            "loyalty_tier": customer.loyalty_tier.value,
            "loyalty_points": customer.loyalty_points,
            "benefits": tier_benefits[customer.loyalty_tier],
            "points_to_next_tier": points_to_next,
            "next_tier": None if points_to_next is None else _get_tier_for_points(
                customer.loyalty_points + points_to_next
            ).value,
            "points_value_usd": round(customer.loyalty_points * 0.25, 2),
        }


# ─── 3. get_booking_history ───────────────────────────────────────────────────

def get_booking_history(customer_id: str) -> dict:
    """Return all bookings for a customer split into active and past."""
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == uuid.UUID(customer_id)).first()
        if not customer:
            return {"error": f"Customer {customer_id} not found"}

        bookings = db.query(Booking).filter(Booking.customer_id == uuid.UUID(customer_id)).all()

        active = []
        history = []
        for b in bookings:
            entry = {
                "booking_id": str(b.id),
                "booking_reference": b.booking_reference,
                "booking_type": b.booking_type.value,
                "status": b.status.value,
                "total_price": b.total_price,
                "created_at": b.created_at.strftime("%Y-%m-%d"),
            }
            if b.status in [BookingStatus.CONFIRMED, BookingStatus.PENDING]:
                active.append(entry)
            else:
                history.append(entry)

        return {
            "customer_id": str(customer.id),
            "full_name": f"{customer.first_name} {customer.last_name}",
            "active_bookings": active,
            "booking_history": history,
            "total_bookings": len(bookings),
        }


# ─── 4. update_loyalty_points ─────────────────────────────────────────────────

def update_loyalty_points(customer_id: str, points_delta: int, reason: str) -> dict:
    """
    Add or subtract loyalty points.
    Automatically upgrades or downgrades tier if threshold is crossed.
    points_delta can be positive (earn) or negative (redeem).
    """
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == uuid.UUID(customer_id)).first()
        if not customer:
            return {"error": f"Customer {customer_id} not found"}

        old_points = customer.loyalty_points
        old_tier = customer.loyalty_tier

        new_points = max(0, old_points + points_delta)
        new_tier = _get_tier_for_points(new_points)

        customer.loyalty_points = new_points
        customer.loyalty_tier = new_tier
        customer.updated_at = datetime.utcnow()
        db.flush()

        tier_changed = old_tier != new_tier
        return {
            "customer_id": str(customer.id),
            "reason": reason,
            "points_before": old_points,
            "points_delta": points_delta,
            "points_after": new_points,
            "tier_before": old_tier.value,
            "tier_after": new_tier.value,
            "tier_changed": tier_changed,
            "tier_upgrade": tier_changed and new_tier != old_tier,
        }


# ─── 5. update_customer_profile ───────────────────────────────────────────────

def update_customer_profile(customer_id: str, updates: dict) -> dict:
    """
    Update allowed customer profile fields.
    Allowed: phone, email, preferences (meal, seat, language).
    Not allowed: passport_number, loyalty_tier, loyalty_points (handled separately).
    """
    ALLOWED_FIELDS = {"phone", "email", "preferences"}
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == uuid.UUID(customer_id)).first()
        if not customer:
            return {"error": f"Customer {customer_id} not found"}

        rejected_fields = [k for k in updates if k not in ALLOWED_FIELDS]
        if rejected_fields:
            return {"error": f"Cannot update restricted fields: {rejected_fields}"}

        for field, value in updates.items():
            setattr(customer, field, value)
        customer.updated_at = datetime.utcnow()
        db.flush()

        return {
            "customer_id": str(customer.id),
            "updated_fields": list(updates.keys()),
            "message": "Profile updated successfully",
        }


# ─── 6. search_customers ──────────────────────────────────────────────────────

def search_customers(
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    tier: Optional[str] = None
) -> dict:
    """Find customers by name, email, phone, or loyalty tier."""
    with get_db() as db:
        query = db.query(Customer)
        if name:
            query = query.filter(
                (Customer.first_name.ilike(f"%{name}%")) |
                (Customer.last_name.ilike(f"%{name}%"))
            )
        if email:
            query = query.filter(Customer.email.ilike(f"%{email}%"))
        if phone:
            query = query.filter(Customer.phone.ilike(f"%{phone}%"))
        if tier:
            query = query.filter(Customer.loyalty_tier == LoyaltyTier(tier.lower()))

        customers = query.limit(20).all()
        return {
            "results": [
                {
                    "customer_id": str(c.id),
                    "full_name": f"{c.first_name} {c.last_name}",
                    "email": c.email,
                    "phone": c.phone,
                    "loyalty_tier": c.loyalty_tier.value,
                    "loyalty_points": c.loyalty_points,
                }
                for c in customers
            ],
            "count": len(customers),
        }


# ─── 7. verify_passport ───────────────────────────────────────────────────────

def verify_passport(customer_id: str, travel_date: str) -> dict:
    """
    Check if passport is valid for travel on given date.
    Most countries require 6 months validity beyond travel date.
    travel_date format: YYYY-MM-DD
    """
    with get_db() as db:
        customer = db.query(Customer).filter(Customer.id == uuid.UUID(customer_id)).first()
        if not customer:
            return {"error": f"Customer {customer_id} not found"}

        if not customer.passport_expiry_date:
            return {
                "customer_id": str(customer.id),
                "passport_number": customer.passport_number,
                "is_valid": False,
                "warning": "No passport expiry date on file. Please update your profile.",
            }

        travel_dt = datetime.strptime(travel_date, "%Y-%m-%d")
        result = is_passport_valid_for_travel(customer.passport_expiry_date, travel_dt)

        return {
            "customer_id": str(customer.id),
            "passport_number": customer.passport_number,
            **result,
        }


# ─── 8. add_booking_to_profile ────────────────────────────────────────────────

def add_booking_to_profile(customer_id: str, booking_id: str) -> dict:
    """Verify a booking belongs to the customer and return confirmation."""
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.customer_id == uuid.UUID(customer_id)
        ).first()

        if not booking:
            return {"error": f"Booking {booking_id} not found for customer {customer_id}"}

        return {
            "customer_id": customer_id,
            "booking_id": booking_id,
            "booking_reference": booking.booking_reference,
            "booking_type": booking.booking_type.value,
            "status": booking.status.value,
            "message": "Booking linked to customer profile",
        }


# ─── 9. move_booking_to_history ───────────────────────────────────────────────

def move_booking_to_history(customer_id: str, booking_id: str) -> dict:
    """
    Mark a booking as COMPLETED and move it to history.
    Called after cancellation or trip completion.
    """
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.customer_id == uuid.UUID(customer_id)
        ).first()

        if not booking:
            return {"error": f"Booking {booking_id} not found for customer {customer_id}"}

        if booking.status == BookingStatus.CANCELLED:
            return {
                "customer_id": customer_id,
                "booking_id": booking_id,
                "booking_reference": booking.booking_reference,
                "status": booking.status.value,
                "message": "Booking already cancelled and moved to history",
            }

        booking.status = BookingStatus.COMPLETED
        booking.updated_at = datetime.utcnow()
        db.flush()

        return {
            "customer_id": customer_id,
            "booking_id": booking_id,
            "booking_reference": booking.booking_reference,
            "previous_status": "confirmed",
            "new_status": "completed",
            "message": "Booking moved to history successfully",
        }