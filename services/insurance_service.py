"""
services/insurance_service.py
Insurance service — policy retrieval, coverage checks, and claims management.
Called by the Financial MCP Server.
Note: check_coverage and check_cancellation_coverage use RAG (PgVector) for
      semantic search on policy documents — implemented in rag/ layer.
      For now, these functions use structured policy_details from the database.
"""

import uuid
import logging
from datetime import datetime
from typing import Optional

from database.connection import get_db
from database.models import InsurancePolicy, Claim, Booking, ClaimStatus
from utils.calculator import calculate_refund_amount
from config import settings

logger = logging.getLogger(__name__)


# ─── Available insurance plans (static catalog) ───────────────────────────────

INSURANCE_PLANS = [
    {
        "plan_id": "travel_basic",
        "name": "Travel Basic",
        "policy_type": "travel",
        "premium_percent": 3.0,
        "coverages": {
            "trip_cancellation": 5000.0,
            "medical": 100000.0,
            "baggage_loss": 1000.0,
            "travel_delay": 500.0,
        },
        "description": "Essential coverage for budget travelers",
    },
    {
        "plan_id": "travel_comprehensive",
        "name": "Travel Comprehensive",
        "policy_type": "travel",
        "premium_percent": 6.0,
        "coverages": {
            "trip_cancellation": 10000.0,
            "medical": 500000.0,
            "medical_evacuation": 1000000.0,
            "baggage_loss": 2500.0,
            "travel_delay": 1000.0,
            "missed_connection": 500.0,
        },
        "description": "Full coverage for international travelers",
    },
    {
        "plan_id": "medical_only",
        "name": "Medical Only",
        "policy_type": "medical",
        "premium_percent": 4.0,
        "coverages": {
            "medical": 500000.0,
            "medical_evacuation": 1000000.0,
            "emergency_dental": 500.0,
        },
        "description": "Medical coverage only — ideal for travelers with existing trip cancellation",
    },
]

# Claim types covered and their max amounts (for check_coverage)
COVERED_CLAIM_TYPES = {
    "trip_cancellation": ["illness", "death", "severe_weather", "job_loss", "jury_duty"],
    "medical": ["emergency", "hospitalization", "surgery", "prescription"],
    "baggage_loss": ["lost", "stolen", "damaged"],
    "baggage_delay": ["delayed_12h", "carrier_delay"],
    "travel_delay": ["mechanical_failure", "severe_weather", "air_traffic_control"],
    "missed_connection": ["covered_delay"],
}


# ─── 1. get_insurance_policy ──────────────────────────────────────────────────

def get_insurance_policy(policy_id: str) -> dict:
    """Return full policy details including coverage and claims history."""
    with get_db() as db:
        policy = db.query(InsurancePolicy).filter(
            InsurancePolicy.id == uuid.UUID(policy_id)
        ).first()

        if not policy:
            return {"error": f"Insurance policy {policy_id} not found"}

        claims = db.query(Claim).filter(Claim.policy_id == policy.id).all()

        return {
            "policy_id": str(policy.id),
            "policy_number": policy.policy_number,
            "policy_type": policy.policy_type,
            "coverage_amount": policy.coverage_amount,
            "premium": policy.premium,
            "start_date": policy.start_date.strftime("%Y-%m-%d") if policy.start_date else None,
            "end_date": policy.end_date.strftime("%Y-%m-%d") if policy.end_date else None,
            "is_active": policy.is_active,
            "policy_details": policy.policy_details or {},
            "claims_count": len(claims),
            "claims": [
                {
                    "claim_id": str(c.id),
                    "claim_reference": c.claim_reference,
                    "claim_type": c.claim_type,
                    "amount_requested": c.amount_requested,
                    "amount_approved": c.amount_approved,
                    "status": c.status.value,
                    "filed_at": c.filed_at.strftime("%Y-%m-%d"),
                }
                for c in claims
            ],
        }


# ─── 2. get_policy_by_booking ─────────────────────────────────────────────────

def get_policy_by_booking(booking_id: str) -> dict:
    """Find insurance policy linked to a specific booking."""
    with get_db() as db:
        policy = db.query(InsurancePolicy).filter(
            InsurancePolicy.booking_id == uuid.UUID(booking_id)
        ).first()

        if not policy:
            return {
                "booking_id": booking_id,
                "has_insurance": False,
                "message": "No insurance policy found for this booking",
            }

        return {
            "booking_id": booking_id,
            "has_insurance": True,
            **get_insurance_policy(str(policy.id)),
        }


# ─── 3. get_policies_by_customer ──────────────────────────────────────────────

