"""
database/seed_data.py
Seeds the travel_ai database with realistic mock data.
Run with: python -m database.seed_data
"""

import uuid
import random
import logging
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy import text

from database.connection import get_db, engine
from database.models import (
    Base, Customer, Flight, Hotel, Car, Booking,
    InsurancePolicy, Payment, Claim,
    LoyaltyTier, BookingStatus, BookingType,
    PaymentStatus, CabinClass, ClaimStatus, create_tables
)

fake = Faker()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def random_future_date(days_min=1, days_max=90):
    return datetime.utcnow() + timedelta(days=random.randint(days_min, days_max))

def random_past_date(days_min=1, days_max=180):
    return datetime.utcnow() - timedelta(days=random.randint(days_min, days_max))

def booking_reference():
    return f"BK{fake.numerify('########')}"

def policy_number():
    return f"POL{fake.numerify('##########')}"

def claim_reference():
    return f"CLM{fake.numerify('########')}"

def transaction_id():
    return f"TXN{fake.numerify('############')}"


# ─── Standard cancellation policies ──────────────────────────────────────────

FLIGHT_CANCELLATION_POLICY = {
    "tiers": [
        {"hours_before": 72, "refund_percent": 100, "label": "Full refund"},
        {"hours_before": 24, "refund_percent": 50,  "label": "50% refund"},
        {"hours_before": 0,  "refund_percent": 0,   "label": "No refund"},
    ]
}

HOTEL_CANCELLATION_POLICY = {
    "tiers": [
        {"days_before": 7,  "refund_percent": 100, "label": "Full refund"},
        {"days_before": 3,  "refund_percent": 50,  "label": "50% refund"},
        {"days_before": 0,  "refund_percent": 0,   "label": "No refund"},
    ]
}

CAR_CANCELLATION_POLICY = {
    "tiers": [
        {"hours_before": 48, "refund_percent": 100, "label": "Full refund"},
        {"hours_before": 12, "refund_percent": 50,  "label": "50% refund"},
        {"hours_before": 0,  "refund_percent": 0,   "label": "No refund"},
    ]
}


# ─── Seed Customers ───────────────────────────────────────────────────────────

