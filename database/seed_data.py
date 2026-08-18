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
    InsurancePolicy, Payment,
    LoyaltyTier, BookingStatus, BookingType,
    PaymentStatus, CabinClass, create_tables
)

fake = Faker()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── Helper Functions ─────────────────────────────────────────────────────────

def random_future_date(days_min=1, days_max=90):
    return datetime.utcnow() + timedelta(days=random.randint(days_min, days_max))

def random_past_date(days_min=1, days_max=180):
    return datetime.utcnow() - timedelta(days=random.randint(days_min, days_max))

def booking_reference():
    return f"BK{fake.numerify('########')}"

def policy_number():
    return f"POL{fake.numerify('##########')}"

def transaction_id():
    return f"TXN{fake.numerify('############')}"


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
            date_of_birth=datetime(1985, 3, 15),
            nationality="American",
            loyalty_tier=LoyaltyTier.PLATINUM,
            loyalty_points=45000,
        ),
        Customer(
            id=uuid.uuid4(),
            email="sarah.johnson@email.com",
            first_name="Sarah",
            last_name="Johnson",
            phone="+1-555-0102",
            passport_number="US987654321",
            date_of_birth=datetime(1990, 7, 22),
            nationality="American",
            loyalty_tier=LoyaltyTier.GOLD,
            loyalty_points=18500,
        ),
        Customer(
            id=uuid.uuid4(),
            email="ahmed.hassan@email.com",
            first_name="Ahmed",
            last_name="Hassan",
            phone="+971-50-1234567",
            passport_number="AE456789012",
            date_of_birth=datetime(1982, 11, 8),
            nationality="Emirati",
            loyalty_tier=LoyaltyTier.SILVER,
            loyalty_points=7200,
        ),
        Customer(
            id=uuid.uuid4(),
            email="priya.patel@email.com",
            first_name="Priya",
            last_name="Patel",
            phone="+91-98765-43210",
            passport_number="IN789012345",
            date_of_birth=datetime(1995, 4, 30),
            nationality="Indian",
            loyalty_tier=LoyaltyTier.BRONZE,
            loyalty_points=1200,
        ),
        Customer(
            id=uuid.uuid4(),
            email="emma.wilson@email.com",
            first_name="Emma",
            last_name="Wilson",
            phone="+44-20-7946-0958",
            passport_number="GB234567890",
            date_of_birth=datetime(1988, 9, 12),
            nationality="British",
            loyalty_tier=LoyaltyTier.GOLD,
            loyalty_points=22000,
        ),
        Customer(
            id=uuid.uuid4(),
            email="carlos.mendez@email.com",
            first_name="Carlos",
            last_name="Mendez",
            phone="+34-91-123-4567",
            passport_number="ES345678901",
            date_of_birth=datetime(1979, 6, 18),
            nationality="Spanish",
            loyalty_tier=LoyaltyTier.SILVER,
            loyalty_points=9800,
        ),
        Customer(
            id=uuid.uuid4(),
            email="yuki.tanaka@email.com",
            first_name="Yuki",
            last_name="Tanaka",
            phone="+81-3-1234-5678",
            passport_number="JP567890123",
            date_of_birth=datetime(1993, 2, 28),
            nationality="Japanese",
            loyalty_tier=LoyaltyTier.BRONZE,
            loyalty_points=3400,
        ),
        Customer(
            id=uuid.uuid4(),
            email="marie.dubois@email.com",
            first_name="Marie",
            last_name="Dubois",
            phone="+33-1-23-45-67-89",
            passport_number="FR678901234",
            date_of_birth=datetime(1986, 12, 5),
            nationality="French",
            loyalty_tier=LoyaltyTier.PLATINUM,
            loyalty_points=67000,
        ),
        Customer(
            id=uuid.uuid4(),
            email="david.lee@email.com",
            first_name="David",
            last_name="Lee",
            phone="+65-9123-4567",
            passport_number="SG890123456",
            date_of_birth=datetime(1991, 8, 20),
            nationality="Singaporean",
            loyalty_tier=LoyaltyTier.GOLD,
            loyalty_points=31000,
        ),
        Customer(
            id=uuid.uuid4(),
            email="anna.kowalski@email.com",
            first_name="Anna",
            last_name="Kowalski",
            phone="+48-22-123-4567",
            passport_number="PL901234567",
            date_of_birth=datetime(1997, 1, 14),
            nationality="Polish",
            loyalty_tier=LoyaltyTier.BRONZE,
            loyalty_points=800,
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

    for i, (orig, dest, orig_city, dest_city, airline, fn, dur, cabin, price, seats) in enumerate(routes):
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
            is_active=True,
        ))

    return flights


