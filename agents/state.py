"""LangGraph state representation for Indian E-Commerce COD RTO & Last-Mile Allocation Engine."""

from typing import Dict, List, Optional, TypedDict
from core.schema import OrderRecord, DispatchPlan, WhatsAppVerificationResult


class IndianLogisticsState(TypedDict):
    """Shared state container across all LangGraph nodes."""
    # Input batch
    raw_orders: List[OrderRecord]

    # Agent 1: Address Intelligence output
    address_scores: Dict[str, float]  # order_id -> quality score (0.0 to 1.0)
    parsed_addresses: Dict[str, Dict[str, str]]

    # Agent 2: RTO Risk Scorer output
    rto_risk_scores: Dict[str, float]  # order_id -> predicted P(RTO)
    expected_margins: Dict[str, float]  # order_id -> estimated margin in ₹

    # Agent 3: WhatsApp Pre-shipment Verification output
    whatsapp_results: Dict[str, WhatsAppVerificationResult]
    cancelled_orders: List[str]  # Orders cancelled by buyer before dispatch (saves ₹180 in freight)
    upi_converted_orders: List[str]  # Orders converted from COD to UPI Prepaid (risk slashed)
    dispatched_candidates: List[OrderRecord]

    # Agent 4: Deterministic Planner (PuLP MILP) output
    dispatch_plan: Optional[DispatchPlan]

    # Agent 5: Quota & Serviceability Critic output
    critic_passed: bool
    critic_violations: List[str]
    retry_count: int

    # Human-in-the-Loop Gate
    hitl_required: bool
    hitl_flagged_orders: List[str]
    hitl_approved: bool

    # Agent 6: Bilingual Explainer output
    briefing_en: str
    briefing_hi: str
