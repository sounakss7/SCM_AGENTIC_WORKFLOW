"""Unit tests for cooperating LangGraph agents workflow."""

from agents.workflow import run_control_tower_pipeline
from core.network import get_default_network


def test_agent_workflow_execution():
    net = get_default_network()
    state = run_control_tower_pipeline(network=net, max_rounds=2)

    assert "forecast_demand" in state
    assert len(state["forecast_demand"]) > 0

    assert "procurement_proposal" in state
    assert "logistics_proposal" in state
    assert "negotiation_log" in state
    assert len(state["negotiation_log"]) >= 1

    assert "joint_solution" in state
    sol = state["joint_solution"]
    assert sol is not None
    assert sol.is_feasible is True
    assert sol.total_cost > 0.0

    assert "plain_english_briefing" in state
    assert len(state["plain_english_briefing"]) > 100
    assert "Multi-Echelon Supply Chain Control Tower" in state["plain_english_briefing"]