# ─── Seed Hotels ──────────────────────────────────────────────────────────────

def seed_hotels():
    hotels_data = [
        ("The Ritz London", "London", "United Kingdom", "150 Piccadilly, London W1J 9BR", 5, 850.0, 45, 200,
         ["spa", "pool", "concierge", "restaurant", "bar", "gym", "wifi"]),
        ("citizenM London Shoreditch", "London", "United Kingdom", "6 Holywell Ln, London EC2A 3ET", 4, 180.0, 80, 150,
         ["wifi", "bar", "gym", "24h reception"]),
        ("Burj Al Arab", "Dubai", "UAE", "Jumeirah St, Dubai", 5, 2200.0, 20, 202,
         ["private beach", "helicopter pad", "butler", "pool", "spa", "multiple restaurants"]),
        ("Marriott Al Jaddaf Dubai", "Dubai", "UAE", "Culture Village, Dubai", 4, 320.0, 90, 300,
         ["pool", "spa", "gym", "restaurant", "wifi", "bar"]),
        ("Mandarin Oriental Tokyo", "Tokyo", "Japan", "2-1-1 Nihonbashi Muromachi, Tokyo", 5, 750.0, 30, 179,
         ["spa", "pool", "concierge", "multiple restaurants", "gym", "wifi"]),
        ("Shinjuku Granbell Hotel", "Tokyo", "Japan", "2-14-5 Kabukicho, Shinjuku, Tokyo", 3, 120.0, 60, 100,
         ["wifi", "restaurant", "bar"]),
        ("Le Grand Hotel Paris", "Paris", "France", "2 Rue Scribe, Paris 75009", 5, 680.0, 25, 171,
         ["spa", "pool", "concierge", "restaurant", "bar", "wifi"]),
        ("Ibis Paris Gare du Nord", "Paris", "France", "58 Rue La Fayette, Paris 75009", 2, 95.0, 100, 250,
         ["wifi", "restaurant", "24h reception"]),
        ("Marina Bay Sands", "Singapore", "Singapore", "10 Bayfront Avenue, Singapore", 5, 620.0, 40, 2561,
         ["infinity pool", "casino", "spa", "multiple restaurants", "gym", "shopping mall"]),
        ("Pod Singapore", "Singapore", "Singapore", "289 Beach Road, Singapore", 3, 85.0, 110, 432,
         ["wifi", "restaurant", "bar", "rooftop pool"]),
        ("The Plaza New York", "New York", "USA", "Fifth Avenue at Central Park South, New York", 5, 950.0, 15, 282,
         ["spa", "concierge", "restaurant", "bar", "gym", "wifi"]),
        ("Pod 51 Hotel New York", "New York", "USA", "230 E 51st St, New York", 2, 110.0, 95, 665,
         ["wifi", "bar", "rooftop lounge"]),
        ("Hotel Arts Barcelona", "Barcelona", "Spain", "Carrer de la Marina 19-21, Barcelona", 5, 480.0, 35, 483,
         ["pool", "beach access", "spa", "restaurant", "bar", "gym", "wifi"]),
        ("Hotel 1898 Barcelona", "Barcelona", "Spain", "La Rambla 109, Barcelona", 4, 220.0, 55, 169,
         ["pool", "spa", "restaurant", "bar", "wifi"]),
        ("W Hong Kong", "Hong Kong", "China", "1 Austin Road West, Kowloon, Hong Kong", 5, 520.0, 38, 393,
         ["pool", "spa", "multiple restaurants", "bar", "gym", "wifi"]),
    ]

    hotels = []
    for name, city, country, address, stars, price, available, total, amenities in hotels_data:
        hotels.append(Hotel(
            id=uuid.uuid4(),
            name=name,
            city=city,
            country=country,
            address=address,
            star_rating=stars,
            price_per_night=price,
            available_rooms=available,
            total_rooms=total,
            amenities=amenities,
            description=f"A {stars}-star hotel in {city} offering world-class amenities and service.",
            is_active=True,
        ))
    return hotels


# ─── Seed Cars ────────────────────────────────────────────────────────────────