def seed_customers():
    customers = [
        Customer(
            id=uuid.uuid4(),
            email="john.smith@email.com",
            first_name="John",
            last_name="Smith",
            phone="+1-555-0101",
            passport_number="US123456789",
            passport_expiry_date=datetime(2028, 6, 15),
            date_of_birth=datetime(1985, 3, 15),
            nationality="American",
            loyalty_tier=LoyaltyTier.PLATINUM,
            loyalty_points=45000,
            preferences={"meal": "vegetarian", "seat": "window", "language": "en"},
            payment_methods=[
                {"type": "credit_card", "last4": "4242", "brand": "Visa", "is_default": True},
                {"type": "paypal", "email": "john.smith@email.com", "is_default": False},
            ],
        ),
        Customer(
            id=uuid.uuid4(),
            email="sarah.johnson@email.com",
            first_name="Sarah",
            last_name="Johnson",
            phone="+1-555-0102",
            passport_number="US987654321",
            passport_expiry_date=datetime(2027, 3, 20),
            date_of_birth=datetime(1990, 7, 22),
            nationality="American",
            loyalty_tier=LoyaltyTier.GOLD,
            loyalty_points=18500,
            preferences={"meal": "standard", "seat": "aisle", "language": "en"},
            payment_methods=[
                {"type": "credit_card", "last4": "1234", "brand": "Mastercard", "is_default": True},
            ],
        ),
        Customer(
            id=uuid.uuid4(),
            email="ahmed.hassan@email.com",
            first_name="Ahmed",
            last_name="Hassan",
            phone="+971-50-1234567",
            passport_number="AE456789012",
            passport_expiry_date=datetime(2026, 9, 10),
            date_of_birth=datetime(1982, 11, 8),
            nationality="Emirati",
            loyalty_tier=LoyaltyTier.SILVER,
            loyalty_points=7200,
            preferences={"meal": "halal", "seat": "aisle", "language": "ar"},
            payment_methods=[
                {"type": "credit_card", "last4": "5678", "brand": "Amex", "is_default": True},
            ],
        ),
        Customer(
            id=uuid.uuid4(),
            email="priya.patel@email.com",
            first_name="Priya",
            last_name="Patel",
            phone="+91-98765-43210",
            passport_number="IN789012345",
            passport_expiry_date=datetime(2029, 1, 5),
            date_of_birth=datetime(1995, 4, 30),
            nationality="Indian",
            loyalty_tier=LoyaltyTier.BRONZE,
            loyalty_points=1200,
            preferences={"meal": "vegetarian", "seat": "window", "language": "en"},
            payment_methods=[
                {"type": "credit_card", "last4": "9012", "brand": "Visa", "is_default": True},
            ],
        ),
        Customer(
            id=uuid.uuid4(),
            email="emma.wilson@email.com",
            first_name="Emma",
            last_name="Wilson",
            phone="+44-20-7946-0958",
            passport_number="GB234567890",
            passport_expiry_date=datetime(2027, 11, 30),
            date_of_birth=datetime(1988, 9, 12),
            nationality="British",
            loyalty_tier=LoyaltyTier.GOLD,
            loyalty_points=22000,
            preferences={"meal": "standard", "seat": "aisle", "language": "en"},
            payment_methods=[
                {"type": "credit_card", "last4": "3456", "brand": "Visa", "is_default": True},
                {"type": "credit_card", "last4": "7890", "brand": "Mastercard", "is_default": False},
            ],
        ),
        Customer(
            id=uuid.uuid4(),
            email="carlos.mendez@email.com",
            first_name="Carlos",
            last_name="Mendez",
            phone="+34-91-123-4567",
            passport_number="ES345678901",
            passport_expiry_date=datetime(2028, 4, 18),
            date_of_birth=datetime(1979, 6, 18),
            nationality="Spanish",
            loyalty_tier=LoyaltyTier.SILVER,
            loyalty_points=9800,
            preferences={"meal": "standard", "seat": "window", "language": "es"},
            payment_methods=[
                {"type": "credit_card", "last4": "2345", "brand": "Mastercard", "is_default": True},
            ],
        ),
        Customer(
            id=uuid.uuid4(),
            email="yuki.tanaka@email.com",
            first_name="Yuki",
            last_name="Tanaka",
            phone="+81-3-1234-5678",
            passport_number="JP567890123",
            passport_expiry_date=datetime(2026, 7, 22),
            date_of_birth=datetime(1993, 2, 28),
            nationality="Japanese",
            loyalty_tier=LoyaltyTier.BRONZE,
            loyalty_points=3400,
            preferences={"meal": "asian", "seat": "window", "language": "ja"},
            payment_methods=[
                {"type": "credit_card", "last4": "6789", "brand": "Visa", "is_default": True},
            ],
        ),
        Customer(
            id=uuid.uuid4(),
            email="marie.dubois@email.com",
            first_name="Marie",
            last_name="Dubois",
            phone="+33-1-23-45-67-89",
            passport_number="FR678901234",
            passport_expiry_date=datetime(2030, 2, 14),
            date_of_birth=datetime(1986, 12, 5),
            nationality="French",
            loyalty_tier=LoyaltyTier.PLATINUM,
            loyalty_points=67000,
            preferences={"meal": "standard", "seat": "aisle", "language": "fr"},
            payment_methods=[
                {"type": "credit_card", "last4": "1122", "brand": "Amex", "is_default": True},
                {"type": "paypal", "email": "marie.dubois@email.com", "is_default": False},
            ],
        ),
        Customer(
            id=uuid.uuid4(),
            email="david.lee@email.com",
            first_name="David",
            last_name="Lee",
            phone="+65-9123-4567",
            passport_number="SG890123456",
            passport_expiry_date=datetime(2028, 8, 9),
            date_of_birth=datetime(1991, 8, 20),
            nationality="Singaporean",
            loyalty_tier=LoyaltyTier.GOLD,
            loyalty_points=31000,
            preferences={"meal": "standard", "seat": "aisle", "language": "en"},
            payment_methods=[
                {"type": "credit_card", "last4": "3344", "brand": "Visa", "is_default": True},
            ],
        ),
        Customer(
            id=uuid.uuid4(),
            email="anna.kowalski@email.com",
            first_name="Anna",
            last_name="Kowalski",
            phone="+48-22-123-4567",
            passport_number="PL901234567",
            passport_expiry_date=datetime(2027, 5, 27),
            date_of_birth=datetime(1997, 1, 14),
            nationality="Polish",
            loyalty_tier=LoyaltyTier.BRONZE,
            loyalty_points=800,
            preferences={"meal": "standard", "seat": "window", "language": "pl"},
            payment_methods=[
                {"type": "credit_card", "last4": "5566", "brand": "Mastercard", "is_default": True},
            ],
        ),
    ]
    return customers


