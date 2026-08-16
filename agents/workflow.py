from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from agents.nodes import (
    user_interface_agent,
    supply_chain_intelligence_agent,
    compliance_agent,
    orchestration_agent,
    external_entities_node
)

class SCMState(TypedDict):
    order_id: str
    customer_id: str
    customer_tier: str
    current_phase: str
    inventory_status: str
    route_selected: str
    carrier_status: str
    optimization_cycles: int
    detected_disruptions: List[str]
    audit_trail: List[Dict[str, Any]]
    status: str
    requires_correction: bool
    simulate_disruption: bool
    cost_savings: str
    live_location: str
    agent_thoughts: Dict[str, str]

def ui_edge_router(state: SCMState) -> str:
    if state.get("status") == "Security Exception":
        return "end"
    return "intelligence_agent"

def orchestration_edge_router(state: SCMState) -> str:
    if state.get("status") == "Security Exception":
        return "end"
    if state.get("carrier_status") == "Booking Rejected (Port Overcapacity/Strike)":
        return "loop_to_orchestration"
    return "end"

def build_scm_workflow():
    workflow = StateGraph(SCMState)
    
    workflow.add_node("ui_agent", user_interface_agent)
    workflow.add_node("intelligence_agent", supply_chain_intelligence_agent)
    workflow.add_node("compliance_agent", compliance_agent)
    workflow.add_node("orchestration_agent", orchestration_agent)
    workflow.add_node("external_entities", external_entities_node)
    
    workflow.set_entry_point("ui_agent")
    
    workflow.add_conditional_edges(
        "ui_agent",
        ui_edge_router,
        {
            "intelligence_agent": "intelligence_agent",
            "end": END
        }
    )
    workflow.add_edge("intelligence_agent", "compliance_agent")
    workflow.add_edge("compliance_agent", "orchestration_agent")
    workflow.add_edge("orchestration_agent", "external_entities")
    
    workflow.add_conditional_edges(
        "external_entities",
        orchestration_edge_router,
        {
            "loop_to_orchestration": "orchestration_agent",
            "end": END
        }
    )
    
    return workflow.compile()

scm_workflow_graph = build_scm_workflow()

