"""
tests/test_calculator.py
Tests for calculator utility functions.
Run with: pytest tests/test_calculator.py -v
"""

import pytest
from utils.calculator import (
    calculate_percentage,
    calculate_discount,
    calculate_total,
    calculate_difference,
    calculate_refund_amount,
    calculate_upgrade_cost,
    calculate_rental_cost,
    calculate_loyalty_points_value,
    points_required_for_discount,
)


def test_calculate_percentage():
    assert calculate_percentage(5000, 10) == 500.0
    assert calculate_percentage(1000, 0) == 0.0
    assert calculate_percentage(1000, 100) == 1000.0
    assert calculate_percentage(333, 33.33) == 110.99


def test_calculate_discount():
    assert calculate_discount(5000, 10) == 4500.0
    assert calculate_discount(1000, 0) == 1000.0
    assert calculate_discount(1000, 100) == 0.0


def test_calculate_total():
    result = calculate_total(5000, tax_percent=8, discount_percent=10)
    assert result["base_amount"] == 5000
    assert result["discount_amount"] == 500.0
    assert result["amount_after_discount"] == 4500.0
    assert result["tax_amount"] == 360.0
    assert result["total"] == 4860.0


def test_calculate_difference():
    assert calculate_difference(2800, 450) == 2350.0
    assert calculate_difference(450, 2800) == 2350.0
    assert calculate_difference(500, 500) == 0.0


def test_calculate_refund_amount():
    assert calculate_refund_amount(450.0, 100) == 450.0
    assert calculate_refund_amount(450.0, 50) == 225.0
    assert calculate_refund_amount(450.0, 0) == 0.0


def test_calculate_upgrade_cost():
    assert calculate_upgrade_cost(450.0, 2800.0) == 2350.0
    assert calculate_upgrade_cost(2800.0, 450.0) == 0.0  # downgrade = 0


def test_calculate_rental_cost():
    result = calculate_rental_cost(120.0, 7)
    assert result["base_cost"] == 840.0
    assert result["total"] == 840.0

    result_with_extras = calculate_rental_cost(120.0, 7, additional_charges=50.0)
    assert result_with_extras["total"] == 890.0


def test_calculate_loyalty_points_value():
    assert calculate_loyalty_points_value(1000) == 250.0   # 4 points = $1
    assert calculate_loyalty_points_value(0) == 0.0
    assert calculate_loyalty_points_value(4) == 1.0


def test_points_required_for_discount():
    assert points_required_for_discount(250.0) == 1000
    assert points_required_for_discount(1.0) == 4
    assert points_required_for_discount(0.0) == 0
