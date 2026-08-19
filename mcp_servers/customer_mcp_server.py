"""
mcp_servers/customer_mcp_server.py
Customer MCP Server — CRM tools for profile, loyalty, and booking management.
Runs on port 8001.
"""

from fastmcp import FastMCP
from services.crm_service import (
    get_customer_profile,
    get_loyalty_tier,
    get_booking_history,
    update_loyalty_points,
    update_customer_profile,
    search_customers,
    verify_passport,
    add_booking_to_profile,
    move_booking_to_history,
)

mcp = FastMCP(
    name="customer-mcp-server",
    instructions="CRM tools for managing customer profiles, loyalty, and booking history.",
)


@mcp.tool()
def get_customer_profile_tool(customer_id: str) -> dict:
    """
    Returns the customer's full profile: name, contact info, passport details,
    loyalty tier, preferences (meal/seat/language), and saved payment methods.
    Call this first when you need to know who the customer is or their preferences.
    """
    return get_customer_profile(customer_id)


@mcp.tool()
def get_loyalty_tier_tool(customer_id: str) -> dict:
    """
    Returns the customer's loyalty tier (Bronze/Silver/Gold/Platinum),
    points balance, tier benefits, and points needed to reach the next tier.
    Use when the customer asks about their rewards or tier status.
    """
    return get_loyalty_tier(customer_id)


@mcp.tool()
def get_booking_history_tool(customer_id: str) -> dict:
    """
    Returns all bookings for the customer split into active (confirmed/pending)
    and past (completed/cancelled). Use when customer asks about their bookings
    or when you need booking context before a modification.
    """
    return get_booking_history(customer_id)


@mcp.tool()
def update_loyalty_points_tool(customer_id: str, points_delta: int, reason: str) -> dict:
    """
    Adds (positive delta) or deducts (negative delta) loyalty points.
    Automatically upgrades or downgrades tier if a threshold is crossed.
    Call after booking confirmation to credit points, or after redemption to deduct.
    Points cannot go below zero.
    """
    return update_loyalty_points(customer_id, points_delta, reason)


@mcp.tool()
def update_customer_profile_tool(customer_id: str, updates: dict) -> dict:
    """
    Updates allowed customer profile fields: phone, email, preferences.
    RESTRICTION: Cannot update passport_number, loyalty_tier, or loyalty_points
    through this tool. Those have dedicated secure processes.
    """
    return update_customer_profile(customer_id, updates)


@mcp.tool()
def search_customers_tool(
    name: str = None,
    email: str = None,
    phone: str = None,
    tier: str = None,
) -> dict:
    """
    Finds customers by name, email, phone, or loyalty tier.
    At least one filter must be provided. Returns up to 20 results.
    Use when customer provides partial information and you need to identify them.
    """
    return search_customers(name, email, phone, tier)


@mcp.tool()
def verify_passport_tool(customer_id: str, travel_date: str) -> dict:
    """
    Checks if the customer's passport is valid for travel on the given date (YYYY-MM-DD).
    Most countries require at least 6 months validity beyond travel date.
    Returns is_valid flag and a warning message if passport is expiring too soon.
    Always call this when booking international travel.
    """
    return verify_passport(customer_id, travel_date)


@mcp.tool()
def add_booking_to_profile_tool(customer_id: str, booking_id: str) -> dict:
    """
    Verifies a booking belongs to the customer and returns confirmation.
    Call after creating a new booking to confirm it is linked correctly.
    """
    return add_booking_to_profile(customer_id, booking_id)


@mcp.tool()
def move_booking_to_history_tool(customer_id: str, booking_id: str) -> dict:
    """
    Marks a booking as completed and moves it from active to booking history.
    Call after a cancellation or after a trip has been completed.
    """
    return move_booking_to_history(customer_id, booking_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)