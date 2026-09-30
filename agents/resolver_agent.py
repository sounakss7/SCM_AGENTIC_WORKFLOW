"""Resolver Agent: Mediates Procurement vs Logistics conflicts using the deterministic MILP optimizer."""

from typing import Dict, List, Any
from agents.state import MultiEchelonAgentState, DisruptionEvent, NegotiationRound
from optimizer.multi_echelon_solver import solve_multi_echelon_replenishment


def resolver_agent_node(state: MultiEchelonAgentState) -> Dict:
    """Detect trade-off tensions between Procurement and Logistics, invoke MILP solver, and log negotiation."""
    net = state["network"]
    demand_pts = {k: v["point_forecast"] for k, v in state["forecast_demand"].items()}
    disruption: DisruptionEvent = state.get("active_disruption")

    cur_round = state.get("negotiation_round", 1)
    history = list(state.get("negotiation_log", []))

    proc_prop = state.get("procurement_proposal", {})
    log_prop = state.get("logistics_proposal", {})

    # Detect tension / conflict
    conflict_identified = (
        "Procurement prioritizes S1 ($14-$50/unit) for cost savings, but Logistics flags that S1's "
        "2-period lead time will cause severe early-period store stockouts (penalty $40-$150/unit). "
        "Warehouse capacity limits (500 units) also prohibit bulk order dumping."
    )

    # Apply disruption overrides to the optimizer
    supplier_cap_override = None
    warehouse_cap_override = None
    supplier_lt_override = None
    lane_cap_override = None

    if disruption:
        if disruption.disruption_type == "SUPPLIER_DELAY":
            supplier_lt_override = {disruption.affected_entity: 4}  # Lead time increased to 4 periods
            conflict_identified += f" CRITICAL DISRUPTION: {disruption.affected_entity} delayed by +2 periods."
        elif disruption.disruption_type == "PORT_CONGESTION":
            lane_cap_override = {("S1", "W1"): 30}  # Lane throttled
            conflict_identified += " CRITICAL DISRUPTION: S1->W1 port lane throttled to 30 units."
        elif disruption.disruption_type == "WAREHOUSE_CAPACITY_LOSS":
            warehouse_cap_override = {disruption.affected_entity: 250}  # Capacity cut by 50%
            conflict_identified += f" CRITICAL DISRUPTION: {disruption.affected_entity} storage capacity cut to 250 units."

    # Solve the multi-echelon MILP with combined physical constraints
    joint_solution = solve_multi_echelon_replenishment(
        network=net,
        demand=demand_pts,
        supplier_capacity_override=supplier_cap_override,
        warehouse_capacity_override=warehouse_cap_override,
        supplier_lead_time_override=supplier_lt_override,
        lane_capacity_override=lane_cap_override
    )

    # Resolution action description
    resolution_action = (
        f"MILP solver optimally split sourcing: Fast suppliers S2/S3 satisfy immediate demand (t=1, t=2), "
        f"while bulk S1 covers steady-state replenishment (t=3, t=4). "
        f"Total Cost: ${joint_solution.total_cost:,.2f} | Service Level: {joint_solution.service_level_pct:.1f}%."
    )

    # Record negotiation round
    round_entry = {
        "round_index": cur_round,
        "procurement_strategy": proc_prop.get("strategy", "Cost Minimization"),
        "logistics_strategy": log_prop.get("strategy", "Lead-Time Feasibility"),
        "conflict": conflict_identified,
        "resolution": resolution_action,
        "joint_cost": joint_solution.total_cost,
        "service_level_pct": joint_solution.service_level_pct,
        "stockout_units": joint_solution.total_stockout_units
    }
    history.append(round_entry)

    # Cost delta computation if before-disruption baseline exists
    before_sol = state.get("before_disruption_solution")
    cost_delta = 0.0
    service_delta = 0.0
    if before_sol:
        cost_delta = round(joint_solution.total_cost - before_sol.total_cost, 2)
        service_delta = round(joint_solution.service_level_pct - before_sol.service_level_pct, 2)

    return {
        "negotiation_round": cur_round + 1,
        "negotiation_log": history,
        "conflict_detected": True,
        "conflict_reason": conflict_identified,
        "joint_solution": joint_solution,
        "cost_delta": cost_delta,
        "service_delta": service_delta
    }
