"""
services/car_service.py
Car rental service — search, booking, and management operations.
Called by the Travel Inventory MCP Server.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from database.connection import get_db
from database.models import Booking, Car, Payment, BookingStatus, BookingType, PaymentStatus
from utils.calculator import calculate_refund_amount, calculate_rental_cost
from utils.date_utils import get_hours_until_travel, calculate_rental_duration, format_date, format_datetime
from config import settings

logger = logging.getLogger(__name__)


# ─── Helper: apply car cancellation policy ────────────────────────────────────

def _calculate_car_refund(total_paid: float, pickup_datetime: datetime, policy: dict) -> dict:
    """
    Apply car cancellation policy tiers based on hours until pickup.
    Business rule enforced in code.
    """
    hours_left = get_hours_until_travel(pickup_datetime)
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
        "hours_until_pickup": round(hours_left, 1),
        "refund_percent": refund_percent,
        "refund_amount": refund_amount,
        "tier_label": tier_label,
        "requires_approval": refund_amount > settings.APPROVAL_THRESHOLD_USD,
    }


# ─── 1. search_cars ───────────────────────────────────────────────────────────

def search_cars(
    city: str,
    pickup_date: str,
    return_date: str,
    category: Optional[str] = None,
    passengers: Optional[int] = None,
    transmission: Optional[str] = None,
    max_price_per_day: Optional[float] = None,
    vendor_type: Optional[str] = None,
) -> dict:
    """
    Search available cars with filtering.
    pickup_date / return_date format: YYYY-MM-DD
    """
    try:
        pickup_dt = datetime.strptime(pickup_date, "%Y-%m-%d")
        return_dt = datetime.strptime(return_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    if return_dt <= pickup_dt:
        return {"error": "Return date must be after pickup date"}

    rental_days = calculate_rental_duration(pickup_dt, return_dt)

    with get_db() as db:
        query = db.query(Car).filter(
            Car.city.ilike(f"%{city}%"),
            Car.available == True,
            Car.is_active == True,
        )

        if category:
            query = query.filter(Car.category == category.lower())
        if transmission:
            query = query.filter(Car.transmission == transmission.lower())
        if max_price_per_day:
            query = query.filter(Car.price_per_day <= max_price_per_day)
        if vendor_type:
            query = query.filter(Car.vendor_type == vendor_type.lower())
        if passengers:
            query = query.filter(Car.seats >= passengers)

        cars = query.order_by(Car.price_per_day).all()

        return {
            "city": city,
            "pickup_date": pickup_date,
            "return_date": return_date,
            "rental_days": rental_days,
            "results": [
                {
                    "car_id": str(c.id),
                    "make": c.make,
                    "model": c.model,
                    "category": c.category,
                    "vendor_type": c.vendor_type,
                    "city": c.city,
                    "price_per_day": c.price_per_day,
                    "total_price": round(c.price_per_day * rental_days, 2),
                    "seats": c.seats,
                    "transmission": c.transmission,
                    "mileage_limit_per_day": c.mileage_limit_per_day,
                    "features": c.features or [],
                }
                for c in cars
            ],
            "count": len(cars),
        }


# ─── 2. get_car_details ───────────────────────────────────────────────────────

def get_car_details(car_id: str) -> dict:
    """Return complete car details including features and cancellation policy."""
    with get_db() as db:
        car = db.query(Car).filter(Car.id == uuid.UUID(car_id)).first()
        if not car:
            return {"error": f"Car {car_id} not found"}

        return {
            "car_id": str(car.id),
            "make": car.make,
            "model": car.model,
            "category": car.category,
            "vendor_type": car.vendor_type,
            "city": car.city,
            "price_per_day": car.price_per_day,
            "available": car.available,
            "seats": car.seats,
            "transmission": car.transmission,
            "mileage_limit_per_day": car.mileage_limit_per_day,
            "features": car.features or [],
            "cancellation_policy": car.cancellation_policy,
        }


# ─── 3. get_car_booking ───────────────────────────────────────────────────────

def get_car_booking(booking_id: str) -> dict:
    """Return full car rental booking details."""
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.CAR
        ).first()

        if not booking:
            return {"error": f"Car booking {booking_id} not found"}

        car = db.query(Car).filter(Car.id == booking.car_id).first()
        rental_days = 0
        if booking.check_in_date and booking.check_out_date:
            rental_days = calculate_rental_duration(booking.check_in_date, booking.check_out_date)

        result = {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "status": booking.status.value,
            "pickup_location": booking.pickup_location,
            "return_location": booking.return_location,
            "pickup_date": format_date(booking.check_in_date) if booking.check_in_date else None,
            "return_date": format_date(booking.check_out_date) if booking.check_out_date else None,
            "pickup_time": booking.pickup_time,
            "return_time": booking.return_time,
            "rental_days": rental_days,
            "total_price": booking.total_price,
            "loyalty_points_earned": booking.loyalty_points_earned,
            "special_requests": booking.special_requests,
        }

        if car:
            result["car"] = {
                "make": car.make,
                "model": car.model,
                "category": car.category,
                "transmission": car.transmission,
                "mileage_limit_per_day": car.mileage_limit_per_day,
            }

        return result


# ─── 4. book_car ──────────────────────────────────────────────────────────────

def book_car(
    car_id: str,
    customer_id: str,
    pickup_location: str,
    pickup_date: str,
    pickup_time: str,
    return_location: str,
    return_date: str,
    return_time: str,
    additional_drivers: int = 0,
    child_seats: int = 0,
) -> dict:
    """Create a new car rental booking. Marks car as unavailable."""
    try:
        pickup_dt = datetime.strptime(pickup_date, "%Y-%m-%d")
        return_dt = datetime.strptime(return_date, "%Y-%m-%d")
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD"}

    if return_dt <= pickup_dt:
        return {"error": "Return date must be after pickup date"}

    with get_db() as db:
        car = db.query(Car).filter(
            Car.id == uuid.UUID(car_id),
            Car.available == True,
            Car.is_active == True
        ).first()

        if not car:
            return {"error": f"Car {car_id} not found or unavailable"}

        rental_days = calculate_rental_duration(pickup_dt, return_dt)
        cost_info = calculate_rental_cost(car.price_per_day, rental_days)
        total_price = cost_info["total"]
        loyalty_points = int(total_price * settings.LOYALTY_POINTS_PER_USD)

        extras = []
        if additional_drivers > 0:
            extras.append(f"{additional_drivers} additional driver(s)")
        if child_seats > 0:
            extras.append(f"{child_seats} child seat(s)")

        booking = Booking(
            id=uuid.uuid4(),
            booking_reference=f"BK{str(uuid.uuid4())[:8].upper()}",
            customer_id=uuid.UUID(customer_id),
            booking_type=BookingType.CAR,
            status=BookingStatus.CONFIRMED,
            car_id=uuid.UUID(car_id),
            check_in_date=pickup_dt,
            check_out_date=return_dt,
            pickup_location=pickup_location,
            return_location=return_location,
            pickup_time=pickup_time,
            return_time=return_time,
            total_price=total_price,
            loyalty_points_earned=loyalty_points,
            special_requests=", ".join(extras) if extras else None,
        )
        db.add(booking)
        car.available = False
        db.flush()

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "status": "confirmed",
            "car": f"{car.make} {car.model}",
            "category": car.category,
            "pickup_location": pickup_location,
            "pickup_date": pickup_date,
            "pickup_time": pickup_time,
            "return_location": return_location,
            "return_date": return_date,
            "return_time": return_time,
            "rental_days": rental_days,
            "total_price": total_price,
            "loyalty_points_earned": loyalty_points,
            "message": "Car rental booked successfully",
        }


# ─── 5. cancel_car ────────────────────────────────────────────────────────────

def cancel_car(booking_id: str, reason: str) -> dict:
    """
    Cancel a car rental booking.
    Refund calculated dynamically based on hours until pickup.
    """
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.CAR
        ).first()

        if not booking:
            return {"error": f"Car booking {booking_id} not found"}

        if booking.status == BookingStatus.CANCELLED:
            return {"error": "Booking is already cancelled"}

        car = db.query(Car).filter(Car.id == booking.car_id).first()

        refund_info = {"refund_amount": 0, "refund_percent": 0, "tier_label": "No refund", "requires_approval": False}
        if car and car.cancellation_policy and booking.check_in_date:
            pickup_time = booking.pickup_time or "00:00"
            hour, minute = map(int, pickup_time.split(":"))
            pickup_datetime = booking.check_in_date.replace(hour=hour, minute=minute)
            refund_info = _calculate_car_refund(booking.total_price, pickup_datetime, car.cancellation_policy)

        booking.status = BookingStatus.CANCELLED
        if car:
            car.available = True
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
            "hours_until_pickup": refund_info.get("hours_until_pickup"),
            "requires_supervisor_approval": refund_info["requires_approval"],
            "message": (
                "Cancellation processed. Refund pending supervisor approval."
                if refund_info["requires_approval"]
                else "Cancellation processed successfully."
            ),
        }


# ─── 6. extend_rental ────────────────────────────────────────────────────────

def extend_rental(booking_id: str, new_return_date: str, new_return_time: str) -> dict:
    """Extend car rental to a later return date. Charges extra days at same rate."""
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.CAR
        ).first()

        if not booking:
            return {"error": f"Car booking {booking_id} not found"}

        if booking.status != BookingStatus.CONFIRMED:
            return {"error": f"Cannot extend a {booking.status.value} booking"}

        try:
            new_return_dt = datetime.strptime(new_return_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}

        if new_return_dt <= booking.check_out_date:
            return {"error": "New return date must be after current return date"}

        car = db.query(Car).filter(Car.id == booking.car_id).first()
        if not car:
            return {"error": "Car not found"}

        old_days = calculate_rental_duration(booking.check_in_date, booking.check_out_date)
        new_days = calculate_rental_duration(booking.check_in_date, new_return_dt)
        extra_days = new_days - old_days
        extra_charge = round(car.price_per_day * extra_days, 2)

        booking.check_out_date = new_return_dt
        booking.return_time = new_return_time
        booking.total_price = round(booking.total_price + extra_charge, 2)
        db.flush()

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "old_return_date": format_date(booking.check_out_date),
            "new_return_date": new_return_date,
            "extra_days": extra_days,
            "extra_charge": extra_charge,
            "new_total_price": booking.total_price,
            "message": f"Rental extended by {extra_days} day(s). Additional charge: ${extra_charge}",
        }


# ─── 7. change_pickup_location ────────────────────────────────────────────────

def change_pickup_location(booking_id: str, new_pickup_location: str) -> dict:
    """Change the pickup location for a car rental."""
    with get_db() as db:
        booking = db.query(Booking).filter(
            Booking.id == uuid.UUID(booking_id),
            Booking.booking_type == BookingType.CAR
        ).first()

        if not booking:
            return {"error": f"Car booking {booking_id} not found"}

        if booking.status != BookingStatus.CONFIRMED:
            return {"error": f"Cannot modify a {booking.status.value} booking"}

        old_location = booking.pickup_location
        booking.pickup_location = new_pickup_location
        db.flush()

        return {
            "booking_id": str(booking.id),
            "booking_reference": booking.booking_reference,
            "old_pickup_location": old_location,
            "new_pickup_location": new_pickup_location,
            "message": "Pickup location updated successfully",
        }


# ─── 8. get_bookings_by_customer ──────────────────────────────────────────────

def get_bookings_by_customer(customer_id: str) -> dict:
    """Return all car rental bookings for a customer."""
    with get_db() as db:
        bookings = db.query(Booking).filter(
            Booking.customer_id == uuid.UUID(customer_id),
            Booking.booking_type == BookingType.CAR
        ).order_by(Booking.created_at.desc()).all()

        result = []
        for b in bookings:
            car = db.query(Car).filter(Car.id == b.car_id).first()
            entry = {
                "booking_id": str(b.id),
                "booking_reference": b.booking_reference,
                "status": b.status.value,
                "pickup_location": b.pickup_location,
                "pickup_date": format_date(b.check_in_date) if b.check_in_date else None,
                "return_date": format_date(b.check_out_date) if b.check_out_date else None,
                "total_price": b.total_price,
            }
            if car:
                entry["car"] = f"{car.make} {car.model}"
                entry["category"] = car.category
            result.append(entry)

        return {
            "customer_id": customer_id,
            "car_bookings": result,
            "total": len(result),
        }