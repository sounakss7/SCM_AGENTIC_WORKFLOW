"""LangGraph 5-Agent Resilience Workflow Orchestrator.

Constructs the multi-agent graph with:
- Monitor Agent -> Risk Assessor (Gemini 2.5 Flash) -> Routing Agent (Solver Core)
  -> Validator Agent (Groq Low Latency) -> [Self-Correction Loop back to Routing if rejected]
  -> Explainer Agent (Gemini 2.5 Flash).
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END

from agents.state import DisruptionWorkflowState
from agents.monitor import monitor_agent_node
from agents.risk_agent import risk_agent_node
from agents.routing_agent import routing_agent_node
from agents.validator_agent import validator_agent_node
from agents.explainer_agent import explainer_agent_node
from optimizer.resilience_solver import find_optimal_alternate_route


def route_after_monitor(state: DisruptionWorkflowState) -> str:
    """Conditional branch after Monitor Agent."""
    if state.get("disruption_detected"):
        return "risk_assessor"
    return "explainer"


def route_after_routing(state: DisruptionWorkflowState) -> str:
    """Conditional branch after Routing Agent."""
    if state.get("status") == "FAILED" or not state.get("proposed_plan"):
        return "explainer"
    return "validator"


def route_after_validator(state: DisruptionWorkflowState) -> str:
    """Conditional branch after Validator Agent with self-correcting retry loop."""
    status = state.get("status")
    if status == "RETRYING":
        return "routing_agent"
    return "explainer"


def build_resilience_graph():
    """Build and compile the 5-Agent LangGraph StateGraph."""
    workflow = StateGraph(DisruptionWorkflowState)

    # 1. Add agent nodes
    workflow.add_node("monitor", monitor_agent_node)
    workflow.add_node("risk_assessor", risk_agent_node)
    workflow.add_node("routing_agent", routing_agent_node)
    workflow.add_node("validator", validator_agent_node)
    workflow.add_node("explainer", explainer_agent_node)

    # 2. Add entry point
    workflow.set_entry_point("monitor")

    # 3. Add conditional & direct transitions
    workflow.add_conditional_edges(
        "monitor",
        route_after_monitor,
        {
            "risk_assessor": "risk_assessor",
            "explainer": "explainer"
        }
    )

    workflow.add_edge("risk_assessor", "routing_agent")

    workflow.add_conditional_edges(
        "routing_agent",
        route_after_routing,
        {
            "validator": "validator",
            "explainer": "explainer"
        }
    )

    workflow.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "routing_agent": "routing_agent",  # Self-correction loop!
            "explainer": "explainer"
        }
    )

    workflow.add_edge("explainer", END)

    return workflow.compile()


resilience_graph = build_resilience_graph()


def run_resilience_workflow(
    order_id: str,
    sku_id: str,
    quantity: int,
    source_supplier: str,
    target_retailer: str,
    disruption: Optional[Dict[str, Any]] = None,
    nominal_plan: Optional[Dict[str, Any]] = None,
    max_retries: int = 3
) -> DisruptionWorkflowState:
    """Execute the full 5-agent LangGraph workflow for an order under disruption."""
    # Compute baseline nominal plan if not supplied
    if not nominal_plan:
        initial_solution, _ = find_optimal_alternate_route(
            supplier_id=source_supplier,
            retailer_id=target_retailer,
            sku_id=sku_id,
            quantity=quantity
        )
        if initial_solution:
            nominal_plan = initial_solution.to_dict()

    initial_state: DisruptionWorkflowState = {
        "order_id": order_id,
        "sku_id": sku_id,
        "quantity": quantity,
        "source_supplier": source_supplier,
        "target_retailer": target_retailer,
        "nominal_plan": nominal_plan,
        "disruption": disruption,
        "disruption_detected": False,
        "risk_assessment": None,
        "proposed_plan": None,
        "validation_result": None,
        "retry_count": 0,
        "max_retries": max_retries,
        "explanation": None,
        "final_plan": nominal_plan,
        "status": "INITIALIZED",
        "agent_logs": [],
        "model_records": []
    }

    final_state = resilience_graph.invoke(initial_state)
    return final_state
