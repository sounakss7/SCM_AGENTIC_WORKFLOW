"""FastAPI Application Server for Indian Supply Chain Resilience Agent.

Exposes REST endpoints:
- GET  /health           : Health & multi-model router liveness
- GET  /network          : Indian network topology, carriers, and 25 FMCG SKUs
- POST /simulate         : End-to-end order simulation with 5-agent resilience workflow
- POST /disrupt          : Inject disruption (carrier failure, port congestion, road closure)
- GET  /plan/{scenario_id}: Retrieve plan details for a specific benchmark scenario or incident
- GET  /catalog/disruptions: Pre-defined Indian supply chain disruptions
"""

import os
import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field

from core.network import (
    NETWORK, SUPPLIERS_DB, PORTS_DB, WAREHOUSES_DB, RETAILERS_DB, CARRIERS_DB, SKUS_DB,
    get_default_indian_network
)
from core.disruptions import (
    DisruptionEvent, DisruptionType, SeverityLevel, get_predefined_disruptions
)
from optimizer.resilience_solver import find_optimal_alternate_route
from agents.workflow import run_resilience_workflow

app = FastAPI(
    title="Indian Supply Chain Resilience Agent API",
    description="5-Agent LangGraph System with Deterministic OR Solver Core for Indian freight corridors under disruption.",
    version="1.0.0"
)


class SimulationRequest(BaseModel):
    order_id: str = Field(default="ORD-API-001", description="Unique order reference")
    sku_id: str = Field(default="SKU_01", description="SKU identifier (e.g. SKU_01 to SKU_25)")
    quantity: int = Field(default=100, ge=1, le=1000, description="Order shipment quantity")
    source_supplier: str = Field(default="SUP_PUNE", description="Origin supplier node ID")
    target_retailer: str = Field(default="RET_MUMBAI", description="Destination retailer node ID")
    disruption: Optional[Dict[str, Any]] = Field(default=None, description="Optional disruption event")


class DisruptionInjectionRequest(BaseModel):
    disruption_type: DisruptionType = Field(..., description="CARRIER_FAILURE, PORT_CONGESTION, ROUTE_CLOSURE, CAPACITY_CHOKE")
    target_type: str = Field(..., description="'CARRIER', 'PORT', or 'LINK'")
    target_id: str = Field(..., description="e.g. 'SAFEXPRESS', 'PORT_JNPT', or 'L_JNPT_DEL'")
    severity: SeverityLevel = Field(default=SeverityLevel.HIGH)
    delay_days_added: float = Field(default=3.0, ge=0.0)
    cost_surcharge_pct: float = Field(default=30.0, ge=0.0)
    capacity_reduction_pct: float = Field(default=80.0, ge=0.0, le=100.0)
    description: str = Field(default="Injected disruption via API.")
    test_order_sku: str = Field(default="SKU_01")
    test_order_qty: int = Field(default=100)


@app.get("/health")
def health_check():
    """System status and agentic routing health."""
    return {
        "status": "healthy",
        "service": "Indian Supply Chain Resilience Agent",
        "version": "1.0.0",
        "agents": ["Monitor", "Risk Assessor (Gemini 2.5 Flash)", "Routing (OR Solver)", "Validator (Groq LPU)", "Explainer (Gemini 2.5 Flash)"],
        "currency": "INR (₹)"
    }


@app.get("/network")
def get_network_topology():
    """Return complete Indian logistics network nodes, links, carriers, and 25 FMCG SKUs."""
    net = get_default_indian_network()
    return net.model_dump()


@app.get("/catalog/disruptions")
def list_disruption_catalog():
    """List predefined Indian logistics disruption events."""
    events = get_predefined_disruptions()
    return [e.model_dump() for e in events]


@app.post("/simulate")
def simulate_order(req: SimulationRequest):
    """Execute the full 5-agent LangGraph resilience workflow for an order."""
    if req.source_supplier not in SUPPLIERS_DB:
        raise HTTPException(status_code=400, detail=f"Supplier '{req.source_supplier}' not found in network.")
    if req.target_retailer not in RETAILERS_DB:
        raise HTTPException(status_code=400, detail=f"Retailer '{req.target_retailer}' not found in network.")
    if req.sku_id not in SKUS_DB:
        raise HTTPException(status_code=400, detail=f"SKU '{req.sku_id}' not found in network catalog.")

    result = run_resilience_workflow(
        order_id=req.order_id,
        sku_id=req.sku_id,
        quantity=req.quantity,
        source_supplier=req.source_supplier,
        target_retailer=req.target_retailer,
        disruption=req.disruption
    )
    return result


@app.post("/disrupt")
def inject_disruption(req: DisruptionInjectionRequest):
    """Inject a disruption into the network and trigger 5-agent self-correcting response."""
    disruption = DisruptionEvent(
        event_id="API-INJECTED-DIS",
        disruption_type=req.disruption_type,
        target_type=req.target_type,
        target_id=req.target_id,
        severity=req.severity,
        delay_days_added=req.delay_days_added,
        cost_surcharge_pct=req.cost_surcharge_pct,
        capacity_reduction_pct=req.capacity_reduction_pct,
        description=req.description
    )

    # Run resilience workflow against a representative lane
    workflow_result = run_resilience_workflow(
        order_id="ORD-DISRUPT-TEST",
        sku_id=req.test_order_sku,
        quantity=req.test_order_qty,
        source_supplier="SUP_PUNE",
        target_retailer="RET_MUMBAI",
        disruption=disruption.to_dict()
    )

    return {
        "injected_disruption": disruption.model_dump(),
        "workflow_resolution": workflow_result
    }


@app.get("/plan/{scenario_id}")
def get_scenario_plan(scenario_id: int = Path(..., ge=1, le=100)):
    """Retrieve the recovery plan and audited performance for a specific benchmark scenario."""
    results_path = os.path.join(os.path.dirname(__file__), "..", "results", "results.json")
    if not os.path.exists(results_path):
        results_path = os.path.join(os.path.dirname(__file__), "results", "results.json")

    if not os.path.exists(results_path):
        raise HTTPException(status_code=404, detail="Benchmark results not found. Please run eval/benchmark_100.py first.")

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenarios = data.get("scenarios", [])
    matched = next((s for s in scenarios if s.get("scenario_id") == scenario_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail=f"Scenario ID {scenario_id} not found in benchmark.")

    return {
        "scenario_metadata": matched,
        "benchmark_summary": data.get("resilience_performance")
    }
