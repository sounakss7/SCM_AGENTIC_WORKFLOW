"""FastAPI Backend Server for Indian E-Commerce COD RTO & Last-Mile Allocation Engine."""

from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.schema import OrderRecord, DispatchPlan, AuditLogEntry, IndianAddress
from core.config import settings, get_default_carrier_rate_cards
from core.database import db
from core.data_loader import generate_indian_orders
from agents.address_parser import parse_indian_address
from agents.whatsapp_agent import simulate_whatsapp_dialogue
from agents.workflow import run_indian_logistics_pipeline

app = FastAPI(
    title="Bharat E-Commerce COD RTO & Last-Mile Allocation Engine",
    description="Autonomous Agentic Workflow + PuLP Deterministic MILP Optimizer for Indian Logistics (Meesho / Shiprocket style)",
    version="2.0.0"
)


class IngestOrdersRequest(BaseModel):
    count: int = 20
    seed: int = 42


class ParseAddressRequest(BaseModel):
    raw_address: str
    pincode: Optional[str] = "110001"


class ApprovalRequest(BaseModel):
    plan_id: str
    approved: bool
    operator_name: str
    notes: Optional[str] = None


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENV,
        "hitl_threshold_inr": settings.HITL_ORDER_VALUE_THRESHOLD_INR,
        "database": settings.DATABASE_URL
    }


@app.get("/carriers/rate-cards")
def get_rate_cards():
    """Inspect active 3PL courier rate cards and daily hub capacities."""
    cards = get_default_carrier_rate_cards()
    return {c.value: card.model_dump() for c, card in cards.items()}


@app.post("/address/parse")
def parse_address_endpoint(req: ParseAddressRequest):
    """Parse a chaotic Indian address and return structured entities and completeness score."""
    addr_obj, score = parse_indian_address(req.raw_address, req.pincode or "110001")
    return {
        "address": addr_obj.model_dump(),
        "completeness_score": score,
        "quality_tier": addr_obj.quality_tier.value,
        "has_landmark": addr_obj.has_landmark
    }


@app.post("/orders/sample")
def sample_orders_endpoint(req: IngestOrdersRequest):
    """Generate a batch of realistic Indian e-commerce orders."""
    orders = generate_indian_orders(count=req.count, seed=req.seed)
    return {
        "count": len(orders),
        "orders": [o.model_dump() for o in orders]
    }


@app.post("/dispatch/allocate")
def allocate_dispatch_endpoint(orders: List[OrderRecord], hitl_approved: bool = False):
    """Execute the full LangGraph + PuLP MILP allocation pipeline on an order batch."""
    if not orders:
        raise HTTPException(status_code=400, detail="Order list cannot be empty.")

    final_state = run_indian_logistics_pipeline(orders, hitl_approved=hitl_approved)
    plan: Optional[DispatchPlan] = final_state.get("dispatch_plan")

    if not plan:
        raise HTTPException(status_code=500, detail="Failed to generate dispatch plan.")

    # Record audit log
    db.log_event(AuditLogEntry(
        log_id=f"LOG-{plan.plan_id}",
        timestamp="",
        event_type="DISPATCH_PLAN_GENERATED",
        details={
            "dispatched": plan.parcels_dispatched,
            "cancelled": plan.parcels_cancelled_prevented_rto,
            "upi_converted": plan.upi_converted_count,
            "rto_savings_inr": plan.rto_cost_savings_inr,
            "hitl_required": plan.hitl_approval_required
        },
        financial_impact_inr=plan.rto_cost_savings_inr,
        operator_approved=not plan.hitl_approval_required
    ))

    return {
        "plan": plan.model_dump(),
        "cancelled_orders": final_state.get("cancelled_orders", []),
        "upi_converted_orders": final_state.get("upi_converted_orders", []),
        "hitl_required": final_state.get("hitl_required", False),
        "hitl_flagged_orders": final_state.get("hitl_flagged_orders", []),
        "briefing_en": final_state.get("briefing_en", ""),
        "briefing_hi": final_state.get("briefing_hi", "")
    }


@app.post("/dispatch/approve")
def approve_dispatch_endpoint(req: ApprovalRequest):
    """Supervisor sign-off for orders requiring Human-in-the-Loop authorization."""
    db.log_event(AuditLogEntry(
        log_id=f"APP-{req.plan_id}",
        timestamp="",
        event_type="HITL_SUPERVISOR_APPROVAL",
        details={"plan_id": req.plan_id, "approved": req.approved},
        financial_impact_inr=0.0,
        operator_approved=req.approved,
        operator_notes=f"Authorized by {req.operator_name}. Notes: {req.notes or 'None'}"
    ))

    return {
        "status": "APPROVED" if req.approved else "REJECTED",
        "plan_id": req.plan_id,
        "operator": req.operator_name,
        "message": "Authorization recorded in immutable ledger."
    }


@app.get("/audit/logs")
def get_audit_logs(limit: int = 50):
    """Retrieve immutable audit ledger entries."""
    logs = db.get_recent_audit_logs(limit)
    return {"count": len(logs), "logs": logs}
