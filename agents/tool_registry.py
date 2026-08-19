"""
agents/tool_registry.py
Central tool filtering registry.
Defines which tools each agent is allowed to use.
This enforces the principle: agents only see tools relevant to their domain.
Prevents token bloat and reduces risk of an agent calling wrong tools.
"""

# Tools each agent is permitted to use.
# Keys must match tool names registered in MCP servers.
# Orchestrator gets minimal tools — it routes, it does not act.

AGENT_TOOL_MAP = {

    "orchestrator": [
        # CRM read-only tools for routing decisions
        "get_customer_profile_tool",
        "get_loyalty_tier_tool",
        "get_booking_history_tool",
        "search_customers_tool",
    ],

    "flight_agent": [
        # Flight operations
        "search_flights_tool",
        "search_flexible_dates_tool",
        "get_flight_details_tool",
        "get_flight_booking_tool",
        "book_flight_tool",
        "cancel_flight_tool",
        "check_flight_cancellation_terms_tool",
        "reschedule_flight_tool",
        "upgrade_flight_cabin_tool",
        "get_flight_bookings_by_customer_tool",
        # Customer context needed for booking
        "get_customer_profile_tool",
        "verify_passport_tool",
        "add_booking_to_profile_tool",
        # Points after booking
        "update_loyalty_points_tool",
    ],

    "hotel_agent": [
        # Hotel operations
        "search_hotels_tool",
        "get_hotel_details_tool",
        "get_hotel_booking_tool",
        "book_hotel_tool",
        "cancel_hotel_tool",
        "modify_hotel_booking_tool",
        "get_hotel_bookings_by_customer_tool",
        # Customer context
        "get_customer_profile_tool",
        "add_booking_to_profile_tool",
        "update_loyalty_points_tool",
    ],

    "car_agent": [
        # Car rental operations
        "search_cars_tool",
        "get_car_details_tool",
        "get_car_booking_tool",
        "book_car_tool",
        "cancel_car_tool",
        "extend_rental_tool",
        "change_pickup_location_tool",
        "get_car_bookings_by_customer_tool",
        # Customer context
        "get_customer_profile_tool",
        "add_booking_to_profile_tool",
        "update_loyalty_points_tool",
    ],

    "insurance_agent": [
        # Insurance operations
        "get_insurance_policy_tool",
        "get_policy_by_booking_tool",
        "get_policies_by_customer_tool",
        "check_coverage_tool",
        "check_cancellation_coverage_tool",
        "file_claim_tool",
        "get_claim_status_tool",
        "cancel_insurance_tool",
        "update_insurance_dates_tool",
        "compare_insurance_plans_tool",
        # Customer context
        "get_customer_profile_tool",
    ],

    "payments_agent": [
        # Payment operations
        "get_payment_methods_tool",
        "get_payment_status_tool",
        "get_customer_transactions_tool",
        "process_refund_tool",
        "get_refund_status_tool",
        "charge_customer_tool",
        "redeem_points_for_discount_tool",
        "get_refunds_by_booking_tool",
        # Customer context
        "get_customer_profile_tool",
        "get_loyalty_tier_tool",
        # NOTE: approve_refund is NOT here.
        # It is only accessible via the supervisor API endpoint.
    ],

}


def get_tools_for_agent(agent_name: str, all_tools: list) -> list:
    """
    Filters the full tool list to only the tools an agent is allowed to use.
    
    Args:
        agent_name: Name of the agent (must match a key in AGENT_TOOL_MAP)
        all_tools: Full list of tool objects from MCP client
    
    Returns:
        Filtered list of tools for the agent
    """
    allowed_names = AGENT_TOOL_MAP.get(agent_name, [])
    return [tool for tool in all_tools if tool.name in allowed_names]
