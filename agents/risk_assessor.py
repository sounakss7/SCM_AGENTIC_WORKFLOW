from typing import Dict, Any
from core.schema import RiskAssessment, CustomerTier
from core.database import log_audit_entry
from agents.state import DisruptionState

def risk_assessor_node(state: DisruptionState) -> Dict[str, Any]:
    """
    Risk Assessor Agent:
    Evaluates order vulnerability, value at risk, baseline delivery delays,
    and contractual SLA penalty exposure prior to mitigation.
    """
    orders = state.get("affected_orders", [])
    event = state["disruption_event"]
    scenario_id = state["scenario_id"]

    total_value = sum(o.total_value for o in orders)
    base_delay = float(event.duration_days)
    
    # Calculate baseline unmitigated penalty exposure
    total_penalty_exposure = 0.0
    high_priority_count = 0

    for o in orders:
        if o.customer_tier in [CustomerTier.VIP, CustomerTier.PREMIUM]:
            high_priority_count += 1
            
        if base_delay > o.cancellation_threshold_days:
            # Order cancellation risk: full item value + 150% penalty
            penalty = o.total_value + (base_delay * o.daily_late_penalty_rate * 1.5)
        else:
            penalty = base_delay * o.daily_late_penalty_rate
        total_penalty_exposure += penalty

    summary_text = (
        f"Assessed {len(orders)} orders (Total Cargo Value: ${total_value:,.2f}). "
        f"Unmitigated disruption delay: {base_delay:.1f} days. "
        f"Potential SLA breach penalty exposure: ${total_penalty_exposure:,.2f}. "
        f"High-priority shipments: {high_priority_count}."
    )

    assessment = RiskAssessment(
        affected_orders_count=len(orders),
        total_value_at_risk=round(total_value, 2),
        base_delay_days=base_delay,
        base_penalty_exposure=round(total_penalty_exposure, 2),
        high_priority_orders_count=high_priority_count,
        summary=summary_text
    )

    log_audit_entry(
        scenario_id=scenario_id,
        phase="RISK_ASSESSMENT",
        agent_name="Risk_Assessor_Agent",
        action_taken="Calculated unmitigated SLA exposure",
        model_used="Operations_Research_Risk_Engine",
        cost_impact=total_penalty_exposure,
        requires_approval=False,
        approval_status="AUTO_APPROVED",
        details=summary_text
    )

    trail = list(state.get("audit_trail", []))
    trail.append({
        "phase": "Risk Assessment",
        "agent": "Risk_Assessor_Agent",
        "action": f"Evaluated ${total_value:,.2f} cargo at risk (${total_penalty_exposure:,.2f} SLA exposure)",
        "details": summary_text
    })

    return {
        "risk_assessment": assessment,
        "audit_trail": trail
    }