# ─── Seed Flights ─────────────────────────────────────────────────────────────

def seed_flights():
    routes = [
        ("JFK", "LHR", "New York", "London", "British Airways", "BA178", 420, CabinClass.ECONOMY, 450.0, 180),
        ("JFK", "LHR", "New York", "London", "British Airways", "BA178", 420, CabinClass.BUSINESS, 2800.0, 40),
        ("DXB", "SIN", "Dubai", "Singapore", "Emirates", "EK354", 480, CabinClass.ECONOMY, 380.0, 200),
        ("DXB", "SIN", "Dubai", "Singapore", "Emirates", "EK354", 480, CabinClass.FIRST, 8500.0, 12),
        ("LAX", "NRT", "Los Angeles", "Tokyo", "Japan Airlines", "JL62", 660, CabinClass.ECONOMY, 720.0, 160),
        ("LAX", "NRT", "Los Angeles", "Tokyo", "Japan Airlines", "JL62", 660, CabinClass.BUSINESS, 4200.0, 30),
        ("CDG", "JFK", "Paris", "New York", "Air France", "AF006", 510, CabinClass.ECONOMY, 520.0, 170),
        ("CDG", "JFK", "Paris", "New York", "Air France", "AF006", 510, CabinClass.BUSINESS, 3100.0, 35),
        ("SIN", "LHR", "Singapore", "London", "Singapore Airlines", "SQ321", 780, CabinClass.ECONOMY, 680.0, 150),
        ("SIN", "LHR", "Singapore", "London", "Singapore Airlines", "SQ321", 780, CabinClass.FIRST, 12000.0, 8),
        ("MIA", "GRU", "Miami", "Sao Paulo", "LATAM", "LA8082", 600, CabinClass.ECONOMY, 420.0, 140),
        ("SYD", "LAX", "Sydney", "Los Angeles", "Qantas", "QF12", 840, CabinClass.ECONOMY, 950.0, 120),
        ("SYD", "LAX", "Sydney", "Los Angeles", "Qantas", "QF12", 840, CabinClass.BUSINESS, 5500.0, 28),
        ("ORD", "FRA", "Chicago", "Frankfurt", "Lufthansa", "LH432", 540, CabinClass.ECONOMY, 480.0, 165),
        ("BOM", "DXB", "Mumbai", "Dubai", "Air India", "AI995", 195, CabinClass.ECONOMY, 180.0, 180),
        ("HKG", "LHR", "Hong Kong", "London", "Cathay Pacific", "CX238", 720, CabinClass.ECONOMY, 750.0, 140),
        ("HKG", "LHR", "Hong Kong", "London", "Cathay Pacific", "CX238", 720, CabinClass.BUSINESS, 4800.0, 32),
        ("GVA", "JFK", "Geneva", "New York", "Swiss", "LX22", 480, CabinClass.ECONOMY, 560.0, 120),
        ("AMS", "SIN", "Amsterdam", "Singapore", "KLM", "KL836", 720, CabinClass.ECONOMY, 620.0, 150),
        ("DXB", "JFK", "Dubai", "New York", "Emirates", "EK201", 840, CabinClass.ECONOMY, 580.0, 190),
    ]

    flights = []
    base_date = datetime.utcnow()
    for orig, dest, orig_city, dest_city, airline, fn, dur, cabin, price, seats in routes:
        dep = base_date + timedelta(days=random.randint(1, 60), hours=random.randint(0, 23))
        arr = dep + timedelta(minutes=dur)
        flights.append(Flight(
            id=uuid.uuid4(),
            flight_number=fn,
            airline=airline,
            origin=orig,
            destination=dest,
            origin_city=orig_city,
            destination_city=dest_city,
            departure_time=dep,
            arrival_time=arr,
            duration_minutes=dur,
            cabin_class=cabin,
            price=price,
            available_seats=seats,
            total_seats=seats,
            aircraft_type=random.choice(["Boeing 777", "Airbus A380", "Boeing 787", "Airbus A350"]),
            cancellation_policy=FLIGHT_CANCELLATION_POLICY,
            amenities=["wifi", "meals", "entertainment"] if cabin != CabinClass.ECONOMY else ["meals"],
            is_active=True,
        ))
    return flights