def seed_cars():
    cars_data = [
        ("Toyota", "Camry", "economy", "New York", 45.0, 5, "automatic", ["AC", "bluetooth", "GPS"]),
        ("BMW", "5 Series", "luxury", "New York", 120.0, 5, "automatic", ["leather seats", "sunroof", "GPS", "AC"]),
        ("Ford", "Explorer", "suv", "New York", 85.0, 7, "automatic", ["AC", "GPS", "bluetooth", "third row"]),
        ("Mercedes", "E-Class", "luxury", "London", 150.0, 5, "automatic", ["leather seats", "sunroof", "GPS"]),
        ("Vauxhall", "Astra", "economy", "London", 40.0, 5, "manual", ["AC", "bluetooth"]),
        ("Toyota", "RAV4", "suv", "Dubai", 75.0, 5, "automatic", ["AC", "GPS", "4WD", "bluetooth"]),
        ("Nissan", "Altima", "economy", "Dubai", 35.0, 5, "automatic", ["AC", "bluetooth"]),
        ("Honda", "CR-V", "suv", "Singapore", 80.0, 5, "automatic", ["AC", "GPS", "bluetooth", "backup camera"]),
        ("Toyota", "Prius", "economy", "Tokyo", 50.0, 5, "automatic", ["AC", "GPS", "hybrid", "bluetooth"]),
        ("Lexus", "ES 350", "luxury", "Paris", 130.0, 5, "automatic", ["leather seats", "sunroof", "GPS", "AC"]),
    ]

    cars = []
    for make, model, category, city, price, seats, transmission, features in cars_data:
        cars.append(Car(
            id=uuid.uuid4(),
            make=make,
            model=model,
            category=category,
            city=city,
            price_per_day=price,
            available=True,
            seats=seats,
            transmission=transmission,
            features=features,
            is_active=True,
        ))
    return cars



# ─── Seed Bookings, Insurance, Payments ───────────────────────────────────────

def seed_transactions(customers, flights, hotels, cars):
    """Create some existing bookings with linked insurance and payments."""
    bookings = []
    insurances = []
    payments = []

    # Booking 1: John Smith (Platinum) - Flight booking
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

    ins1 = InsurancePolicy(
        id=uuid.uuid4(),
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

    pay1 = Payment(
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
    )
    payments.append(pay1)

    # Booking 2: Sarah Johnson (Gold) - Hotel booking
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
        total_price=2550.0,
        loyalty_points_earned=2550,
        special_requests="High floor room, late checkout if possible",
        created_at=random_past_date(10, 20),
    )
    bookings.append(b2)

    pay2 = Payment(
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
    )
    payments.append(pay2)

    # Booking 3: Marie Dubois (Platinum) - Car booking
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
        total_price=390.0,
        loyalty_points_earned=390,
        created_at=random_past_date(35, 45),
    )
    bookings.append(b3)

    pay3 = Payment(
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
    )
    payments.append(pay3)

    # Booking 4: Ahmed Hassan - Cancelled booking with refund
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
        special_requests=None,
        created_at=random_past_date(45, 60),
    )
    bookings.append(b4)

    pay4 = Payment(
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
    )
    payments.append(pay4)

    # Booking 5: Emma Wilson (Gold) - Upcoming flight with insurance
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

    ins5 = InsurancePolicy(
        id=uuid.uuid4(),
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

    pay5 = Payment(
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
    )
    payments.append(pay5)

    return bookings, insurances, payments


# ─── Main Seed Function ───────────────────────────────────────────────────────

def seed_all():
    """Run all seeders and populate the database."""
    logger.info("Starting database seeding...")

    # Ensure tables exist
    create_tables(engine)

    with get_db() as db:
        # Check if already seeded
        existing = db.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        if existing > 0:
            logger.info(f"Database already has {existing} customers. Skipping seed.")
            logger.info("To re-seed, run: python -m database.seed_data --force")
            return

        # Seed in order (respecting foreign key dependencies)
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


        logger.info("Seeding bookings, insurance, and payments...")
        bookings, insurances, payments = seed_transactions(customers, flights, hotels, cars)
        db.add_all(bookings)
        db.flush()
        db.add_all(insurances)
        db.flush()
        db.add_all(payments)
        db.flush()
        logger.info(f"  ✅ {len(bookings)} bookings created")
        logger.info(f"  ✅ {len(insurances)} insurance policies created")
        logger.info(f"  ✅ {len(payments)} payments created")

    logger.info("")
    logger.info(" Database seeding complete!")
    logger.info(f"   Customers:          {len(customers)}")
    logger.info(f"   Flights:            {len(flights)}")
    logger.info(f"   Hotels:             {len(hotels)}")
    logger.info(f"   Cars:               {len(cars)}")
    logger.info(f"   Bookings:           {len(bookings)}")
    logger.info(f"   Insurance Policies: {len(insurances)}")
    logger.info(f"   Payments:           {len(payments)}")


if __name__ == "__main__":
    seed_all()
