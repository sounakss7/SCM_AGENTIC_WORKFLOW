from typing import Dict, Any, List
from core.data_loader import DataCoDataLoader
from core.database import log_audit_entry
from agents.state import DisruptionState

def monitor_node(state: DisruptionState) -> Dict[str, Any]:
    """
    Monitor Agent:
    Detects disruption events from telemetry feeds or simulation injections,
    identifies vulnerable active orders from the DataCo dataset, and tags them.
    """
    event = state["disruption_event"]
    scenario_id = state["scenario_id"]
    
    # If orders were not already pre-populated, query the data layer
    orders = state.get("affected_orders", [])
    if not orders:
        loader = DataCoDataLoader()
        target_warehouse = event.affected_warehouse or "Pacific_Hub_LA"
        orders = loader.sample_active_orders(n=12, origin_warehouse=target_warehouse)

    details = (
        f"Detected {event.disruption_type.value} at {event.location}. "
        f"Severity: {event.severity:.2f}, Est. Duration: {event.duration_days} days. "
        f"Identified {len(orders)} active shipments at risk."
    )

    log_audit_entry(
        scenario_id=scenario_id,
        phase="DISRUPTION_DETECTION",
        agent_name="Monitor_Agent",
        action_taken=f"Ingested {event.disruption_type.value}",
        model_used="Telemetry_Sensor_Stream",
        cost_impact=0.0,
        requires_approval=False,
        approval_status="AUTO_APPROVED",
        details=details
    )

    audit_entry = {
        "phase": "Monitor",
        "agent": "Monitor_Agent",
        "action": f"Identified {len(orders)} at-risk orders for {event.disruption_type.value}",
        "details": details
    }
    
    trail = list(state.get("audit_trail", []))
    trail.append(audit_entry)

    return {
        "affected_orders": orders,
        "audit_trail": trail
    }
