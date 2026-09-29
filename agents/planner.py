from typing import Dict, Any
from core.config import settings
from core.database import log_audit_entry, save_recovery_plan
from optimizer.solver import SupplyChainOptimizer
from agents.state import DisruptionState

def planner_node(state: DisruptionState) -> Dict[str, Any]:
    """
    Planner Agent:
    Formulates recovery alternatives (reroute, air expedite, alternate supplier, split)
    and executes the deterministic Mixed-Integer Linear Program (PuLP).
    The LLM does NOT do the math; the solver guarantees global optimality and physical constraints.
    """
    orders = state.get("affected_orders", [])
    event = state["disruption_event"]
    scenario_id = state["scenario_id"]
    constraints = state.get("constraints")
    retry_count = state.get("retry_count", 0)

    optimizer = SupplyChainOptimizer(time_limit_sec=settings.SOLVER_TIMEOUT_SEC)
    
    plan = optimizer.solve(
        scenario_id=scenario_id,
        orders=orders,
        base_disruption_delay_days=event.duration_days,
        constraints=constraints
    )

    # Check Human-in-the-Loop approval requirement
    # High-cost recovery plans (> $5,000 threshold) require human approval
    requires_approval = bool(plan.total_recovery_cost > settings.HITL_APPROVAL_THRESHOLD_USD)
    approval_status = "PENDING" if requires_approval else "AUTO_APPROVED"

    # Persist plan to database
    save_recovery_plan(plan.model_dump())

    details = (
        f"Generated {plan.status} Recovery Plan via PuLP (Solver time: {plan.solver_time_sec*1000:.1f}ms). "
        f"Total Combined Cost: ${plan.total_combined_cost:,.2f} "
        f"(Recovery Cost: ${plan.total_recovery_cost:,.2f}, Penalties: ${plan.total_penalty_cost:,.2f}). "
        f"Service Level: {plan.service_level_pct:.1f}% ({plan.orders_on_time}/{len(orders)} on time). "
        f"Requires Human Approval: {requires_approval} (Status: {approval_status})."
    )

    log_audit_entry(
        scenario_id=scenario_id,
        phase=f"PLANNING_OPTIMIZATION (Iteration {retry_count + 1})",
        agent_name="Planner_Agent",
        action_taken=f"Solved MILP Allocation ({plan.status})",
        model_used="PuLP_CBC_MIP_Solver",
        cost_impact=plan.total_combined_cost,
        requires_approval=requires_approval,
        approval_status=approval_status,
        details=details
    )

    trail = list(state.get("audit_trail", []))
    trail.append({
        "phase": f"Planning (Iter {retry_count + 1})",
        "agent": "Planner_Agent",
        "action": f"Computed optimal allocation with PuLP: ${plan.total_combined_cost:,.2f} total cost",
        "details": details
    })

    return {
        "optimized_plan": plan,
        "requires_human_approval": requires_approval,
        "approval_status": approval_status,
        "audit_trail": trail
    }
