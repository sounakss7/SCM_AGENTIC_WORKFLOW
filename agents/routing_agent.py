"""Routing Agent (Agent 3 in Resilience Workflow).

Invokes the Deterministic Operations Research Decision Core.
The LLM does NOT calculate routes or costs. The routing agent feeds operational
constraints and blocked nodes/edges into the deterministic solver to compute
the globally optimal alternate path minimizing Total Landed Cost in INR (₹).
"""

from typing import Dict, Any, List
from agents.state import DisruptionWorkflowState
from optimizer.resilience_solver import find_optimal_alternate_route, RoutePlan
from core.network import CARRIERS_DB


def routing_agent_node(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    """Invoke the deterministic decision core to compute the optimal alternate route."""
    logs = state.get("agent_logs", [])
    model_records = state.get("model_records", [])

    if not state.get("disruption_detected"):
        return state

    order_id = state.get("order_id", "ORD_001")
    sku_id = state.get("sku_id", "SKU_001")
    quantity = state.get("quantity", 100)
    source_supplier = state.get("source_supplier")
    target_retailer = state.get("target_retailer")
    nominal_plan = state.get("nominal_plan", {})
    disruption = state.get("disruption", {})
    retry_count = state.get("retry_count", 0)

    # Determine blocked elements from disruption
    blocked_carriers = []
    congested_ports = {}
    blocked_lanes = []

    if disruption.get("carrier"):
        blocked_carriers.append(disruption["carrier"])
    if disruption.get("port"):
        congested_ports[disruption["port"]] = disruption.get("delay_days", 2.0)
    if disruption.get("supplier") and disruption.get("warehouse"):
        blocked_lanes.append((disruption["supplier"], disruption["warehouse"]))
    if disruption.get("warehouse") and disruption.get("retailer"):
        blocked_lanes.append((disruption["warehouse"], disruption["retailer"]))

    # If this is a retry triggered by validator rejection, add validator rejected carrier
    validation_result = state.get("validation_result")
    if validation_result and not validation_result.get("is_valid", True):
        prev_carrier = state.get("proposed_plan", {}).get("carrier")
        if prev_carrier and prev_carrier not in blocked_carriers:
            blocked_carriers.append(prev_carrier)

    # Run deterministic optimization solver (NO LLM MATH)
    alternate_plan, _ = find_optimal_alternate_route(
        supplier_id=source_supplier,
        retailer_id=target_retailer,
        sku_id=sku_id,
        quantity=quantity,
        blocked_carriers=blocked_carriers,
        congested_ports=congested_ports,
        blocked_lanes=blocked_lanes
    )

    if alternate_plan:
        plan_dict = alternate_plan.to_dict()
        nominal_cost = nominal_plan.get("total_cost_inr", 0.0)
        cost_delta = round(plan_dict["total_cost_inr"] - nominal_cost, 2)
        nominal_transit = nominal_plan.get("total_transit_days", 0.0)
        transit_delta = round(plan_dict["total_transit_days"] - nominal_transit, 2)

        plan_dict["cost_delta_inr"] = cost_delta
        plan_dict["transit_delta_days"] = transit_delta

        logs.append({
            "agent": "Routing Agent",
            "action": "Deterministic Re-route Solved",
            "message": (
                f"Generated alternate path: {plan_dict['supplier']} -> {plan_dict['port']} -> "
                f"{plan_dict['warehouse']} -> {plan_dict['retailer']} via {plan_dict['carrier']}. "
                f"Landed Cost: ₹{plan_dict['total_cost_inr']:,.2f} (Delta: ₹{cost_delta:+,.2f}), "
                f"Transit: {plan_dict['total_transit_days']} days."
            ),
            "status": "SUCCESS"
        })

        return {
            "proposed_plan": plan_dict,
            "status": "ROUTING_PROPOSED",
            "agent_logs": logs,
            "model_records": model_records
        }
    else:
        logs.append({
            "agent": "Routing Agent",
            "action": "Infeasible",
            "message": "Deterministic solver could not find any feasible path satisfying all network constraints.",
            "status": "FAILED"
        })
        return {
            "proposed_plan": None,
            "status": "FAILED",
            "agent_logs": logs,
            "model_records": model_records
        }
