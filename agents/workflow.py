"""LangGraph StateGraph workflow orchestration for Indian E-Commerce COD RTO & Last-Mile Allocation Engine."""

from typing import Dict, List, Optional
from langgraph.graph import StateGraph, START, END

from agents.state import IndianLogisticsState
from agents.address_parser import address_parser_node
from agents.rto_scorer import rto_scorer_node
from agents.whatsapp_agent import whatsapp_verification_node
from agents.planner import planner_node
from agents.critic import critic_node
from agents.explainer import explainer_node
from core.schema import OrderRecord, DispatchPlan


def should_retry_planning(state: IndianLogisticsState) -> str:
    """Evaluate whether critic constraints passed or retry is needed."""
    if state.get("critic_passed", True):
        return "explainer"
    return "planner"


def create_logistics_workflow():
    """Build and compile the multi-agent StateGraph."""
    graph = StateGraph(IndianLogisticsState)

    # Register nodes
    graph.add_node("address_parser", address_parser_node)
    graph.add_node("rto_scorer", rto_scorer_node)
    graph.add_node("whatsapp_verification", whatsapp_verification_node)
    graph.add_node("planner", planner_node)
    graph.add_node("critic", critic_node)
    graph.add_node("explainer", explainer_node)

    # Establish edges
    graph.add_edge(START, "address_parser")
    graph.add_edge("address_parser", "rto_scorer")
    graph.add_edge("rto_scorer", "whatsapp_verification")
    graph.add_edge("whatsapp_verification", "planner")
    graph.add_edge("planner", "critic")

    # Conditional retry edge
    graph.add_conditional_edges(
        "critic",
        should_retry_planning,
        {
            "explainer": "explainer",
            "planner": "planner"
        }
    )

    graph.add_edge("explainer", END)

    return graph.compile()


# Singleton compiled graph instance
compiled_workflow = create_logistics_workflow()


def run_indian_logistics_pipeline(orders: List[OrderRecord], hitl_approved: bool = False) -> Dict:
    """Execute the full agentic workflow on an incoming batch of Indian orders."""
    initial_state: IndianLogisticsState = {
        "raw_orders": orders,
        "address_scores": {},
        "parsed_addresses": {},
        "rto_risk_scores": {},
        "expected_margins": {},
        "whatsapp_results": {},
        "cancelled_orders": [],
        "upi_converted_orders": [],
        "dispatched_candidates": orders,
        "dispatch_plan": None,
        "critic_passed": False,
        "critic_violations": [],
        "retry_count": 0,
        "hitl_required": False,
        "hitl_flagged_orders": [],
        "hitl_approved": hitl_approved,
        "briefing_en": "",
        "briefing_hi": ""
    }

    final_state = compiled_workflow.invoke(initial_state)
    return final_state
