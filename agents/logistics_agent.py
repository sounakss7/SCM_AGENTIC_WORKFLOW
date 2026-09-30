"""Logistics Agent: Transport and storage routing minimizing stockout delay and warehouse holding costs."""

from typing import Dict, Any
from agents.state import MultiEchelonAgentState, DisruptionEvent


def logistics_agent_node(state: MultiEchelonAgentState) -> Dict:
    """Formulate replenishment and warehouse inventory proposal based on lead times and lane capacity."""
    net = state["network"]
    disruption: DisruptionEvent = state.get("active_disruption")

    # Assess lead-time exposure:
    # S1 takes 2 periods; Stores need inventory immediately (t=1, t=2).
    # If initial warehouse stock is low, relying heavily on S1 creates early-period stockouts.
    total_forecast = sum(f["point_forecast"] for f in state["forecast_demand"].values())

    logistics_proposal = {
        "strategy": "Lead-Time & Capacity-Feasible Replenishment",
        "warehouse_preference": {"W1": 0.50, "W2": 0.50},
        "minimum_fast_supplier_share_required": 0.40,  # Needs at least 40% in S2/S3 for t=1 & t=2 arrivals
        "rationale": (
            "S1 2-period lead time creates critical deficit in periods 1 & 2. "
            "Requires immediate S2/S3 allocations to bridge store SLA requirements. "
            "Warehouse capacities constrained to 500 units each."
        ),
        "warehouse_capacity_headroom": {
            w.warehouse_id: w.storage_capacity - sum(w.initial_inventory.values())
            for w in net.warehouses
        }
    }

    if disruption and disruption.disruption_type == "WAREHOUSE_CAPACITY_LOSS":
        aff_wh = disruption.affected_entity
        logistics_proposal["warehouse_preference"][aff_wh] = 0.20
        other_wh = "W2" if aff_wh == "W1" else "W1"
        logistics_proposal["warehouse_preference"][other_wh] = 0.80
        logistics_proposal["rationale"] += f" Re-routing throughput to {other_wh} due to capacity loss at {aff_wh}."

    return {"logistics_proposal": logistics_proposal}
