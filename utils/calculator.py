"""
utils/calculator.py
Deterministic calculator utilities.
The LLM calls these via tools or services call them directly.
Never let the LLM do arithmetic — use these functions instead.
"""

from typing import Union


def calculate_percentage(amount: float, percent: float) -> float:
    """Calculate percentage of an amount. e.g. 10% of 5000 = 500.0"""
    return round((amount * percent) / 100, 2)


def calculate_discount(amount: float, discount_percent: float) -> float:
    """Apply a discount and return the discounted price. e.g. 5000 - 10% = 4500.0"""
    discount = calculate_percentage(amount, discount_percent)
    return round(amount - discount, 2)


def calculate_total(base_amount: float, tax_percent: float = 0.0, discount_percent: float = 0.0) -> dict:
    """
    Calculate final total after tax and discount.
    Discount is applied first, then tax is added.
    Returns breakdown dict.
    """
    discounted = calculate_discount(base_amount, discount_percent)
    tax_amount = calculate_percentage(discounted, tax_percent)
    total = round(discounted + tax_amount, 2)
    return {
        "base_amount": base_amount,
        "discount_percent": discount_percent,
        "discount_amount": round(base_amount - discounted, 2),
        "amount_after_discount": discounted,
        "tax_percent": tax_percent,
        "tax_amount": tax_amount,
        "total": total,
    }


def calculate_difference(value1: float, value2: float) -> float:
    """Return the absolute difference between two values."""
    return round(abs(value1 - value2), 2)


def calculate_refund_amount(total_paid: float, refund_percent: float) -> float:
    """Calculate refund amount based on refund percentage."""
    return calculate_percentage(total_paid, refund_percent)


def calculate_upgrade_cost(current_price: float, upgrade_price: float) -> float:
    """Calculate cost to upgrade from current to higher tier."""
    diff = upgrade_price - current_price
    return round(max(diff, 0.0), 2)


def calculate_rental_cost(price_per_day: float, days: int, additional_charges: float = 0.0) -> dict:
    """Calculate total car rental cost."""
    base = round(price_per_day * days, 2)
    total = round(base + additional_charges, 2)
    return {
        "price_per_day": price_per_day,
        "days": days,
        "base_cost": base,
        "additional_charges": additional_charges,
        "total": total,
    }


def calculate_loyalty_points_value(points: int, rate: float = 0.25) -> float:
    """
    Convert loyalty points to currency value.
    Default rate: 4 points = $1 (0.25 per point).
    """
    return round(points * rate, 2)


def points_required_for_discount(discount_amount: float, rate: float = 0.25) -> int:
    """
    Calculate how many points needed for a given discount.
    Default: 4 points = $1.
    """
    return int(discount_amount / rate)