def get_policies_by_customer(customer_id: str) -> dict:
    """Return all insurance policies for a customer via their bookings."""
    with get_db() as db:
        bookings = db.query(Booking).filter(
            Booking.customer_id == uuid.UUID(customer_id)
        ).all()

        booking_ids = [b.id for b in bookings]
        if not booking_ids:
            return {"customer_id": customer_id, "policies": [], "total": 0}

        policies = db.query(InsurancePolicy).filter(
            InsurancePolicy.booking_id.in_(booking_ids)
        ).all()

        return {
            "customer_id": customer_id,
            "policies": [
                {
                    "policy_id": str(p.id),
                    "policy_number": p.policy_number,
                    "policy_type": p.policy_type,
                    "coverage_amount": p.coverage_amount,
                    "premium": p.premium,
                    "start_date": p.start_date.strftime("%Y-%m-%d") if p.start_date else None,
                    "end_date": p.end_date.strftime("%Y-%m-%d") if p.end_date else None,
                    "is_active": p.is_active,
                }
                for p in policies
            ],
            "total": len(policies),
        }


# ─── 4. check_coverage ────────────────────────────────────────────────────────

def check_coverage(policy_id: str, claim_type: str) -> dict:
    """
    Check if a specific claim type is covered under this policy.
    Returns coverage amount and conditions.
    Note: For nuanced coverage questions (e.g. "does my policy cover
    medical evacuation from remote areas?"), the Insurance Agent should
    also call the RAG layer to retrieve relevant policy document sections.
    """
    with get_db() as db:
        policy = db.query(InsurancePolicy).filter(
            InsurancePolicy.id == uuid.UUID(policy_id)
        ).first()

        if not policy:
            return {"error": f"Policy {policy_id} not found"}

        if not policy.is_active:
            return {
                "policy_id": str(policy.id),
                "claim_type": claim_type,
                "is_covered": False,
                "reason": "Policy is no longer active",
            }

        # Check if claim type exists in covered types
        is_covered = claim_type.lower() in COVERED_CLAIM_TYPES
        coverage_limit = policy.coverage_amount

        # Check policy_details for specific coverage amounts
        if policy.policy_details and "coverages" in policy.policy_details:
            coverage_limit = policy.policy_details["coverages"].get(claim_type.lower(), 0)
            if coverage_limit == 0:
                is_covered = False

        return {
            "policy_id": str(policy.id),
            "policy_number": policy.policy_number,
            "claim_type": claim_type,
            "is_covered": is_covered,
            "coverage_limit": coverage_limit if is_covered else 0,
            "covered_conditions": COVERED_CLAIM_TYPES.get(claim_type.lower(), []),
            "note": (
                "Coverage confirmed. File a claim with supporting documentation."
                if is_covered
                else f"'{claim_type}' is not covered under this policy type."
            ),
        }


# ─── 5. check_cancellation_coverage ──────────────────────────────────────────

def check_cancellation_coverage(policy_id: str, cancellation_reason: str) -> dict:
    """
    Check if a specific cancellation reason is covered.
    Returns whether the reason qualifies for trip cancellation benefit.
    """
    covered_reasons = COVERED_CLAIM_TYPES.get("trip_cancellation", [])

    # Simple keyword matching against covered reasons
    reason_lower = cancellation_reason.lower()
    is_covered = any(r in reason_lower for r in covered_reasons)

    with get_db() as db:
        policy = db.query(InsurancePolicy).filter(
            InsurancePolicy.id == uuid.UUID(policy_id)
        ).first()

        if not policy:
            return {"error": f"Policy {policy_id} not found"}

    return {
        "policy_id": policy_id,
        "cancellation_reason": cancellation_reason,
        "is_covered": is_covered,
        "covered_reasons": covered_reasons,
        "recommendation": (
            "Your cancellation reason may be covered. File a claim with medical/supporting documentation."
            if is_covered
            else "This reason may not be covered. Review your policy document for full exclusions list."
        ),
    }


# ─── 6. file_claim ────────────────────────────────────────────────────────────