# ─── Seed Hotels ──────────────────────────────────────────────────────────────

def seed_hotels():
    hotels_data = [
        ("The Ritz London", "London", "United Kingdom", "150 Piccadilly, London W1J 9BR",
         "luxury", 5, 850.0, 45, 200,
         ["spa", "pool", "concierge", "restaurant", "bar", "gym", "wifi"],
         {"standard": 850.0, "deluxe": 1200.0, "suite": 2500.0},
         ["room_only", "breakfast", "half_board"]),

        ("citizenM London Shoreditch", "London", "United Kingdom", "6 Holywell Ln, London EC2A 3ET",
         "business", 4, 180.0, 80, 150,
         ["wifi", "bar", "gym", "24h reception"],
         {"standard": 180.0},
         ["room_only"]),

        ("Burj Al Arab", "Dubai", "UAE", "Jumeirah St, Dubai",
         "luxury", 5, 2200.0, 20, 202,
         ["private beach", "helicopter pad", "butler", "pool", "spa", "multiple restaurants"],
         {"junior_suite": 2200.0, "one_bedroom_suite": 4500.0, "royal_suite": 18000.0},
         ["full_board", "half_board"]),

        ("Marriott Al Jaddaf Dubai", "Dubai", "UAE", "Culture Village, Dubai",
         "business", 4, 320.0, 90, 300,
         ["pool", "spa", "gym", "restaurant", "wifi", "bar"],
         {"standard": 320.0, "deluxe": 450.0},
         ["room_only", "breakfast"]),

        ("Mandarin Oriental Tokyo", "Tokyo", "Japan", "2-1-1 Nihonbashi Muromachi, Tokyo",
         "luxury", 5, 750.0, 30, 179,
         ["spa", "pool", "concierge", "multiple restaurants", "gym", "wifi"],
         {"standard": 750.0, "deluxe": 1100.0, "suite": 3200.0},
         ["room_only", "breakfast"]),

        ("Shinjuku Granbell Hotel", "Tokyo", "Japan", "2-14-5 Kabukicho, Shinjuku, Tokyo",
         "leisure", 3, 120.0, 60, 100,
         ["wifi", "restaurant", "bar"],
         {"standard": 120.0, "superior": 160.0},
         ["room_only"]),

        ("Le Grand Hotel Paris", "Paris", "France", "2 Rue Scribe, Paris 75009",
         "luxury", 5, 680.0, 25, 171,
         ["spa", "pool", "concierge", "restaurant", "bar", "wifi"],
         {"classic": 680.0, "deluxe": 950.0, "suite": 2800.0},
         ["room_only", "breakfast"]),

        ("Ibis Paris Gare du Nord", "Paris", "France", "58 Rue La Fayette, Paris 75009",
         "budget", 2, 95.0, 100, 250,
         ["wifi", "restaurant", "24h reception"],
         {"standard": 95.0},
         ["room_only", "breakfast"]),

        ("Marina Bay Sands", "Singapore", "Singapore", "10 Bayfront Avenue, Singapore",
         "luxury", 5, 620.0, 40, 2561,
         ["infinity pool", "casino", "spa", "multiple restaurants", "gym", "shopping mall"],
         {"deluxe": 620.0, "premier": 850.0, "suite": 3500.0},
         ["room_only", "breakfast", "full_board"]),

        ("Pod Singapore", "Singapore", "Singapore", "289 Beach Road, Singapore",
         "leisure", 3, 85.0, 110, 432,
         ["wifi", "restaurant", "bar", "rooftop pool"],
         {"standard": 85.0, "superior": 120.0},
         ["room_only"]),

        ("The Plaza New York", "New York", "USA", "Fifth Avenue at Central Park South, New York",
         "luxury", 5, 950.0, 15, 282,
         ["spa", "concierge", "restaurant", "bar", "gym", "wifi"],
         {"classic": 950.0, "deluxe": 1400.0, "suite": 6000.0},
         ["room_only", "breakfast"]),

        ("Pod 51 Hotel New York", "New York", "USA", "230 E 51st St, New York",
         "budget", 2, 110.0, 95, 665,
         ["wifi", "bar", "rooftop lounge"],
         {"standard": 110.0, "bunk": 75.0},
         ["room_only"]),

        ("Hotel Arts Barcelona", "Barcelona", "Spain", "Carrer de la Marina 19-21, Barcelona",
         "luxury", 5, 480.0, 35, 483,
         ["pool", "beach access", "spa", "restaurant", "bar", "gym", "wifi"],
         {"standard": 480.0, "superior": 650.0, "suite": 2200.0},
         ["room_only", "breakfast", "half_board"]),

        ("Hotel 1898 Barcelona", "Barcelona", "Spain", "La Rambla 109, Barcelona",
         "leisure", 4, 220.0, 55, 169,
         ["pool", "spa", "restaurant", "bar", "wifi"],
         {"standard": 220.0, "superior": 310.0},
         ["room_only", "breakfast"]),

        ("W Hong Kong", "Hong Kong", "China", "1 Austin Road West, Kowloon, Hong Kong",
         "luxury", 5, 520.0, 38, 393,
         ["pool", "spa", "multiple restaurants", "bar", "gym", "wifi"],
         {"wonderful": 520.0, "spectacular": 750.0, "extreme_wow_suite": 5000.0},
         ["room_only", "breakfast"]),
    ]

    hotels = []
    for name, city, country, address, category, stars, price, available, total, amenities, room_types, meal_plans in hotels_data:
        hotels.append(Hotel(
            id=uuid.uuid4(),
            name=name,
            city=city,
            country=country,
            address=address,
            category=category,
            star_rating=stars,
            price_per_night=price,
            available_rooms=available,
            total_rooms=total,
            amenities=amenities,
            room_types=room_types,
            meal_plans=meal_plans,
            cancellation_policy=HOTEL_CANCELLATION_POLICY,
            description=f"A {stars}-star {category} hotel in {city}.",
            is_active=True,
        ))
    return hotels


