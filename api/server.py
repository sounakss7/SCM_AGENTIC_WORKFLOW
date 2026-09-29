import os
import uuid
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field

from core.config import settings
from core.schema import (
    DisruptionEvent,
    DisruptionType,
    OptimizationConstraints,
    OptimizedPlan,
    RiskAssessment
)
from core.data_loader import DataCoDataLoader
from core.database import (
    init_database,
    log_audit_entry,
    get_audit_trail,
    update_approval_status
)
from agents.workflow import scm_graph

# Initialize database tables on server startup
init_database()

app = FastAPI(
    title="SCM Autonomous Disruption Response Engine",
    description="Multi-agent logistics disruption recovery system with deterministic MILP solver (PuLP) and Human-in-the-Loop governance.",
    version="2.0.0"
)

# Request/Response models for API
class DisruptRequest(BaseModel):
    disruption_type: DisruptionType = DisruptionType.PORT_CONGESTION
    location: str = "Port of Los Angeles"
    severity: float = Field(default=0.8, ge=0.0, le=1.0)
    duration_days: int = Field(default=8, ge=1, le=60)
    affected_warehouse: Optional[str] = "Pacific_Hub_LA"
    description: str = "Severe terminal congestion and labor dispute at Port of LA."
    order_count: int = Field(default=12, ge=1, le=100)

class PlanRequest(BaseModel):
    scenario_id: Optional[str] = None
    disruption: DisruptRequest = Field(default_factory=DisruptRequest)
    constraints: Optional[OptimizationConstraints] = None

class ApprovalRequest(BaseModel):
    scenario_id: str
    decision: str = Field(..., description="'APPROVED' or 'REJECTED'")
    dispatcher_name: str = "Dispatcher_Lead"
    notes: Optional[str] = "Approved after reviewing carrier capacity and customer SLA tier."


@app.get("/health", tags=["System"])
def health_check():
    """System health check and configuration status."""
    return {
        "status": "healthy",
        "service": "SCM Disruption Response Engine",
        "database_mode": "SQLite" if settings.USE_SQLITE else "MySQL",
        "hitl_approval_threshold_usd": settings.HITL_APPROVAL_THRESHOLD_USD,
        "solver": "PuLP / CBC MILP Engine",
        "llm_provider": settings.ROUTING_PREFERENCE,
        "langsmith_tracing": settings.LANGCHAIN_TRACING_V2
    }


@app.post("/disrupt", tags=["Disruption Management"])
def inject_disruption(payload: DisruptRequest):
    """
    Ingests or simulates a supply chain disruption event.
    Returns the detected disruption entity and affected orders.
    """
    scenario_id = f"SCEN-{uuid.uuid4().hex[:6].upper()}"
    event = DisruptionEvent(
        event_id=f"EVT-{uuid.uuid4().hex[:6].upper()}",
        disruption_type=payload.disruption_type,
        location=payload.location,
        severity=payload.severity,
        duration_days=payload.duration_days,
        affected_warehouse=payload.affected_warehouse,
        description=payload.description
    )

    loader = DataCoDataLoader()
    orders = loader.sample_active_orders(
        n=payload.order_count,
        origin_warehouse=payload.affected_warehouse or "Pacific_Hub_LA"
    )

    total_value = sum(o.total_value for o in orders)
    base_exposure = sum(
        o.total_value + (payload.duration_days * o.daily_late_penalty_rate * 1.5)
        if payload.duration_days > o.cancellation_threshold_days
        else payload.duration_days * o.daily_late_penalty_rate
        for o in orders
    )

    log_audit_entry(
        scenario_id=scenario_id,
        phase="API_DISRUPT_INGESTION",
        agent_name="FastAPI_Gateway",
        action_taken=f"Injected {payload.disruption_type.value}",
        model_used="API_Endpoint",
        cost_impact=base_exposure,
        requires_approval=False,
        approval_status="AUTO_APPROVED",
        details=f"Injected disruption at {payload.location}. Flagged {len(orders)} orders (${total_value:,.2f} cargo at risk)."
    )

    return {
        "scenario_id": scenario_id,
        "disruption_event": event,
        "affected_orders_count": len(orders),
        "total_value_at_risk_usd": round(total_value, 2),
        "unmitigated_penalty_exposure_usd": round(base_exposure, 2),
        "orders": [o.model_dump() for o in orders]
    }


