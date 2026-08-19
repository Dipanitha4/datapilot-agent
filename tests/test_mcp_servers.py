"""
tests/test_mcp_servers.py
Tests for MCP server tool registration.
Verifies all tools are registered with correct names.
Run with: pytest tests/test_mcp_servers.py -v
"""

import asyncio
import pytest


def get_tool_names(mcp) -> list:
    """Helper to get tool names from an MCP server synchronously."""
    tools = asyncio.run(mcp.list_tools())
    return [t.name for t in tools]


def test_customer_mcp_tools_registered():
    """All 9 customer MCP tools should be registered."""
    from mcp_servers.customer_mcp_server import mcp
    tool_names = get_tool_names(mcp)
    expected = [
        "get_customer_profile_tool",
        "get_loyalty_tier_tool",
        "get_booking_history_tool",
        "update_loyalty_points_tool",
        "update_customer_profile_tool",
        "search_customers_tool",
        "verify_passport_tool",
        "add_booking_to_profile_tool",
        "move_booking_to_history_tool",
    ]
    for name in expected:
        assert name in tool_names, f"Missing tool: {name}"
    assert len(tool_names) == 9


def test_travel_inventory_mcp_tools_registered():
    """All 35 travel inventory MCP tools should be registered."""
    from mcp_servers.travel_inventory_mcp_server import mcp
    tool_names = get_tool_names(mcp)

    expected = [
        # Flight (10)
        "search_flights_tool", "search_flexible_dates_tool",
        "get_flight_details_tool", "get_flight_booking_tool",
        "book_flight_tool", "cancel_flight_tool",
        "check_flight_cancellation_terms_tool", "reschedule_flight_tool",
        "upgrade_flight_cabin_tool", "get_flight_bookings_by_customer_tool",
        # Hotel (7)
        "search_hotels_tool", "get_hotel_details_tool",
        "get_hotel_booking_tool", "book_hotel_tool",
        "cancel_hotel_tool", "modify_hotel_booking_tool",
        "get_hotel_bookings_by_customer_tool",
        # Car (8)
        "search_cars_tool", "get_car_details_tool",
        "get_car_booking_tool", "book_car_tool",
        "cancel_car_tool", "extend_rental_tool",
        "change_pickup_location_tool", "get_car_bookings_by_customer_tool",
        # Insurance (10)
        "get_insurance_policy_tool", "get_policy_by_booking_tool",
        "get_policies_by_customer_tool", "check_coverage_tool",
        "check_cancellation_coverage_tool", "file_claim_tool",
        "get_claim_status_tool", "cancel_insurance_tool",
        "update_insurance_dates_tool", "compare_insurance_plans_tool",
    ]

    for name in expected:
        assert name in tool_names, f"Missing tool: {name}"
    assert len(tool_names) == 35


def test_financial_mcp_tools_registered():
    """All 8 financial MCP tools should be registered (approve_refund excluded)."""
    from mcp_servers.financial_mcp_server import mcp
    tool_names = get_tool_names(mcp)
    expected = [
        "get_payment_methods_tool",
        "get_payment_status_tool",
        "get_customer_transactions_tool",
        "process_refund_tool",
        "get_refund_status_tool",
        "charge_customer_tool",
        "redeem_points_for_discount_tool",
        "get_refunds_by_booking_tool",
    ]
    for name in expected:
        assert name in tool_names, f"Missing tool: {name}"

    # Critical security check: approve_refund must NOT be in customer-facing MCP
    assert "approve_refund_tool" not in tool_names, \
        "SECURITY: approve_refund_tool must not be in financial MCP server"
    assert len(tool_names) == 8


def test_tool_count():
    """Verify total tool count across all 3 servers."""
    from mcp_servers.customer_mcp_server import mcp as customer_mcp
    from mcp_servers.travel_inventory_mcp_server import mcp as travel_mcp
    from mcp_servers.financial_mcp_server import mcp as financial_mcp

    assert len(asyncio.run(customer_mcp.list_tools())) == 9
    assert len(asyncio.run(travel_mcp.list_tools())) == 35
    assert len(asyncio.run(financial_mcp.list_tools())) == 8


def test_tool_descriptions_not_empty():
    """All tools must have descriptions — LLM needs them to decide when to call."""
    from mcp_servers.customer_mcp_server import mcp
    tools = asyncio.run(mcp.list_tools())
    for tool in tools:
        assert tool.description, f"Tool '{tool.name}' has no description"
        assert len(tool.description) > 20, f"Tool '{tool.name}' description too short"


def test_approve_refund_not_in_any_agent_mcp():
    """
    Security test: approve_refund must never appear in any MCP server
    accessible by customer-facing agents.
    """
    from mcp_servers.customer_mcp_server import mcp as c
    from mcp_servers.travel_inventory_mcp_server import mcp as t
    from mcp_servers.financial_mcp_server import mcp as f

    all_names = (
        [tool.name for tool in asyncio.run(c.list_tools())] +
        [tool.name for tool in asyncio.run(t.list_tools())] +
        [tool.name for tool in asyncio.run(f.list_tools())]
    )
    assert "approve_refund_tool" not in all_names, \
        "CRITICAL SECURITY VIOLATION: approve_refund_tool found in agent-accessible MCP server"
