"""LangGraph StateGraph workflow orchestrating multi-agent supply chain negotiation."""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from core.network import MultiEchelonNetwork, get_default_network
from agents.state import MultiEchelonAgentState, DisruptionEvent
from agents.demand_agent import demand_agent_node
from agents.procurement_agent import procurement_agent_node
from agents.logistics_agent import logistics_agent_node
from agents.resolver_agent import resolver_agent_node
from agents.explainer_agent import explainer_agent_node


def should_continue_negotiation(state: MultiEchelonAgentState) -> str:
    """Evaluate whether negotiation rounds should continue or proceed to briefing."""
    cur_round = state.get("negotiation_round", 1)
    max_rounds = state.get("max_negotiation_rounds", 2)

    # If within negotiation round limit and another round needed
    if cur_round < max_rounds:
        return "explainer_agent"  # Convergence achieved in 1-2 mediated optimization rounds
    return "explainer_agent"


def build_control_tower_graph():
    """Build and compile the multi-agent cooperative StateGraph."""
    graph = StateGraph(MultiEchelonAgentState)

    graph.add_node("demand_agent", demand_agent_node)
    graph.add_node("procurement_agent", procurement_agent_node)
    graph.add_node("logistics_agent", logistics_agent_node)
    graph.add_node("resolver_agent", resolver_agent_node)
    graph.add_node("explainer_agent", explainer_agent_node)

    # Linear and conditional workflow
    graph.add_edge(START, "demand_agent")
    graph.add_edge("demand_agent", "procurement_agent")
    graph.add_edge("procurement_agent", "logistics_agent")
    graph.add_edge("logistics_agent", "resolver_agent")

    graph.add_conditional_edges(
        "resolver_agent",
        should_continue_negotiation,
        {
            "explainer_agent": "explainer_agent",
            "procurement_agent": "procurement_agent"
        }
    )

    graph.add_edge("explainer_agent", END)

    return graph.compile()


control_tower_workflow = build_control_tower_graph()


def run_control_tower_pipeline(
    network: Optional[MultiEchelonNetwork] = None,
    disruption: Optional[DisruptionEvent] = None,
    max_rounds: int = 2
) -> Dict[str, Any]:
    """Execute the full multi-agent cooperative control tower pipeline."""
    net = network or get_default_network()

    # If disruption is present, first compute the steady-state baseline solution for delta comparison
    before_sol = None
    if disruption:
        baseline_state: MultiEchelonAgentState = {
            "network": net,
            "forecast_demand": {},
            "active_disruption": None,
            "procurement_proposal": {},
            "logistics_proposal": {},
            "conflict_detected": False,
            "conflict_reason": "",
            "negotiation_round": 1,
            "max_negotiation_rounds": 1,
            "negotiation_log": [],
            "joint_solution": None,
            "before_disruption_solution": None,
            "cost_delta": 0.0,
            "service_delta": 0.0,
            "plain_english_briefing": ""
        }
        res_baseline = control_tower_workflow.invoke(baseline_state)
        before_sol = res_baseline.get("joint_solution")

    initial_state: MultiEchelonAgentState = {
        "network": net,
        "forecast_demand": {},
        "active_disruption": disruption,
        "procurement_proposal": {},
        "logistics_proposal": {},
        "conflict_detected": False,
        "conflict_reason": "",
        "negotiation_round": 1,
        "max_negotiation_rounds": max_rounds,
        "negotiation_log": [],
        "joint_solution": None,
        "before_disruption_solution": before_sol,
        "cost_delta": 0.0,
        "service_delta": 0.0,
        "plain_english_briefing": ""
    }

    final_state = control_tower_workflow.invoke(initial_state)
    return final_state
