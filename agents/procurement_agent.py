"""Procurement Agent: Sourcing optimization focused on supplier unit costs and contract volume."""

from typing import Dict, Any
from agents.state import MultiEchelonAgentState, DisruptionEvent


def procurement_agent_node(state: MultiEchelonAgentState) -> Dict:
    """Formulate initial sourcing proposal prioritizing low unit procurement costs."""
    net = state["network"]
    disruption: DisruptionEvent = state.get("active_disruption")

    # Evaluate suppliers: S1 is bulk low cost, S2 is regional, S3 is express
    preferred_shares = {"S1": 0.60, "S2": 0.30, "S3": 0.10}

    # If supplier disruption is known to Procurement
    if disruption and disruption.disruption_type == "SUPPLIER_DELAY" and disruption.affected_entity == "S1":
        # Shift away from S1
        preferred_shares = {"S1": 0.10, "S2": 0.60, "S3": 0.30}

    total_forecast_units = sum(f["point_forecast"] for f in state["forecast_demand"].values())

    procurement_proposal = {
        "strategy": "Cost-Minimization Sourcing",
        "preferred_shares": preferred_shares,
        "rationale": (
            "Maximizing volume through S1 (unit cost $14-$50) to minimize COGS. "
            "S2 and S3 utilized primarily as risk buffers."
            if preferred_shares["S1"] > 0.4 else
            "Emergency re-sourcing to S2 and S3 due to active lead-time disruption on S1."
        ),
        "target_sourcing_volume": {
            s: round(total_forecast_units * share, 1)
            for s, share in preferred_shares.items()
        }
    }

    return {"procurement_proposal": procurement_proposal}
