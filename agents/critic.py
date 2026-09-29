from typing import Dict, Any, List
from core.config import settings
from core.schema import CriticVerdict, RecoveryActionType, OptimizationConstraints
from core.database import log_audit_entry
from agents.state import DisruptionState

def critic_node(state: DisruptionState) -> Dict[str, Any]:
    """
    Critic Agent:
    Validates proposed recovery plans against physical constraints (capacities, SLA boundaries, budgets).
    If infeasible or violating constraints, rejects the plan, adjusts constraint slack, and triggers a retry loop.
    """
    plan = state.get("optimized_plan")
    constraints = state.get("constraints") or OptimizationConstraints()
    retry_count = state.get("retry_count", 0)
    scenario_id = state["scenario_id"]

    violations: List[str] = []
    
    if plan is None or not plan.is_feasible or plan.status != "OPTIMAL":
        violations.append(f"Solver failed to find an optimal solution (Solver Status: {getattr(plan, 'status', 'NULL')}).")

    if plan and plan.allocations:
        # Check air freight capacity compliance
        air_units = sum(
            a.quantity if a.selected_action == RecoveryActionType.EXPEDITE_AIR 
            else (0.5 * a.quantity if a.selected_action == RecoveryActionType.SPLIT_EXPEDITE else 0)
            for a in plan.allocations
        )
        if air_units > constraints.max_air_freight_units:
            violations.append(f"Air freight volume ({air_units} units) exceeds physical limit ({constraints.max_air_freight_units} units).")

        # Check total warehouse divert capacity compliance
        total_wh_cap = sum(constraints.warehouse_divert_capacities.values())
        wh_units = sum(
            a.quantity if a.selected_action == RecoveryActionType.STANDARD_REROUTE
            else (0.5 * a.quantity if a.selected_action == RecoveryActionType.SPLIT_EXPEDITE else 0)
            for a in plan.allocations
        )
        if wh_units > total_wh_cap:
            violations.append(f"Diverted warehouse volume ({wh_units} units) exceeds total network capacity ({total_wh_cap} units).")

        # Check budget constraint if set
        if constraints.max_budget is not None and plan.total_recovery_cost > constraints.max_budget:
            violations.append(f"Total recovery cost (${plan.total_recovery_cost:,.2f}) exceeds budget limit (${constraints.max_budget:,.2f}).")

    is_feasible = (len(violations) == 0)
    retry_recommended = (not is_feasible) and (retry_count < settings.MAX_CRITIC_RETRIES)
    
    suggested_adjustments = {}
    new_constraints = constraints.model_copy()

    if retry_recommended:
        # Relax constraints to recover feasibility
        if constraints.max_budget is not None:
            new_budget = round(constraints.max_budget * 1.35, 2)
            suggested_adjustments["max_budget"] = new_budget
            new_constraints.max_budget = new_budget
            
        new_air_cap = constraints.max_air_freight_units + 50
        suggested_adjustments["max_air_freight_units"] = new_air_cap
        new_constraints.max_air_freight_units = new_air_cap

    verdict = CriticVerdict(
        is_feasible=is_feasible,
        violation_details=violations,
        retry_recommended=retry_recommended,
        retry_count=retry_count + (1 if retry_recommended else 0),
        suggested_constraint_adjustments=suggested_adjustments
    )

    action_text = "Approved plan feasibility" if is_feasible else (
        f"Rejected plan - Triggering Solver Retry {retry_count + 1}" if retry_recommended else "Rejected plan - Max Retries Reached"
    )

    details = (
        f"Critic Validation Result: Feasible={is_feasible}. Violations: {violations if violations else 'None'}. "
        f"Retry Recommended: {retry_recommended} (Iteration {retry_count + 1}/{settings.MAX_CRITIC_RETRIES})."
    )

    log_audit_entry(
        scenario_id=scenario_id,
        phase=f"CRITIC_VERIFICATION (Iteration {retry_count + 1})",
        agent_name="Critic_Agent",
        action_taken=action_text,
        model_used="Deterministic_Constraint_Validator",
        cost_impact=0.0,
        requires_approval=False,
        approval_status="AUTO_APPROVED",
        details=details
    )

    trail = list(state.get("audit_trail", []))
    trail.append({
        "phase": f"Critic (Iter {retry_count + 1})",
        "agent": "Critic_Agent",
        "action": action_text,
        "details": details
    })

    updates: Dict[str, Any] = {
        "critic_verdict": verdict,
        "audit_trail": trail
    }

    if retry_recommended:
        updates["constraints"] = new_constraints
        updates["retry_count"] = retry_count + 1

    return updates
