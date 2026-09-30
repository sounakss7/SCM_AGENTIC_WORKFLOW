"""Monitor Agent (Agent 1 in Resilience Workflow).

Watches disruption telemetry feed and cross-checks active shipments / nominal route plans.
Detects if any assigned carrier, transit port, or highway segment is impaired.
"""

from typing import Dict, Any
from agents.state import DisruptionWorkflowState
from core.disruptions import DisruptionType


def monitor_agent_node(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    """Evaluate whether an incoming disruption impacts the active nominal route plan."""
    logs = state.get("agent_logs", [])
    model_records = state.get("model_records", [])

    disruption = state.get("disruption")
    nominal_plan = state.get("nominal_plan")

    if not disruption or not nominal_plan:
        logs.append({
            "agent": "Monitor Agent",
            "action": "Inspection",
            "message": "No disruption event detected or nominal plan missing. Status nominal.",
            "status": "PASS"
        })
        return {
            "disruption_detected": False,
            "status": "NOMINAL",
            "final_plan": nominal_plan,
            "agent_logs": logs,
            "model_records": model_records
        }

    disruption_type = disruption.get("disruption_type")
    carrier = disruption.get("carrier")
    port = disruption.get("port")
    supplier = disruption.get("supplier")
    warehouse = disruption.get("warehouse")
    retailer = disruption.get("retailer")

    # Check nominal plan route components
    plan_carrier = nominal_plan.get("carrier")
    plan_port = nominal_plan.get("port")
    plan_supplier = nominal_plan.get("supplier")
    plan_warehouse = nominal_plan.get("warehouse")
    plan_retailer = nominal_plan.get("retailer")

    impacted = False
    reasons = []

    if carrier and plan_carrier == carrier:
        impacted = True
        reasons.append(f"Carrier '{carrier}' assigned to order is disrupted ({disruption.get('description')}).")

    if port and plan_port == port:
        impacted = True
        reasons.append(f"Transit Port '{port}' in routing path is congested/blocked.")

    if supplier and warehouse and plan_supplier == supplier and plan_warehouse == warehouse:
        impacted = True
        reasons.append(f"Inbound lane '{supplier}' -> '{warehouse}' is disrupted.")

    if warehouse and retailer and plan_warehouse == warehouse and plan_retailer == retailer:
        impacted = True
        reasons.append(f"Outbound lane '{warehouse}' -> '{retailer}' is disrupted.")

    if impacted:
        reason_msg = " | ".join(reasons)
        logs.append({
            "agent": "Monitor Agent",
            "action": "Alert Triggered",
            "message": f"Active disruption confirmed: {reason_msg}",
            "status": "ALERT"
        })
        return {
            "disruption_detected": True,
            "status": "DISRUPTED",
            "agent_logs": logs,
            "model_records": model_records
        }
    else:
        logs.append({
            "agent": "Monitor Agent",
            "action": "Filtered",
            "message": f"Disruption '{disruption.get('event_id')}' detected in network, but does not intersect this order's lane.",
            "status": "PASS"
        })
        return {
            "disruption_detected": False,
            "status": "NOMINAL",
            "final_plan": nominal_plan,
            "agent_logs": logs,
            "model_records": model_records
        }