# ─── Seed Cars ────────────────────────────────────────────────────────────────

def seed_cars():
    cars_data = [
        ("Toyota", "Camry", "economy", "corporate", "New York", 45.0, 5, "automatic", 250, ["AC", "bluetooth", "GPS"]),
        ("BMW", "5 Series", "luxury", "premium", "New York", 120.0, 5, "automatic", None, ["leather seats", "sunroof", "GPS", "AC"]),
        ("Ford", "Explorer", "suv", "corporate", "New York", 85.0, 7, "automatic", 300, ["AC", "GPS", "bluetooth", "third row"]),
        ("Mercedes", "E-Class", "luxury", "premium", "London", 150.0, 5, "automatic", None, ["leather seats", "sunroof", "GPS"]),
        ("Vauxhall", "Astra", "economy", "local", "London", 40.0, 5, "manual", 200, ["AC", "bluetooth"]),
        ("Toyota", "RAV4", "suv", "corporate", "Dubai", 75.0, 5, "automatic", 350, ["AC", "GPS", "4WD", "bluetooth"]),
        ("Nissan", "Altima", "economy", "local", "Dubai", 35.0, 5, "automatic", 200, ["AC", "bluetooth"]),
        ("Honda", "CR-V", "suv", "corporate", "Singapore", 80.0, 5, "automatic", 300, ["AC", "GPS", "bluetooth", "backup camera"]),
        ("Toyota", "Prius", "economy", "local", "Tokyo", 50.0, 5, "automatic", 150, ["AC", "GPS", "hybrid", "bluetooth"]),
        ("Lexus", "ES 350", "luxury", "premium", "Paris", 130.0, 5, "automatic", None, ["leather seats", "sunroof", "GPS", "AC"]),
    ]

    cars = []
    for make, model, category, vendor_type, city, price, seats, transmission, mileage, features in cars_data:
        cars.append(Car(
            id=uuid.uuid4(),
            make=make,
            model=model,
            category=category,
            vendor_type=vendor_type,
            city=city,
            price_per_day=price,
            available=True,
            seats=seats,
            transmission=transmission,
            mileage_limit_per_day=mileage,
            features=features,
            cancellation_policy=CAR_CANCELLATION_POLICY,
            is_active=True,
        ))
    return cars


# ─── Seed Transactions ────────────────────────────────────────────────────────

