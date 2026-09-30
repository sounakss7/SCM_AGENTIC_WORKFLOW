"""FastAPI Application Server for Multi-Echelon Supply Chain Control Tower."""

import os
import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.network import MultiEchelonNetwork, get_default_network
from forecasting.forecaster import forecaster
from agents.state import DisruptionEvent
from agents.workflow import run_control_tower_pipeline
from eval.benchmark_scenarios import generate_200_scenarios

app = FastAPI(
    title="Multi-Echelon Supply Chain Control Tower",
    description="Autonomous cooperating LangGraph agents with a deterministic MILP optimization core for multi-echelon replenishment and disruption management.",
    version="3.0.0"
)


class ForecastRequest(BaseModel):
    horizon_length: int = Field(default=4, ge=1, le=12)


class PlanRequest(BaseModel):
    max_negotiation_rounds: int = Field(default=2, ge=1, le=5)


class DisruptRequest(BaseModel):
    disruption_type: str = Field(..., description="SUPPLIER_DELAY, PORT_CONGESTION, DEMAND_SPIKE, or WAREHOUSE_CAPACITY_LOSS")
    affected_entity: str = Field(..., description="e.g., 'S1', 'W1', or 'R1'")
    severity_factor: float = Field(default=2.0, ge=0.1)
    duration_periods: int = Field(default=2, ge=1)
    description: Optional[str] = "Operational disruption injected via Control Tower API."


@app.get("/health")
def health_endpoint():
    """System liveness and configuration health check."""
    return {
        "status": "healthy",
        "app_name": "Multi-Echelon Supply Chain Control Tower",
        "version": "3.0.0",
        "optimizer": "PuLP / CBC Branch-and-Bound",
        "ml_forecaster": "LightGBM / Gradient Boosting"
    }


@app.get("/network")
def network_topology_endpoint():
    """Return the physical multi-echelon network topology (suppliers, warehouses, stores, SKUs)."""
    net = get_default_network()
    return net.model_dump()


@app.post("/forecast")
def forecast_endpoint(req: ForecastRequest = ForecastRequest()):
    """Generate multi-period demand forecasts with uncertainty bounds and backtest accuracy."""
    forecasts = forecaster.predict_horizon(horizon_length=req.horizon_length)
    formatted = [
        {
            "store_id": k[0],
            "sku_id": k[1],
            "period": k[2],
            "point_forecast": v["point_forecast"],
            "lower_bound_80": v["lower_bound_80"],
            "upper_bound_80": v["upper_bound_80"],
            "std_dev": v["std_dev"]
        }
        for k, v in forecasts.items()
    ]

    return {
        "horizon_periods": req.horizon_length,
        "backtest_metrics": forecaster.metrics_report,
        "forecasts": formatted
    }


@app.post("/plan")
def plan_endpoint(req: PlanRequest = PlanRequest()):
    """Execute multi-agent negotiation and deterministic MILP replenishment optimization."""
    final_state = run_control_tower_pipeline(max_rounds=req.max_negotiation_rounds)
    sol = final_state.get("joint_solution")

    if not sol:
        raise HTTPException(status_code=500, detail="Failed to generate optimal multi-echelon plan.")

    return {
        "solution": sol.model_dump(),
        "negotiation_rounds_executed": len(final_state.get("negotiation_log", [])),
        "negotiation_log": final_state.get("negotiation_log", []),
        "plain_english_briefing": final_state.get("plain_english_briefing", "")
    }


@app.post("/disrupt")
def disrupt_endpoint(req: DisruptRequest):
    """Inject a disruption, trigger multi-agent re-negotiation, and return cost delta."""
    event = DisruptionEvent(
        disruption_type=req.disruption_type,
        affected_entity=req.affected_entity,
        severity_factor=req.severity_factor,
        duration_periods=req.duration_periods,
        description=req.description or "Injected disruption"
    )

    final_state = run_control_tower_pipeline(disruption=event, max_rounds=2)
    sol = final_state.get("joint_solution")

    return {
        "disruption": event.model_dump(),
        "solution": sol.model_dump() if sol else None,
        "cost_delta": final_state.get("cost_delta", 0.0),
        "service_delta": final_state.get("service_delta", 0.0),
        "negotiation_log": final_state.get("negotiation_log", []),
        "plain_english_briefing": final_state.get("plain_english_briefing", "")
    }


@app.get("/scenario/{scenario_id}")
def get_scenario_endpoint(scenario_id: int):
    """Retrieve details for a specific benchmark scenario ID (1 to 200)."""
    scenarios = generate_200_scenarios()
    if scenario_id < 1 or scenario_id > len(scenarios):
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found. Valid IDs: 1 to 200.")

    scn = scenarios[scenario_id - 1]
    return {
        "scenario_id": scn["scenario_id"],
        "seed": scn["seed"],
        "disruption": scn["disruption"].model_dump() if scn["disruption"] else None,
        "demand_count": len(scn["demand"])
    }


@app.get("/benchmark/summary")
def get_benchmark_summary_endpoint():
    """Retrieve raw benchmark summary results from results/results.json."""
    res_path = os.path.join(os.path.dirname(__file__), "..", "results", "results.json")
    if not os.path.exists(res_path):
        raise HTTPException(status_code=404, detail="Benchmark results.json not found. Run benchmark first.")

    with open(res_path, "r", encoding="utf-8") as f:
        return json.load(f)