@app.post("/plan", tags=["Autonomous Planning"])
def generate_recovery_plan(payload: PlanRequest):
    """
    Executes the full LangGraph multi-agent disruption response workflow:
    Monitor ➔ Risk Assessor ➔ PuLP Solver ➔ Critic (Retry Verification) ➔ Explainer
    """
    scenario_id = payload.scenario_id or f"SCEN-{uuid.uuid4().hex[:6].upper()}"
    d = payload.disruption
    event = DisruptionEvent(
        event_id=f"EVT-{uuid.uuid4().hex[:6].upper()}",
        disruption_type=d.disruption_type,
        location=d.location,
        severity=d.severity,
        duration_days=d.duration_days,
        affected_warehouse=d.affected_warehouse,
        description=d.description
    )

    constraints = payload.constraints or OptimizationConstraints()
    
    loader = DataCoDataLoader()
    orders = loader.sample_active_orders(
        n=d.order_count,
        origin_warehouse=d.affected_warehouse or "Pacific_Hub_LA"
    )

    init_state = {
        "scenario_id": scenario_id,
        "disruption_event": event,
        "affected_orders": orders,
        "risk_assessment": None,
        "constraints": constraints,
        "optimized_plan": None,
        "critic_verdict": None,
        "explanation": "",
        "requires_human_approval": False,
        "approval_status": "AUTO_APPROVED",
        "retry_count": 0,
        "llm_call_count": 0,
        "audit_trail": []
    }

    final_state = scm_graph.invoke(init_state)

    plan = final_state.get("optimized_plan")
    if not plan:
        raise HTTPException(status_code=500, detail="Planning engine failed to compute plan.")

    return {
        "scenario_id": scenario_id,
        "disruption_type": event.disruption_type.value,
        "location": event.location,
        "plan_status": plan.status,
        "total_combined_cost_usd": plan.total_combined_cost,
        "recovery_cost_usd": plan.total_recovery_cost,
        "penalty_cost_usd": plan.total_penalty_cost,
        "service_level_pct": plan.service_level_pct,
        "orders_on_time": plan.orders_on_time,
        "orders_delayed": plan.orders_delayed,
        "is_feasible": plan.is_feasible,
        "requires_human_approval": final_state.get("requires_human_approval", False),
        "approval_status": final_state.get("approval_status", "AUTO_APPROVED"),
        "explanation": final_state.get("explanation", ""),
        "capacity_utilization": plan.capacity_utilization,
        "allocations": [a.model_dump() for a in plan.allocations],
        "audit_trail": final_state.get("audit_trail", [])
    }


@app.post("/approve", tags=["Governance"])
def approve_recovery_plan(payload: ApprovalRequest):
    """
    Human-in-the-Loop (HITL) approval endpoint for high-cost recovery plans.
    Updates the decision status in the immutable audit ledger.
    """
    decision = payload.decision.upper().strip()
    if decision not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Decision must be either 'APPROVED' or 'REJECTED'.")

    update_approval_status(payload.scenario_id, decision)

    log_audit_entry(
        scenario_id=payload.scenario_id,
        phase="HUMAN_IN_THE_LOOP_GOVERNANCE",
        agent_name=payload.dispatcher_name,
        action_taken=f"Human Decision: {decision}",
        model_used="Human_Supervisor",
        cost_impact=0.0,
        requires_approval=False,
        approval_status=decision,
        details=f"Dispatcher {payload.dispatcher_name} set decision to {decision}. Notes: {payload.notes or 'None'}"
    )

    return {
        "scenario_id": payload.scenario_id,
        "decision": decision,
        "dispatcher": payload.dispatcher_name,
        "status": "Decision logged successfully in audit ledger."
    }


@app.get("/audit", tags=["Governance"])
def get_audit_logs(
    limit: int = Query(default=30, ge=1, le=200),
    scenario_id: Optional[str] = None
):
    """Retrieves immutable audit ledger logs."""
    logs = get_audit_trail(limit=limit, scenario_id=scenario_id)
    return {"count": len(logs), "logs": logs}


@app.get("/benchmark/summary", tags=["Analytics"])
def get_latest_benchmark_summary():
    """Returns the latest benchmark summary from results/results.json if available."""
    results_path = os.path.join(os.path.dirname(__file__), "..", "results", "results.json")
    if os.path.exists(results_path):
        import json
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "metadata": data.get("benchmark_metadata", {}),
            "summary": data.get("summary", [])
        }
    return {"detail": "Benchmark results not yet generated. Run 'python -m eval.run_benchmark' first."}
