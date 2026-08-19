"""
services/hotel_service.py
Hotel service — search, booking, modification, and cancellation.
Called by the Travel Inventory MCP Server.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from database.connection import get_db
from database.models import Booking, Hotel, BookingStatus, BookingType
from utils.calculator import calculate_refund_amount, calculate_difference
from utils.date_utils import get_days_until_checkin, calculate_hotel_nights, format_date
from config import settings

logger = logging.getLogger(__name__)


# ─── Helper: apply hotel cancellation policy ──────────────────────────────────

def _calculate_hotel_refund(total_paid: float, check_in_date: datetime, policy: dict) -> dict:
    """
    Apply hotel cancellation policy tiers based on days until check-in.
    Business rule enforced here in code.
    """
    days_left = get_days_until_checkin(check_in_date)
    tiers = policy.get("tiers", [])

    refund_percent = 0
    tier_label = "No refund"

    for tier in tiers:
        if days_left >= tier["days_before"]:
            refund_percent = tier["refund_percent"]
            tier_label = tier["label"]
            break

    refund_amount = calculate_refund_amount(total_paid, refund_percent)
    return {
        "days_until_checkin": round(days_left, 1),
        "refund_percent": refund_percent,
        "refund_amount": refund_amount,
        "tier_label": tier_label,
        "requires_approval": refund_amount > settings.APPROVAL_THRESHOLD_USD,
    }


# ─── 1. search_hotels ─────────────────────────────────────────────────────────

def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    adults: int = 1,
    children: int = 0,
    category: Optional[str] = None,
    min_star_rating: Optional[int] = None,
    max_price_per_night: Optional[float] = None,
    required_amenities: Optional[list] = None,
    meal_plan: Optional[str] = None,
) -> dict:
    """
    Search available hotels with full filtering.
    check_in / check_out format: YYYY-MM-DD
    """
    try:
        check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_dt = datetime.strptime(check_out, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    if check_out_dt <= check_in_dt:
        return {"error": "Check-out must be after check-in"}

    nights = calculate_hotel_nights(check_in_dt, check_out_dt)

    with get_db() as db:
        query = db.query(Hotel).filter(
            Hotel.city.ilike(f"%{city}%"),
            Hotel.is_active == True,
            Hotel.available_rooms > 0,
        )

        if category:
            query = query.filter(Hotel.category == category.lower())
        if min_star_rating:
            query = query.filter(Hotel.star_rating >= min_star_rating)
        if max_price_per_night:
            query = query.filter(Hotel.price_per_night <= max_price_per_night)

        hotels = query.order_by(Hotel.star_rating.desc(), Hotel.price_per_night).all()

        # Filter by amenities and meal plan in Python (JSON columns)
        if required_amenities:
            hotels = [
                h for h in hotels
                if h.amenities and all(a.lower() in [x.lower() for x in h.amenities] for a in required_amenities)
            ]

        if meal_plan:
            hotels = [
                h for h in hotels
                if h.meal_plans and meal_plan.lower() in [m.lower() for m in h.meal_plans]
            ]

        return {
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "nights": nights,
            "guests": adults + children,
            "results": [
                {
                    "hotel_id": str(h.id),
                    "name": h.name,
                    "city": h.city,
                    "country": h.country,
                    "category": h.category,
                    "star_rating": h.star_rating,
                    "price_per_night": h.price_per_night,
                    "total_price": round(h.price_per_night * nights, 2),
                    "available_rooms": h.available_rooms,
                    "amenities": h.amenities or [],
                    "meal_plans": h.meal_plans or [],
                    "room_types": h.room_types or {},
                }
                for h in hotels
            ],
            "count": len(hotels),
        }


# ─── 2. get_hotel_details ─────────────────────────────────────────────────────

def get_hotel_details(hotel_id: str) -> dict:
    """Return complete hotel details including room types, meal plans, and policies."""
    with get_db() as db:
        hotel = db.query(Hotel).filter(Hotel.id == uuid.UUID(hotel_id)).first()
        if not hotel:
            return {"error": f"Hotel {hotel_id} not found"}

        return {
            "hotel_id": str(hotel.id),
            "name": hotel.name,
            "city": hotel.city,
            "country": hotel.country,
            "address": hotel.address,
            "category": hotel.category,
            "star_rating": hotel.star_rating,
            "description": hotel.description,
            "price_per_night": hotel.price_per_night,
            "available_rooms": hotel.available_rooms,
            "total_rooms": hotel.total_rooms,
            "amenities": hotel.amenities or [],
            "room_types": hotel.room_types or {},
            "meal_plans": hotel.meal_plans or [],
            "cancellation_policy": hotel.cancellation_policy,
        }


# ─── 3. get_hotel_booking ─────────────────────────────────────────────────────

def get_hotel_booking(booking_id: str) -> dict:
    """Return full hotel booking details."""
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.HOTEL
        ).first()

        if not booking:
            return {"error": f"Hotel booking {booking_id} not found"}

        hotel = db.query(Hotel).filter(Hotel.id == booking.hotel_id).first()
        nights = 0
        if booking.check_in_date and booking.check_out_date:
            nights = calculate_hotel_nights(booking.check_in_date, booking.check_out_date)

        result = {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "status": booking.status.value,
            "check_in": format_date(booking.check_in_date) if booking.check_in_date else None,
            "check_out": format_date(booking.check_out_date) if booking.check_out_date else None,
            "nights": nights,
            "num_guests": booking.num_guests,
            "room_type": booking.room_type,
            "meal_plan": booking.meal_plan,
            "total_price": booking.total_price,
            "loyalty_points_earned": booking.loyalty_points_earned,
            "special_requests": booking.special_requests,
        }

        if hotel:
            result["hotel"] = {
                "name": hotel.name,
                "city": hotel.city,
                "star_rating": hotel.star_rating,
                "address": hotel.address,
            }

        if booking.status == BookingStatus.CONFIRMED and hotel and hotel.cancellation_policy and booking.check_in_date:
            result["cancellation_terms"] = _calculate_hotel_refund(
                booking.total_price,
                booking.check_in_date,
                hotel.cancellation_policy
            )

        return result


# ─── 4. book_hotel ────────────────────────────────────────────────────────────

def book_hotel(
    hotel_id: str,
    customer_id: str,
    room_type: str,
    check_in: str,
    check_out: str,
    adults: int = 1,
    children: int = 0,
    meal_plan: Optional[str] = None,
    special_requests: Optional[str] = None,
) -> dict:
    """Create a new hotel booking. Deducts room availability."""
    try:
        check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_dt = datetime.strptime(check_out, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    if check_out_dt <= check_in_dt:
        return {"error": "Check-out must be after check-in"}

    with get_db() as db:
        hotel = db.query(Hotel).filter(
            Hotel.id == uuid.UUID(hotel_id),
            Hotel.is_active == True
        ).first()

        if not hotel:
            return {"error": f"Hotel {hotel_id} not found"}

        if hotel.available_rooms < 1:
            return {"error": "No rooms available"}

        if hotel.room_types and room_type not in hotel.room_types:
            return {"error": f"Room type '{room_type}' not available. Options: {list(hotel.room_types.keys())}"}

        if meal_plan and hotel.meal_plans and meal_plan not in hotel.meal_plans:
            return {"error": f"Meal plan '{meal_plan}' not available. Options: {hotel.meal_plans}"}

        nights = calculate_hotel_nights(check_in_dt, check_out_dt)
        room_price = hotel.room_types.get(room_type, hotel.price_per_night) if hotel.room_types else hotel.price_per_night
        total_price = round(room_price * nights, 2)
        loyalty_points = int(total_price * settings.LOYALTY_POINTS_PER_USD)

        booking = Booking(
            id=uuid.uuid4(),
            booking_reference=f"BK{str(uuid.uuid4())[:8].upper()}",
            customer_id=uuid.UUID(customer_id),
            booking_type=BookingType.HOTEL,
            status=BookingStatus.CONFIRMED,
            hotel_id=uuid.UUID(hotel_id),
            check_in_date=check_in_dt,
            check_out_date=check_out_dt,
            num_guests=adults + children,
            room_type=room_type,
            meal_plan=meal_plan,
            total_price=total_price,
            loyalty_points_earned=loyalty_points,
            special_requests=special_requests,
        )
        db.add(booking)
        hotel.available_rooms -= 1
        db.flush()

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "status": "confirmed",
            "hotel_name": hotel.name,
            "city": hotel.city,
            "check_in": check_in,
            "check_out": check_out,
            "nights": nights,
            "room_type": room_type,
            "meal_plan": meal_plan,
            "total_price": total_price,
            "loyalty_points_earned": loyalty_points,
            "message": "Hotel booked successfully",
        }


# ─── 5. cancel_hotel ──────────────────────────────────────────────────────────

def cancel_hotel(booking_id: str, reason: str) -> dict:
    """
    Cancel a hotel booking.
    Refund calculated dynamically based on days until check-in.
    Business rule: refund > APPROVAL_THRESHOLD_USD requires supervisor approval.
    """
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.HOTEL
        ).first()

        if not booking:
            return {"error": f"Hotel booking {booking_id} not found"}

        if booking.status == BookingStatus.CANCELLED:
            return {"error": "Booking is already cancelled"}

        hotel = db.query(Hotel).filter(Hotel.id == booking.hotel_id).first()

        refund_info = {"refund_amount": 0, "refund_percent": 0, "tier_label": "No refund", "requires_approval": False}
        if hotel and hotel.cancellation_policy and booking.check_in_date:
            refund_info = _calculate_hotel_refund(
                booking.total_price,
                booking.check_in_date,
                hotel.cancellation_policy
            )

        booking.status = BookingStatus.CANCELLED
        if hotel:
            hotel.available_rooms += 1
        db.flush()

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "status": "cancelled",
            "cancellation_reason": reason,
            "total_paid": booking.total_price,
            "refund_amount": refund_info["refund_amount"],
            "refund_percent": refund_info["refund_percent"],
            "refund_tier": refund_info["tier_label"],
            "days_until_checkin": refund_info.get("days_until_checkin"),
            "requires_supervisor_approval": refund_info["requires_approval"],
            "message": (
                "Cancellation processed. Refund pending supervisor approval."
                if refund_info["requires_approval"]
                else "Cancellation processed successfully."
            ),
        }


# ─── 6. modify_hotel_booking ──────────────────────────────────────────────────

def modify_hotel_booking(
    booking_id: str,
    new_check_in: Optional[str] = None,
    new_check_out: Optional[str] = None,
    new_room_type: Optional[str] = None,
    new_meal_plan: Optional[str] = None,
    add_special_request: Optional[str] = None,
) -> dict:
    """
    Modify a hotel booking — dates, room type, meal plan, or special requests.
    Calculates any price differences.
    """
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.HOTEL
        ).first()

        if not booking:
            return {"error": f"Hotel booking {booking_id} not found"}

        if booking.status != BookingStatus.CONFIRMED:
            return {"error": f"Cannot modify a {booking.status.value} booking"}

        hotel = db.query(Hotel).filter(Hotel.id == booking.hotel_id).first()
        if not hotel:
            return {"error": "Hotel not found"}

        old_price = booking.total_price
        changes = []

        # Update dates
        if new_check_in:
            booking.check_in_date = datetime.strptime(new_check_in, "%Y-%m-%d")
            changes.append(f"Check-in changed to {new_check_in}")
        if new_check_out:
            booking.check_out_date = datetime.strptime(new_check_out, "%Y-%m-%d")
            changes.append(f"Check-out changed to {new_check_out}")

        # Recalculate price if dates changed
        if new_check_in or new_check_out:
            nights = calculate_hotel_nights(booking.check_in_date, booking.check_out_date)
            room_price = hotel.room_types.get(booking.room_type, hotel.price_per_night) if hotel.room_types else hotel.price_per_night
            booking.total_price = round(room_price * nights, 2)

        # Update room type
        if new_room_type:
            if hotel.room_types and new_room_type not in hotel.room_types:
                return {"error": f"Room type '{new_room_type}' not available"}
            old_room_type = booking.room_type
            booking.room_type = new_room_type
            changes.append(f"Room type changed from {old_room_type} to {new_room_type}")

        # Update meal plan
        if new_meal_plan:
            if hotel.meal_plans and new_meal_plan not in hotel.meal_plans:
                return {"error": f"Meal plan '{new_meal_plan}' not available"}
            booking.meal_plan = new_meal_plan
            changes.append(f"Meal plan changed to {new_meal_plan}")

        # Add special request
        if add_special_request:
            existing = booking.special_requests or ""
            booking.special_requests = f"{existing} | {add_special_request}".strip(" | ")
            changes.append(f"Special request added: {add_special_request}")

        db.flush()

        price_diff = calculate_difference(old_price, booking.total_price)
        additional_charge = max(0, booking.total_price - old_price)

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "changes": changes,
            "old_price": old_price,
            "new_price": booking.total_price,
            "price_difference": price_diff,
            "additional_charge": additional_charge,
            "message": "Booking modified successfully",
        }


# ─── 7. get_bookings_by_customer ──────────────────────────────────────────────

def get_bookings_by_customer(customer_id: str) -> dict:
    """Return all hotel bookings for a customer."""
    with get_db() as db:
        bookings = db.query(Booking).filter(
            Booking.customer_id == uuid.UUID(customer_id),
            Booking.booking_type == BookingType.HOTEL
        ).order_by(Booking.created_at.desc()).all()

        result = []
        for b in bookings:
            hotel = db.query(Hotel).filter(Hotel.id == b.hotel_id).first()
            entry = {
                "booking_id": str(b.id),
                "booking_reference": b.booking_reference,
                "status": b.status.value,
                "check_in": format_date(b.check_in_date) if b.check_in_date else None,
                "check_out": format_date(b.check_out_date) if b.check_out_date else None,
                "room_type": b.room_type,
                "meal_plan": b.meal_plan,
                "total_price": b.total_price,
            }
            if hotel:
                entry["hotel_name"] = hotel.name
                entry["city"] = hotel.city
            result.append(entry)

        return {
            "customer_id": customer_id,
            "hotel_bookings": result,
            "total": len(result),
        }