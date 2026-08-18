"""
tests/test_database.py
Tests for database connection, models, and seeding.
Run with: pytest tests/test_database.py -v
"""

import pytest
from sqlalchemy import text
from database.connection import get_db, get_redis_client, check_all_connections, engine
from database.models import create_tables, Customer, Flight, Hotel, Car, Booking


def test_postgres_connection():
    """PostgreSQL should be reachable and respond to a query."""
    status = check_all_connections()
    assert status["postgresql"] is True, "PostgreSQL connection failed"


def test_redis_connection():
    """Redis should be reachable and respond to PING."""
    status = check_all_connections()
    assert status["redis"] is True, "Redis connection failed"


def test_redis_set_get():
    """Redis should correctly store and retrieve a value."""
    client = get_redis_client()
    client.set("test_key", "test_value", ex=10)
    value = client.get("test_key")
    assert value == "test_value"
    client.delete("test_key")


def test_tables_exist():
    """All expected tables should exist in the database."""
    expected_tables = [
        "customers", "flights", "hotels", "cars",
        "bookings", "insurance_policies", "payments", "claims", "policy_documents"
    ]
    with get_db() as db:
        for table in expected_tables:
            result = db.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
            )).scalar()
            assert result is True, f"Table '{table}' does not exist"


def test_customers_seeded():
    """Customers table should have at least 10 records."""
    with get_db() as db:
        count = db.execute(text("SELECT COUNT(*) FROM customers")).scalar()
        assert count >= 10, f"Expected at least 10 customers, got {count}"


def test_flights_seeded():
    """Flights table should have at least 20 records."""
    with get_db() as db:
        count = db.execute(text("SELECT COUNT(*) FROM flights")).scalar()
        assert count >= 20, f"Expected at least 20 flights, got {count}"


def test_customer_has_required_fields():
    """Customer records should have passport_expiry_date and preferences."""
    with get_db() as db:
        customer = db.execute(text(
            "SELECT passport_expiry_date, preferences, payment_methods FROM customers LIMIT 1"
        )).fetchone()
        assert customer is not None
        assert customer.passport_expiry_date is not None
        assert customer.preferences is not None
        assert customer.payment_methods is not None


def test_hotel_has_required_fields():
    """Hotel records should have room_types and meal_plans."""
    with get_db() as db:
        hotel = db.execute(text(
            "SELECT room_types, meal_plans, category FROM hotels LIMIT 1"
        )).fetchone()
        assert hotel is not None
        assert hotel.room_types is not None
        assert hotel.meal_plans is not None
        assert hotel.category is not None
