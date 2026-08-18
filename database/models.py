"""
database/models.py
SQLAlchemy ORM models for the Travel AI Agent platform.
"""

import uuid
from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, Enum as SQLEnum, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


# ─── Base Class ───────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ─── Enums ────────────────────────────────────────────────────────────────────

class LoyaltyTier(str, enum.Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class BookingType(str, enum.Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    CAR = "car"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class CabinClass(str, enum.Enum):
    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"


class ClaimStatus(str, enum.Enum):
    FILED = "filed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


# ─── Customer ─────────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    passport_number = Column(String(50))
    passport_expiry_date = Column(DateTime, nullable=True)        # NEW: for verify_passport
    date_of_birth = Column(DateTime)
    nationality = Column(String(100))
    loyalty_tier = Column(SQLEnum(LoyaltyTier), default=LoyaltyTier.BRONZE)
    loyalty_points = Column(Integer, default=0)
    preferences = Column(JSON, nullable=True)                     # NEW: meal, seat, language prefs
    payment_methods = Column(JSON, nullable=True)                 # NEW: saved cards/wallets
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = relationship("Booking", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.first_name} {self.last_name} ({self.email})>"


# ─── Flight ───────────────────────────────────────────────────────────────────

class Flight(Base):
    __tablename__ = "flights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flight_number = Column(String(20), nullable=False, index=True)
    airline = Column(String(100), nullable=False)
    origin = Column(String(10), nullable=False)
    destination = Column(String(10), nullable=False)
    origin_city = Column(String(100))
    destination_city = Column(String(100))
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    cabin_class = Column(SQLEnum(CabinClass), default=CabinClass.ECONOMY)
    price = Column(Float, nullable=False)
    available_seats = Column(Integer, default=0)
    total_seats = Column(Integer)
    aircraft_type = Column(String(50))
    cancellation_policy = Column(JSON, nullable=True)             # NEW: refund tiers by hours
    amenities = Column(JSON, nullable=True)                       # NEW: wifi, meals, entertainment
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Flight {self.flight_number} {self.origin}->{self.destination}>"


# ─── Hotel ────────────────────────────────────────────────────────────────────

class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(100), nullable=False)
    address = Column(String(500))
    category = Column(String(50), nullable=True)                  # NEW: business, leisure, boutique
    star_rating = Column(Integer)
    price_per_night = Column(Float, nullable=False)
    available_rooms = Column(Integer, default=0)
    total_rooms = Column(Integer)
    amenities = Column(JSON)
    room_types = Column(JSON, nullable=True)                      # NEW: standard, deluxe, suite with prices
    meal_plans = Column(JSON, nullable=True)                      # NEW: room_only, breakfast, half_board, full_board
    cancellation_policy = Column(JSON, nullable=True)             # NEW: refund tiers by days before checkin
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Hotel {self.name} ({self.city})>"


# ─── Car Rental ───────────────────────────────────────────────────────────────

class Car(Base):
    __tablename__ = "cars"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    category = Column(String(50))
    vendor_type = Column(String(50), nullable=True)               # NEW: corporate, local, premium
    city = Column(String(100), nullable=False, index=True)
    price_per_day = Column(Float, nullable=False)
    available = Column(Boolean, default=True)
    seats = Column(Integer)
    transmission = Column(String(20))
    mileage_limit_per_day = Column(Integer, nullable=True)        # NEW: km per day, None = unlimited
    features = Column(JSON)
    cancellation_policy = Column(JSON, nullable=True)             # NEW: refund tiers by hours before pickup
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Car {self.make} {self.model} ({self.city})>"


# ─── Booking ──────────────────────────────────────────────────────────────────

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_reference = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    booking_type = Column(SQLEnum(BookingType), nullable=False)
    status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)

    flight_id = Column(UUID(as_uuid=True), ForeignKey("flights.id"), nullable=True)
    hotel_id = Column(UUID(as_uuid=True), ForeignKey("hotels.id"), nullable=True)
    car_id = Column(UUID(as_uuid=True), ForeignKey("cars.id"), nullable=True)

    check_in_date = Column(DateTime, nullable=True)
    check_out_date = Column(DateTime, nullable=True)
    num_guests = Column(Integer, default=1)

    # Car-specific fields                                         # NEW
    pickup_location = Column(String(200), nullable=True)
    return_location = Column(String(200), nullable=True)
    pickup_time = Column(String(10), nullable=True)               # "09:00"
    return_time = Column(String(10), nullable=True)               # "18:00"

    # Hotel-specific fields                                       # NEW
    room_type = Column(String(100), nullable=True)
    meal_plan = Column(String(50), nullable=True)

    total_price = Column(Float, nullable=False)
    loyalty_points_earned = Column(Integer, default=0)
    loyalty_points_used = Column(Integer, default=0)
    special_requests = Column(Text)
    booking_metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    insurance = relationship("InsurancePolicy", back_populates="booking", uselist=False)

    def __repr__(self):
        return f"<Booking {self.booking_reference} ({self.booking_type})>"


# ─── Insurance Policy ─────────────────────────────────────────────────────────

class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_number = Column(String(30), unique=True, nullable=False, index=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    policy_type = Column(String(100))
    coverage_amount = Column(Float)
    premium = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    policy_details = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="insurance")
    claims = relationship("Claim", back_populates="policy")       # NEW

    def __repr__(self):
        return f"<InsurancePolicy {self.policy_number}>"


# ─── Claim ────────────────────────────────────────────────────────────────────  NEW

class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_reference = Column(String(30), unique=True, nullable=False, index=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("insurance_policies.id"), nullable=False)
    claim_type = Column(String(100), nullable=False)              # trip_cancellation, medical, baggage, delay
    amount_requested = Column(Float, nullable=False)
    amount_approved = Column(Float, nullable=True)
    status = Column(SQLEnum(ClaimStatus), default=ClaimStatus.FILED)
    description = Column(Text)
    incident_date = Column(DateTime)
    filed_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)                           # reviewer notes

    policy = relationship("InsurancePolicy", back_populates="claims")

    def __repr__(self):
        return f"<Claim {self.claim_reference} ({self.claim_type})>"


# ─── Payment ──────────────────────────────────────────────────────────────────

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method = Column(String(50))
    refund_amount = Column(Float, default=0.0)
    refund_reason = Column(Text)
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String(100))
    payment_metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="payments")
    booking = relationship("Booking", back_populates="payment")

    def __repr__(self):
        return f"<Payment {self.transaction_id} ${self.amount}>"


# ─── Policy Documents (RAG + PgVector) ────────────────────────────────────────

class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    document_type = Column(String(100))
    chunk_index = Column(Integer, default=0)
    source = Column(String(200))
    embedding = Column(Vector(384))                               # sentence-transformers dimension
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PolicyDocument {self.title[:50]}>"


# ─── Create All Tables ────────────────────────────────────────────────────────

def create_tables(engine):
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully")


if __name__ == "__main__":
    from database.connection import engine
    create_tables(engine)