def file_claim(
    policy_id: str,
    claim_type: str,
    amount_requested: float,
    description: str,
    incident_date: str,
) -> dict:
    """
    File a new insurance claim.
    Automatically caps claim amount at policy maximum.
    """
    with get_db() as db:
        policy = db.query(InsurancePolicy).filter(
            InsurancePolicy.id == uuid.UUID(policy_id)
        ).first()

        if not policy:
            return {"error": f"Policy {policy_id} not found"}

        if not policy.is_active:
            return {"error": "Cannot file a claim on an inactive policy"}

        # Cap at policy maximum
        capped_amount = min(amount_requested, policy.coverage_amount)

        try:
            incident_dt = datetime.strptime(incident_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid incident_date format. Use YYYY-MM-DD"}

        claim = Claim(
            id=uuid.uuid4(),
            claim_reference=f"CLM{str(uuid.uuid4())[:8].upper()}",
            policy_id=uuid.UUID(policy_id),
            claim_type=claim_type,
            amount_requested=capped_amount,
            status=ClaimStatus.FILED,
            description=description,
            incident_date=incident_dt,
        )
        db.add(claim)
        db.flush()

        return {
            "claim_id": str(claim.id),
            "claim_reference": claim.claim_reference,
            "policy_number": policy.policy_number,
            "claim_type": claim_type,
            "amount_requested": capped_amount,
            "original_amount_requested": amount_requested,
            "was_capped": amount_requested > policy.coverage_amount,
            "status": "filed",
            "message": "Claim filed successfully. Review within 10 business days.",
        }


# ─── 7. get_claim_status ─────────────────────────────────────────────────────

def get_claim_status(policy_id: str, claim_id: str) -> dict:
    """Return current status and details of a filed claim."""
    with get_db() as db:
        claim = db.query(Claim).filter(
            Claim.id == uuid.UUID(claim_id),
            Claim.policy_id == uuid.UUID(policy_id)
        ).first()

        if not claim:
            return {"error": f"Claim {claim_id} not found for policy {policy_id}"}

        return {
            "claim_id": str(claim.id),
            "claim_reference": claim.claim_reference,
            "policy_id": policy_id,
            "claim_type": claim.claim_type,
            "amount_requested": claim.amount_requested,
            "amount_approved": claim.amount_approved,
            "status": claim.status.value,
            "description": claim.description,
            "incident_date": claim.incident_date.strftime("%Y-%m-%d") if claim.incident_date else None,
            "filed_at": claim.filed_at.strftime("%Y-%m-%d"),
            "resolved_at": claim.resolved_at.strftime("%Y-%m-%d") if claim.resolved_at else None,
            "notes": claim.notes,
        }


# ─── 8. cancel_insurance ─────────────────────────────────────────────────────

def cancel_insurance(policy_id: str, reason: str) -> dict:
    """
    Cancel an insurance policy and process premium refund.
    Blocked if there are pending or under-review claims.
    """
    with get_db() as db:
        policy = db.query(InsurancePolicy).filter(
            InsurancePolicy.id == uuid.UUID(policy_id)
        ).first()

        if not policy:
            return {"error": f"Policy {policy_id} not found"}

        if not policy.is_active:
            return {"error": "Policy is already cancelled"}

        # Block if active claims exist
        active_claims = db.query(Claim).filter(
            Claim.policy_id == uuid.UUID(policy_id),
            Claim.status.in_([ClaimStatus.FILED, ClaimStatus.UNDER_REVIEW])
        ).count()

        if active_claims > 0:
            return {
                "error": f"Cannot cancel policy with {active_claims} pending/active claim(s). "
                         f"Resolve all claims before cancelling."
            }

        policy.is_active = False
        db.flush()

        refund = calculate_refund_amount(policy.premium or 0, 50)

        return {
            "policy_id": str(policy.id),
            "policy_number": policy.policy_number,
            "status": "cancelled",
            "cancellation_reason": reason,
            "premium_paid": policy.premium,
            "refund_amount": refund,
            "message": "Policy cancelled. 50% premium refund will be processed.",
        }


# ─── 9. update_insurance_travel_dates ────────────────────────────────────────

def update_insurance_travel_dates(
    policy_id: str,
    new_start_date: str,
    new_end_date: str,
) -> dict:
    """Update travel dates on a policy (e.g. after rescheduling a flight)."""
    with get_db() as db:
        policy = db.query(InsurancePolicy).filter(
            InsurancePolicy.id == uuid.UUID(policy_id)
        ).first()

        if not policy:
            return {"error": f"Policy {policy_id} not found"}

        if not policy.is_active:
            return {"error": "Cannot update an inactive policy"}

        try:
            new_start = datetime.strptime(new_start_date, "%Y-%m-%d")
            new_end = datetime.strptime(new_end_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}

        if new_end <= new_start:
            return {"error": "End date must be after start date"}

        old_start = policy.start_date
        old_end = policy.end_date
        policy.start_date = new_start
        policy.end_date = new_end
        db.flush()

        return {
            "policy_id": str(policy.id),
            "policy_number": policy.policy_number,
            "old_start_date": old_start.strftime("%Y-%m-%d") if old_start else None,
            "old_end_date": old_end.strftime("%Y-%m-%d") if old_end else None,
            "new_start_date": new_start_date,
            "new_end_date": new_end_date,
            "message": "Insurance travel dates updated successfully",
        }


# ─── 10. compare_plans ────────────────────────────────────────────────────────

def compare_plans() -> dict:
    """Return all available insurance plans for comparison."""
    return {
        "plans": INSURANCE_PLANS,
        "count": len(INSURANCE_PLANS),
        "note": "Premium is calculated as a percentage of total trip cost",
    }