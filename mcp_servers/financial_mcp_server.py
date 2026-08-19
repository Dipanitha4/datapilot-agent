"""
mcp_servers/financial_mcp_server.py
Financial MCP Server — payment, refund, charge, and loyalty tools.
Runs on port 8003. Called by Payments Agent only.

approve_refund is NOT exposed here. It is only accessible via the
supervisor API endpoint — never through customer-facing agents.
"""

from fastmcp import FastMCP
from services.payment_service import (
    get_payment_methods,
    get_payment_status,
    get_customer_transactions,
    process_refund,
    get_refund_status,
    charge_customer,
    redeem_points_for_discount,
    get_refunds_by_booking,
)

mcp = FastMCP(
    name="financial-mcp-server",
    instructions="Payment, refund, charge, and loyalty tools. Refunds above $500 require supervisor approval and cannot be bypassed.",
)


@mcp.tool()
def get_payment_methods_tool(customer_id: str) -> dict:
    """
    Returns the customer's saved payment methods and identifies the default one.
    Use this before charging a customer to confirm a payment method exists.
    """
    return get_payment_methods(customer_id)


@mcp.tool()
def get_payment_status_tool(transaction_id: str) -> dict:
    """
    Returns the current status and full details of a specific transaction.
    Use this to check if a payment completed, failed, or is pending approval.
    """
    return get_payment_status(transaction_id)


@mcp.tool()
def get_customer_transactions_tool(
    customer_id: str,
    transaction_type: str = None,
    booking_type: str = None,
) -> dict:
    """
    Returns transaction history for a customer with total spending summary.
    transaction_type: 'payment' or 'refund' (omit for all).
    booking_type: 'flight', 'hotel', or 'car' (omit for all).
    """
    return get_customer_transactions(customer_id, transaction_type, booking_type)


@mcp.tool()
def process_refund_tool(
    customer_id: str,
    booking_id: str,
    amount: float,
    reason: str,
    refund_method: str = None,
) -> dict:
    """
    Initiates a refund for a completed booking payment.
    HARD RULE: Refunds above $500 are automatically flagged as
    requires_supervisor_approval=true and set to PENDING status.
    These cannot be auto-approved. Do not attempt to route around this.
    Refunds at or below $500 are processed immediately.
    Expected completion: 7 business days after approval.
    """
    return process_refund(customer_id, booking_id, amount, reason, refund_method)


@mcp.tool()
def get_refund_status_tool(refund_id: str) -> dict:
    """
    Returns the current status of a refund: initiated, processing,
    completed, failed, or pending_approval.
    Use this when a customer asks about their refund.
    """
    return get_refund_status(refund_id)


@mcp.tool()
def charge_customer_tool(
    customer_id: str,
    booking_id: str,
    amount: float,
    reason: str,
) -> dict:
    """
    Charges the customer's default payment method for ancillary fees.
    Use for: upgrade fees, reschedule fees, extension charges, extra days.
    Do not use for original booking payments — those are handled by booking tools.
    """
    return charge_customer(customer_id, booking_id, amount, reason)


@mcp.tool()
def redeem_points_for_discount_tool(customer_id: str, points_to_redeem: int) -> dict:
    """
    Converts loyalty points to a cash discount. Rate: 4 points = $1.
    Deducts points from the customer's balance immediately.
    Returns error if customer has insufficient points.
    """
    return redeem_points_for_discount(customer_id, points_to_redeem)


@mcp.tool()
def get_refunds_by_booking_tool(booking_id: str) -> dict:
    """
    Returns all refund transactions associated with a specific booking.
    Use when a customer disputes a refund or asks for refund history on a booking.
    """
    return get_refunds_by_booking(booking_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8003)