def seed_transactions(customers, flights, hotels, cars):
    bookings = []
    insurances = []
    payments = []
    claims = []

    # Booking 1: John Smith (Platinum) — flight, confirmed, with insurance
    b1_id = uuid.uuid4()
    b1 = Booking(
        id=b1_id,
        booking_reference=booking_reference(),
        customer_id=customers[0].id,
        booking_type=BookingType.FLIGHT,
        status=BookingStatus.CONFIRMED,
        flight_id=flights[0].id,
        total_price=450.0,
        loyalty_points_earned=450,
        loyalty_points_used=0,
        special_requests="Window seat preferred",
        created_at=random_past_date(30, 60),
    )
    bookings.append(b1)

    ins1_id = uuid.uuid4()
    ins1 = InsurancePolicy(
        id=ins1_id,
        policy_number=policy_number(),
        booking_id=b1_id,
        policy_type="travel",
        coverage_amount=10000.0,
        premium=45.0,
        start_date=flights[0].departure_time,
        end_date=flights[0].departure_time + timedelta(days=14),
        is_active=True,
        policy_details={"type": "comprehensive", "deductible": 100},
    )
    insurances.append(ins1)

    payments.append(Payment(
        id=uuid.uuid4(),
        transaction_id=transaction_id(),
        customer_id=customers[0].id,
        booking_id=b1_id,
        amount=495.0,
        currency="USD",
        status=PaymentStatus.COMPLETED,
        payment_method="credit_card",
        refund_amount=0.0,
        requires_approval=False,
    ))

    # Booking 2: Sarah Johnson (Gold) — hotel, confirmed
    b2_id = uuid.uuid4()
    b2 = Booking(
        id=b2_id,
        booking_reference=booking_reference(),
        customer_id=customers[1].id,
        booking_type=BookingType.HOTEL,
        status=BookingStatus.CONFIRMED,
        hotel_id=hotels[0].id,
        check_in_date=random_future_date(5, 15),
        check_out_date=random_future_date(16, 20),
        num_guests=2,
        room_type="deluxe",
        meal_plan="breakfast",
        total_price=2550.0,
        loyalty_points_earned=2550,
        special_requests="High floor room, late checkout if possible",
        created_at=random_past_date(10, 20),
    )
    bookings.append(b2)

    payments.append(Payment(
        id=uuid.uuid4(),
        transaction_id=transaction_id(),
        customer_id=customers[1].id,
        booking_id=b2_id,
        amount=2550.0,
        currency="USD",
        status=PaymentStatus.COMPLETED,
        payment_method="credit_card",
        refund_amount=0.0,
        requires_approval=False,
    ))

    # Booking 3: Marie Dubois (Platinum) — car, completed
    b3_id = uuid.uuid4()
    b3 = Booking(
        id=b3_id,
        booking_reference=booking_reference(),
        customer_id=customers[7].id,
        booking_type=BookingType.CAR,
        status=BookingStatus.COMPLETED,
        car_id=cars[9].id,
        check_in_date=random_past_date(20, 30),
        check_out_date=random_past_date(10, 19),
        pickup_location="Paris CDG Airport",
        return_location="Paris CDG Airport",
        pickup_time="10:00",
        return_time="18:00",
        total_price=390.0,
        loyalty_points_earned=390,
        created_at=random_past_date(35, 45),
    )
    bookings.append(b3)

    payments.append(Payment(
        id=uuid.uuid4(),
        transaction_id=transaction_id(),
        customer_id=customers[7].id,
        booking_id=b3_id,
        amount=390.0,
        currency="EUR",
        status=PaymentStatus.COMPLETED,
        payment_method="paypal",
        refund_amount=0.0,
        requires_approval=False,
    ))

    # Booking 4: Ahmed Hassan — flight cancelled with large refund (requires approval)
    b4_id = uuid.uuid4()
    b4 = Booking(
        id=b4_id,
        booking_reference=booking_reference(),
        customer_id=customers[2].id,
        booking_type=BookingType.FLIGHT,
        status=BookingStatus.CANCELLED,
        flight_id=flights[2].id,
        total_price=380.0,
        loyalty_points_earned=0,
        created_at=random_past_date(45, 60),
    )
    bookings.append(b4)

    payments.append(Payment(
        id=uuid.uuid4(),
        transaction_id=transaction_id(),
        customer_id=customers[2].id,
        booking_id=b4_id,
        amount=380.0,
        currency="USD",
        status=PaymentStatus.REFUNDED,
        payment_method="credit_card",
        refund_amount=380.0,
        refund_reason="Flight cancelled by customer due to medical emergency",
        requires_approval=True,
        approved_by="supervisor@travelai.com",
    ))

    # Booking 5: Emma Wilson (Gold) — flight confirmed with insurance + filed claim
    b5_id = uuid.uuid4()
    b5 = Booking(
        id=b5_id,
        booking_reference=booking_reference(),
        customer_id=customers[4].id,
        booking_type=BookingType.FLIGHT,
        status=BookingStatus.CONFIRMED,
        flight_id=flights[8].id,
        total_price=680.0,
        loyalty_points_earned=680,
        special_requests="Vegetarian meal",
        created_at=random_past_date(5, 10),
    )
    bookings.append(b5)

    ins5_id = uuid.uuid4()
    ins5 = InsurancePolicy(
        id=ins5_id,
        policy_number=policy_number(),
        booking_id=b5_id,
        policy_type="medical",
        coverage_amount=500000.0,
        premium=68.0,
        start_date=flights[8].departure_time,
        end_date=flights[8].departure_time + timedelta(days=7),
        is_active=True,
        policy_details={"type": "medical_only", "deductible": 0},
    )
    insurances.append(ins5)

    payments.append(Payment(
        id=uuid.uuid4(),
        transaction_id=transaction_id(),
        customer_id=customers[4].id,
        booking_id=b5_id,
        amount=748.0,
        currency="USD",
        status=PaymentStatus.COMPLETED,
        payment_method="credit_card",
        refund_amount=0.0,
        requires_approval=False,
    ))

    # Claim against ins5 — baggage delay claim
    claims.append(Claim(
        id=uuid.uuid4(),
        claim_reference=claim_reference(),
        policy_id=ins5_id,
        claim_type="baggage_delay",
        amount_requested=250.0,
        amount_approved=None,
        status=ClaimStatus.UNDER_REVIEW,
        description="Baggage delayed more than 12 hours on arrival. Purchased essential clothing.",
        incident_date=random_past_date(3, 5),
    ))

    return bookings, insurances, payments, claims


