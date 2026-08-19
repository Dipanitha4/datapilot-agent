"""
services/flight_service.py
Flight service — all flight search, booking, and management operations.
Called by the Travel Inventory MCP Server. Never called directly by agents.
Business rules (refund tiers, approval thresholds) are enforced here in code,
not left to the LLM.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from database.connection import get_db
from database.models import (
    Flight, Booking, Payment,
    BookingStatus, BookingType, PaymentStatus, CabinClass
)
from utils.calculator import calculate_refund_amount, calculate_upgrade_cost, calculate_difference
from utils.date_utils import get_hours_until_travel, format_datetime
from config import settings

logger = logging.getLogger(__name__)


# ─── Helper: apply cancellation policy ────────────────────────────────────────

def _calculate_flight_refund(total_paid: float, departure_time: datetime, policy: dict) -> dict:
    """
    Apply cancellation policy tiers based on hours until departure.
    Returns refund amount and applicable tier label.
    Business rule enforced here — not in the LLM prompt.
    """
    hours_left = get_hours_until_travel(departure_time)
    tiers = policy.get("tiers", [])

    refund_percent = 0
    tier_label = "No refund"

    for tier in tiers:
        if hours_left >= tier["hours_before"]:
            refund_percent = tier["refund_percent"]
            tier_label = tier["label"]
            break

    refund_amount = calculate_refund_amount(total_paid, refund_percent)
    return {
        "hours_until_departure": round(hours_left, 1),
        "refund_percent": refund_percent,
        "refund_amount": refund_amount,
        "tier_label": tier_label,
        "requires_approval": refund_amount > settings.APPROVAL_THRESHOLD_USD,
    }


# ─── 1. search_flights ────────────────────────────────────────────────────────

def search_flights(
    origin: str,
    destination: str,
    travel_date: str,
    cabin_class: Optional[str] = None,
    passengers: int = 1,
    preferred_airline: Optional[str] = None,
    max_price: Optional[float] = None,
) -> dict:
    """
    Search available flights by route and filters.
    travel_date format: YYYY-MM-DD
    Returns flights sorted by price ascending.
    """
    with get_db() as db:
        query = db.query(Flight).filter(
            Flight.origin == origin.upper(),
            Flight.destination == destination.upper(),
            Flight.is_active == True,
            Flight.available_seats >= passengers,
        )

        if cabin_class:
            query = query.filter(Flight.cabin_class == CabinClass(cabin_class.lower()))
        if preferred_airline:
            query = query.filter(Flight.airline.ilike(f"%{preferred_airline}%"))
        if max_price:
            query = query.filter(Flight.price <= max_price)

        # Filter by travel date (same day)
        try:
            travel_dt = datetime.strptime(travel_date, "%Y-%m-%d")
            query = query.filter(
                Flight.departure_time >= travel_dt.replace(hour=0, minute=0),
                Flight.departure_time <= travel_dt.replace(hour=23, minute=59),
            )
        except ValueError:
            return {"error": f"Invalid travel_date format: {travel_date}. Use YYYY-MM-DD"}

        flights = query.order_by(Flight.price).all()

        return {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "travel_date": travel_date,
            "passengers": passengers,
            "results": [
                {
                    "flight_id": str(f.id),
                    "flight_number": f.flight_number,
                    "airline": f.airline,
                    "origin": f.origin,
                    "destination": f.destination,
                    "departure_time": format_datetime(f.departure_time),
                    "arrival_time": format_datetime(f.arrival_time),
                    "duration_minutes": f.duration_minutes,
                    "cabin_class": f.cabin_class.value,
                    "price": f.price,
                    "price_per_passenger": f.price,
                    "total_price": round(f.price * passengers, 2),
                    "available_seats": f.available_seats,
                    "aircraft_type": f.aircraft_type,
                    "amenities": f.amenities or [],
                }
                for f in flights
            ],
            "count": len(flights),
        }


# ─── 2. search_flexible_dates ─────────────────────────────────────────────────

def search_flexible_dates(
    origin: str,
    destination: str,
    dates: list,
    cabin_class: Optional[str] = None,
    passengers: int = 1,
) -> dict:
    """
    Search across multiple dates and return cheapest option per date.
    dates: list of YYYY-MM-DD strings
    """
    results_by_date = {}
    cheapest_overall = None
    cheapest_date = None

    for date in dates:
        result = search_flights(origin, destination, date, cabin_class, passengers)
        if result.get("count", 0) > 0:
            cheapest_on_date = result["results"][0]
            results_by_date[date] = {
                "cheapest_flight": cheapest_on_date,
                "flights_available": result["count"],
            }
            if cheapest_overall is None or cheapest_on_date["price"] < cheapest_overall["price"]:
                cheapest_overall = cheapest_on_date
                cheapest_date = date
        else:
            results_by_date[date] = {"cheapest_flight": None, "flights_available": 0}

    return {
        "origin": origin.upper(),
        "destination": destination.upper(),
        "dates_searched": dates,
        "results_by_date": results_by_date,
        "recommendation": {
            "cheapest_date": cheapest_date,
            "cheapest_flight": cheapest_overall,
        },
    }


# ─── 3. get_flight_details ────────────────────────────────────────────────────

def get_flight_details(flight_id: str) -> dict:
    """Return complete flight details including cancellation policy."""
    with get_db() as db:
        flight = db.query(Flight).filter(Flight.id == uuid.UUID(flight_id)).first()
        if not flight:
            return {"error": f"Flight {flight_id} not found"}

        return {
            "flight_id": str(flight.id),
            "flight_number": flight.flight_number,
            "airline": flight.airline,
            "origin": flight.origin,
            "origin_city": flight.origin_city,
            "destination": flight.destination,
            "destination_city": flight.destination_city,
            "departure_time": format_datetime(flight.departure_time),
            "arrival_time": format_datetime(flight.arrival_time),
            "duration_minutes": flight.duration_minutes,
            "cabin_class": flight.cabin_class.value,
            "price": flight.price,
            "available_seats": flight.available_seats,
            "total_seats": flight.total_seats,
            "aircraft_type": flight.aircraft_type,
            "amenities": flight.amenities or [],
            "cancellation_policy": flight.cancellation_policy,
        }


# ─── 4. get_flight_booking ────────────────────────────────────────────────────

def get_flight_booking(booking_id: str) -> dict:
    """Return full booking details for a flight booking."""
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.FLIGHT
        ).first()

        if not booking:
            return {"error": f"Flight booking {booking_id} not found"}

        flight = db.query(Flight).filter(Flight.id == booking.flight_id).first()

        result = {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "status": booking.status.value,
            "total_price": booking.total_price,
            "loyalty_points_earned": booking.loyalty_points_earned,
            "special_requests": booking.special_requests,
            "created_at": booking.created_at.strftime("%Y-%m-%d"),
        }

        if flight:
            result["flight"] = {
                "flight_number": flight.flight_number,
                "airline": flight.airline,
                "origin": flight.origin,
                "destination": flight.destination,
                "departure_time": format_datetime(flight.departure_time),
                "arrival_time": format_datetime(flight.arrival_time),
                "cabin_class": flight.cabin_class.value,
            }

            # Check cancellation eligibility
            if booking.status == BookingStatus.CONFIRMED and flight.cancellation_policy:
                refund_info = _calculate_flight_refund(
                    booking.total_price,
                    flight.departure_time,
                    flight.cancellation_policy
                )
                result["cancellation_eligibility"] = refund_info

        return result


# ─── 5. book_flight ───────────────────────────────────────────────────────────

def book_flight(
    flight_id: str,
    customer_id: str,
    cabin_class: str,
    passengers: int = 1,
    meal_preferences: Optional[str] = None,
    special_requests: Optional[str] = None,
) -> dict:
    """
    Create a new flight booking.
    Deducts seat availability.
    Calculates loyalty points earned (1 point per $1).
    """
    with get_db() as db:
        flight = db.query(Flight).filter(
            Flight.id == uuid.UUID(flight_id),
            Flight.is_active == True
        ).first()

        if not flight:
            return {"error": f"Flight {flight_id} not found or inactive"}

        if flight.available_seats < passengers:
            return {
                "error": f"Insufficient seats. Available: {flight.available_seats}, Requested: {passengers}"
            }

        if flight.cabin_class != CabinClass(cabin_class.lower()):
            return {"error": f"Flight {flight_id} is not a {cabin_class} flight"}

        total_price = round(flight.price * passengers, 2)
        loyalty_points = int(total_price * settings.LOYALTY_POINTS_PER_USD)

        special = []
        if meal_preferences:
            special.append(f"Meal: {meal_preferences}")
        if special_requests:
            special.append(special_requests)

        booking = Booking(
            id=uuid.uuid4(),
            booking_reference=f"BK{str(uuid.uuid4())[:8].upper()}",
            customer_id=uuid.UUID(customer_id),
            booking_type=BookingType.FLIGHT,
            status=BookingStatus.CONFIRMED,
            flight_id=uuid.UUID(flight_id),
            num_guests=passengers,
            total_price=total_price,
            loyalty_points_earned=loyalty_points,
            special_requests=" | ".join(special) if special else None,
        )
        db.add(booking)

        # Deduct seat availability
        flight.available_seats -= passengers
        db.flush()

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "status": "confirmed",
            "flight_number": flight.flight_number,
            "airline": flight.airline,
            "origin": flight.origin,
            "destination": flight.destination,
            "departure_time": format_datetime(flight.departure_time),
            "cabin_class": cabin_class,
            "passengers": passengers,
            "total_price": total_price,
            "loyalty_points_earned": loyalty_points,
            "message": "Flight booked successfully",
        }


# ─── 6. cancel_flight ────────────────────────────────────────────────────────

def cancel_flight(booking_id: str, reason: str) -> dict:
    """
    Cancel a flight booking.
    Refund calculated dynamically based on hours until departure.
    Business rule: refund > APPROVAL_THRESHOLD_USD requires supervisor approval.
    This rule is enforced here in code — not relying on LLM memory.
    """
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.FLIGHT
        ).first()

        if not booking:
            return {"error": f"Flight booking {booking_id} not found"}

        if booking.status == BookingStatus.CANCELLED:
            return {"error": "Booking is already cancelled"}

        if booking.status == BookingStatus.COMPLETED:
            return {"error": "Cannot cancel a completed booking"}

        flight = db.query(Flight).filter(Flight.id == booking.flight_id).first()

        refund_info = {"refund_amount": 0, "refund_percent": 0, "tier_label": "No refund", "requires_approval": False}
        if flight and flight.cancellation_policy:
            refund_info = _calculate_flight_refund(
                booking.total_price,
                flight.departure_time,
                flight.cancellation_policy
            )

        # Update booking status
        booking.status = BookingStatus.CANCELLED
        db.flush()

        # Restore seat availability
        if flight:
            flight.available_seats += booking.num_guests
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
            "hours_until_departure": refund_info.get("hours_until_departure"),
            "requires_supervisor_approval": refund_info["requires_approval"],
            "message": (
                "Cancellation processed. Refund pending supervisor approval."
                if refund_info["requires_approval"]
                else "Cancellation processed successfully."
            ),
        }


# ─── 7. check_cancellation_terms ─────────────────────────────────────────────

def check_cancellation_terms(booking_id: str) -> dict:
    """
    Check what refund the customer would get RIGHT NOW if they cancel.
    Read-only — does not cancel the booking.
    """
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.FLIGHT
        ).first()

        if not booking:
            return {"error": f"Flight booking {booking_id} not found"}

        if booking.status != BookingStatus.CONFIRMED:
            return {
                "booking_id": str(booking.id),
                "booking_reference": booking.booking_reference,
                "status": booking.status.value,
                "message": f"Booking is {booking.status.value} — cancellation terms not applicable",
            }

        flight = db.query(Flight).filter(Flight.id == booking.flight_id).first()

        if not flight or not flight.cancellation_policy:
            return {"error": "Cannot determine cancellation terms — no policy found"}

        refund_info = _calculate_flight_refund(
            booking.total_price,
            flight.departure_time,
            flight.cancellation_policy
        )

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "total_paid": booking.total_price,
            "departure_time": format_datetime(flight.departure_time),
            "hours_until_departure": refund_info["hours_until_departure"],
            "if_cancelled_now": {
                "refund_amount": refund_info["refund_amount"],
                "refund_percent": refund_info["refund_percent"],
                "tier": refund_info["tier_label"],
                "requires_supervisor_approval": refund_info["requires_approval"],
            },
            "full_policy": flight.cancellation_policy,
        }


# ─── 8. reschedule_flight ─────────────────────────────────────────────────────

def reschedule_flight(
    booking_id: str,
    new_flight_id: str,
) -> dict:
    """
    Reschedule a flight booking to a different flight.
    If new flight is more expensive, customer pays the difference.
    If cheaper, no refund (standard policy).
    """
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.FLIGHT
        ).first()

        if not booking:
            return {"error": f"Booking {booking_id} not found"}

        if booking.status != BookingStatus.CONFIRMED:
            return {"error": f"Cannot reschedule a {booking.status.value} booking"}

        new_flight = db.query(Flight).filter(
            Flight.id == uuid.UUID(new_flight_id),
            Flight.is_active == True
        ).first()

        if not new_flight:
            return {"error": f"New flight {new_flight_id} not found or inactive"}

        if new_flight.available_seats < booking.num_guests:
            return {"error": f"New flight has insufficient seats: {new_flight.available_seats}"}

        old_flight = db.query(Flight).filter(Flight.id == booking.flight_id).first()
        old_price = booking.total_price
        new_price = round(new_flight.price * booking.num_guests, 2)
        price_difference = calculate_difference(old_price, new_price)
        additional_charge = max(0, new_price - old_price)

        # Restore old flight seats
        if old_flight:
            old_flight.available_seats += booking.num_guests

        # Update booking
        booking.flight_id = new_flight.id
        booking.total_price = new_price
        new_flight.available_seats -= booking.num_guests
        db.flush()

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "new_flight_number": new_flight.flight_number,
            "new_departure_time": format_datetime(new_flight.departure_time),
            "old_price": old_price,
            "new_price": new_price,
            "price_difference": price_difference,
            "additional_charge": additional_charge,
            "message": (
                f"Reschedule successful. Additional charge of ${additional_charge}"
                if additional_charge > 0
                else "Reschedule successful. No additional charge."
            ),
        }


# ─── 9. upgrade_cabin ────────────────────────────────────────────────────────

def upgrade_cabin(booking_id: str, target_cabin: str) -> dict:
    """
    Upgrade a booking to a higher cabin class.
    Finds the same route in the target cabin and charges the difference.
    """
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.FLIGHT
        ).first()

        if not booking:
            return {"error": f"Booking {booking_id} not found"}

        if booking.status != BookingStatus.CONFIRMED:
            return {"error": f"Cannot upgrade a {booking.status.value} booking"}

        current_flight = db.query(Flight).filter(Flight.id == booking.flight_id).first()
        if not current_flight:
            return {"error": "Current flight not found"}

        target_cabin_enum = CabinClass(target_cabin.lower())
        if current_flight.cabin_class == target_cabin_enum:
            return {"error": f"Booking is already in {target_cabin} class"}

        # Find upgrade flight — same route, same day, target cabin
        upgrade_flight = db.query(Flight).filter(
            Flight.origin == current_flight.origin,
            Flight.destination == current_flight.destination,
            Flight.flight_number == current_flight.flight_number,
            Flight.cabin_class == target_cabin_enum,
            Flight.is_active == True,
            Flight.available_seats >= booking.num_guests,
        ).first()

        if not upgrade_flight:
            return {"error": f"No {target_cabin} availability on this flight"}

        upgrade_cost = calculate_upgrade_cost(
            current_flight.price,
            upgrade_flight.price
        ) * booking.num_guests

        # Update booking
        current_flight.available_seats += booking.num_guests
        booking.flight_id = upgrade_flight.id
        booking.total_price = round(upgrade_flight.price * booking.num_guests, 2)
        upgrade_flight.available_seats -= booking.num_guests
        db.flush()

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "upgraded_from": current_flight.cabin_class.value,
            "upgraded_to": target_cabin,
            "upgrade_cost": upgrade_cost,
            "new_total_price": booking.total_price,
            "message": f"Upgrade to {target_cabin} successful. Charge: ${upgrade_cost}",
        }


# ─── 10. get_bookings_by_customer ─────────────────────────────────────────────

def get_bookings_by_customer(customer_id: str) -> dict:
    """Return all flight bookings for a customer, separated into active and cancelled."""
    with get_db() as db:
        bookings = db.query(Booking).filter(
            Booking.customer_id == uuid.UUID(customer_id),
            Booking.booking_type == BookingType.FLIGHT
        ).order_by(Booking.created_at.desc()).all()

        active = []
        cancelled = []

        for b in bookings:
            flight = db.query(Flight).filter(Flight.id == b.flight_id).first()
            entry = {
                "booking_id": str(b.id),
                "booking_reference": b.booking_reference,
                "status": b.status.value,
                "total_price": b.total_price,
                "created_at": b.created_at.strftime("%Y-%m-%d"),
            }
            if flight:
                entry["flight"] = {
                    "flight_number": flight.flight_number,
                    "route": f"{flight.origin} → {flight.destination}",
                    "departure_time": format_datetime(flight.departure_time),
                    "cabin_class": flight.cabin_class.value,
                }

            if b.status == BookingStatus.CONFIRMED:
                active.append(entry)
            else:
                cancelled.append(entry)

        return {
            "customer_id": customer_id,
            "active_flights": active,
            "cancelled_flights": cancelled,
            "total": len(bookings),
        }
