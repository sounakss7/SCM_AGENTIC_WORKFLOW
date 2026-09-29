from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from agents.state import DisruptionState
from agents.monitor import monitor_node
from agents.risk_assessor import risk_assessor_node
from agents.planner import planner_node
from agents.critic import critic_node
from agents.explainer import explainer_node

def critic_router(state: DisruptionState) -> Literal["planner", "explainer"]:
    """
    Evaluates whether the critic rejected the plan and recommended a retry loop.
    """
    critic_verdict = state.get("critic_verdict")
    if critic_verdict and critic_verdict.retry_recommended:
        return "planner"
    return "explainer"

def build_scm_graph():
    """
    Constructs and compiles the cyclic LangGraph StateGraph for SCM Disruption Response.
    
    Flow:
    START ➔ monitor ➔ risk_assessor ➔ planner ➔ critic
                                         ▲          │
                                         │(retry)   │(feasible)
                                         └──────────┴──➔ explainer ➔ END
    """
    workflow = StateGraph(DisruptionState)

    workflow.add_node("monitor", monitor_node)
    workflow.add_node("risk_assessor", risk_assessor_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("explainer", explainer_node)

    workflow.add_edge(START, "monitor")
    workflow.add_edge("monitor", "risk_assessor")
    workflow.add_edge("risk_assessor", "planner")
    workflow.add_edge("planner", "critic")

    workflow.add_conditional_edges(
        "critic",
        critic_router,
        {
            "planner": "planner",
            "explainer": "explainer"
        }
    )

    workflow.add_edge("explainer", END)

    return workflow.compile()

scm_graph = build_scm_graph()