# ─── Main ─────────────────────────────────────────────────────────────────────

def seed_all():
    logger.info("Starting database seeding...")
    create_tables(engine)

    with get_db() as db:
        existing = db.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        if existing > 0:
            logger.info(f"Database already has {existing} customers. Skipping seed.")
            return

        logger.info("Seeding customers...")
        customers = seed_customers()
        db.add_all(customers)
        db.flush()
        logger.info(f"  ✅ {len(customers)} customers created")

        logger.info("Seeding flights...")
        flights = seed_flights()
        db.add_all(flights)
        db.flush()
        logger.info(f"  ✅ {len(flights)} flights created")

        logger.info("Seeding hotels...")
        hotels = seed_hotels()
        db.add_all(hotels)
        db.flush()
        logger.info(f"  ✅ {len(hotels)} hotels created")

        logger.info("Seeding cars...")
        cars = seed_cars()
        db.add_all(cars)
        db.flush()
        logger.info(f"  ✅ {len(cars)} cars created")

        logger.info("Seeding bookings, insurance, payments, claims...")
        bookings, insurances, payments, claims = seed_transactions(customers, flights, hotels, cars)
        db.add_all(bookings)
        db.flush()
        db.add_all(insurances)
        db.flush()
        db.add_all(payments)
        db.flush()
        db.add_all(claims)
        db.flush()
        logger.info(f"  ✅ {len(bookings)} bookings created")
        logger.info(f"  ✅ {len(insurances)} insurance policies created")
        logger.info(f"  ✅ {len(payments)} payments created")
        logger.info(f"  ✅ {len(claims)} claims created")

    logger.info("")
    logger.info("🎉 Database seeding complete!")
    logger.info(f"   Customers:          {len(customers)}")
    logger.info(f"   Flights:            {len(flights)}")
    logger.info(f"   Hotels:             {len(hotels)}")
    logger.info(f"   Cars:               {len(cars)}")
    logger.info(f"   Bookings:           {len(bookings)}")
    logger.info(f"   Insurance Policies: {len(insurances)}")
    logger.info(f"   Payments:           {len(payments)}")
    logger.info(f"   Claims:             {len(claims)}")


if __name__ == "__main__":
    seed_all()