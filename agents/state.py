"""
agents/state.py
LangGraph state definition for the Travel AI Agent platform.

This TypedDict defines the shared state that flows through the agent graph.
Each customer conversation gets its own state instance identified by thread_id.
No state is shared between different customer sessions.

The state is persisted using the 2-layer approach:
- Redis: fast active session access
- PostgreSQL checkpointer: durable state that survives restarts
"""

from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class TravelAgentState(TypedDict):
    """
    State schema for the Travel AI Agent multi-agent system.
    
    All fields are per-session — thread_id ensures complete isolation
    between concurrent customer sessions.
    """

    # ── Conversation ──────────────────────────────────────────────────────────
    messages: Annotated[list, add_messages]
    # Full conversation history.
    # add_messages reducer appends new messages rather than replacing.
    # Capped at MAX_CONVERSATION_HISTORY by the orchestrator to control tokens.

    # ── Session Identity ──────────────────────────────────────────────────────
    customer_id: Optional[str]
    # Extracted from the incoming request. Used by all agents to scope
    # every database query to this customer only.

    thread_id: str
    # Unique identifier for this conversation session.
    # LangGraph uses this to isolate state between concurrent customers.

    # ── Routing ───────────────────────────────────────────────────────────────
    current_agent: Optional[str]
    # Which specialist agent is currently active.
    # Values: 'orchestrator', 'flight_agent', 'hotel_agent',
    #         'car_agent', 'insurance_agent', 'payments_agent'

    next_agent: Optional[str]
    # Which agent the orchestrator has decided to route to next.
    # Set by orchestrator, consumed by the router node.

    # ── Human-in-the-Loop ─────────────────────────────────────────────────────
    pending_approval: bool
    # True when a tool result requires supervisor approval before continuing.
    # When True, LangGraph pauses the workflow.

    approval_data: Optional[dict]
    # Stores the pending action details while waiting for supervisor approval.
    # Example: {"type": "refund", "amount": 650.0, "booking_id": "...", "reason": "..."}
    # Cleared after approval or rejection.

    approval_status: Optional[str]
    # Set by supervisor via the API: 'approved' or 'rejected'
    # LangGraph resumes when this is set.

    # ── Safety ────────────────────────────────────────────────────────────────
    pii_detected: bool
    # True if Presidio detected PII in the customer's message.
    # The sanitized version of the message is stored in messages.

    sanitized_message: Optional[str]
    # The PII-redacted version of the customer's input.
    # This is what gets passed to the LLM — never the raw message.

    # ── Context ───────────────────────────────────────────────────────────────
    customer_profile: Optional[dict]
    # Cached customer profile fetched at session start.
    # Avoids repeated DB calls for the same customer within one conversation.

    active_booking_context: Optional[dict]
    # When a customer is working on a specific booking, its details are stored here.
    # Cleared when the conversation moves to a different booking.

    # ── Error Handling ────────────────────────────────────────────────────────
    last_error: Optional[str]
    # Last error message from a tool call, if any.
    # Used by agents to decide whether to retry or inform the customer.

    retry_count: int
    # Number of consecutive tool failures for the current request.
    # Agents stop retrying after 3 attempts and escalate to human.


def create_initial_state(customer_id: str, thread_id: str, user_message: str) -> TravelAgentState:
    """
    Creates a fresh state for a new customer conversation.
    Called by FastAPI when a new /chat request arrives.
    
    Args:
        customer_id: The authenticated customer's ID
        thread_id: Unique session identifier (typically customer_id + timestamp)
        user_message: The customer's first message (already PII-scanned by FastAPI)
    """
    return TravelAgentState(
        messages=[{"role": "user", "content": user_message}],
        customer_id=customer_id,
        thread_id=thread_id,
        current_agent="orchestrator",
        next_agent=None,
        pending_approval=False,
        approval_data=None,
        approval_status=None,
        pii_detected=False,
        sanitized_message=None,
        customer_profile=None,
        active_booking_context=None,
        last_error=None,
        retry_count=0,
    )
