"""Agent 4: Multi-Carrier Allocation Planner (PuLP MILP Integration).

Formulates the parcel allocation optimization model and executes the PuLP CBC solver.
Evaluates Human-in-the-Loop (HITL) threshold requirements for high-risk, high-value orders.
"""

from typing import Dict, List
from core.schema import DispatchPlan, OrderRecord, PaymentMode
from core.config import settings
from optimizer.carrier_solver import optimize_carrier_allocation
from agents.state import IndianLogisticsState


def planner_node(state: IndianLogisticsState) -> Dict:
    """LangGraph node: Optimize carrier allocation for all valid dispatch candidates."""
    candidates = state.get("dispatched_candidates", state["raw_orders"])
    rto_scores = state.get("rto_risk_scores", {})

    # Evaluate Human-in-the-Loop (HITL) trigger
    hitl_flagged: List[str] = []
    for order in candidates:
        order_risk = rto_scores.get(order.order_id, 0.3)
        if order.order_value_inr >= settings.HITL_ORDER_VALUE_THRESHOLD_INR and (order.payment_mode == PaymentMode.COD or order_risk >= settings.HITL_HIGH_RISK_PROB_THRESHOLD):
            hitl_flagged.append(order.order_id)

    hitl_required = len(hitl_flagged) > 0 and not state.get("hitl_approved", False)

    # Solve deterministic carrier allocation
    plan = optimize_carrier_allocation(candidates, rto_scores)

    # Calculate net RTO savings vs Blind Dispatch
    # Blind dispatch baseline: assume ₹80 forward freight + ₹35 COD fee + baseline RTO loss on ALL orders
    blind_freight_per_order = 115.0  # ₹ Forward + COD fee
    rto_loss_per_order = 150.0  # ₹ Reverse + Damage

    baseline_total_cost = 0.0
    for order in state["raw_orders"]:
        initial_risk = state.get("rto_risk_scores", {}).get(order.order_id, 0.3)
        baseline_total_cost += blind_freight_per_order + (initial_risk * rto_loss_per_order)

    # Saved cost from cancelled orders (each avoided ₹115 shipping + expected RTO loss)
    cancelled_count = len(state.get("cancelled_orders", []))
    upi_count = len(state.get("upi_converted_orders", []))

    plan.parcels_cancelled_prevented_rto = cancelled_count
    plan.upi_converted_count = upi_count
    plan.rto_cost_savings_inr = round(max(0.0, baseline_total_cost - plan.total_cost_inr), 2)
    plan.hitl_approval_required = hitl_required
    if hitl_required:
        plan.hitl_approval_reason = f"{len(hitl_flagged)} high-risk orders exceed ₹{settings.HITL_ORDER_VALUE_THRESHOLD_INR:,.0f} limit"

    return {
        "dispatch_plan": plan,
        "hitl_required": hitl_required,
        "hitl_flagged_orders": hitl_flagged
    }
