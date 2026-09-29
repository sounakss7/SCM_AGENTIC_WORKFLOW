import pytest
from core.schema import (
    DisruptionEvent,
    DisruptionType,
    OptimizationConstraints
)
from agents.workflow import scm_graph

def test_workflow_execution():
    event = DisruptionEvent(
        event_id="EVT-UNIT-TEST",
        disruption_type=DisruptionType.CARRIER_FAILURE,
        location="Chicago Intermodal Terminal",
        severity=0.75,
        duration_days=6,
        affected_warehouse="Midwest_Hub_Chicago",
        description="Regional rail carrier failure affecting shipments."
    )

    init_state = {
        "scenario_id": "SCEN-UNIT-TEST",
        "disruption_event": event,
        "affected_orders": [],
        "risk_assessment": None,
        "constraints": OptimizationConstraints(),
        "optimized_plan": None,
        "critic_verdict": None,
        "explanation": "",
        "requires_human_approval": False,
        "approval_status": "AUTO_APPROVED",
        "retry_count": 0,
        "llm_call_count": 0,
        "audit_trail": []
    }

    final_state = scm_graph.invoke(init_state)

    # Assert all nodes executed properly
    assert len(final_state["affected_orders"]) > 0
    assert final_state["risk_assessment"] is not None
    assert final_state["risk_assessment"].affected_orders_count == len(final_state["affected_orders"])
    assert final_state["optimized_plan"] is not None
    assert final_state["optimized_plan"].is_feasible is True
    assert final_state["critic_verdict"] is not None
    assert final_state["critic_verdict"].is_feasible is True
    assert len(final_state["explanation"]) > 0
    assert len(final_state["audit_trail"]) >= 4

def test_workflow_hitl_approval_flag():
    # Large order batch with high value should trigger HITL approval requirement
    event = DisruptionEvent(
        event_id="EVT-HIGH-VALUE",
        disruption_type=DisruptionType.PORT_CONGESTION,
        location="Port of Los Angeles",
        severity=0.9,
        duration_days=14,
        affected_warehouse="Pacific_Hub_LA",
        description="Major 14-day port disruption."
    )

    from core.data_loader import DataCoDataLoader
    loader = DataCoDataLoader()
    orders = loader.sample_active_orders(n=40, origin_warehouse="Pacific_Hub_LA", random_seed=999)

    init_state = {
        "scenario_id": "SCEN-HITL-TEST",
        "disruption_event": event,
        "affected_orders": orders,
        "risk_assessment": None,
        "constraints": OptimizationConstraints(),
        "optimized_plan": None,
        "critic_verdict": None,
        "explanation": "",
        "requires_human_approval": False,
        "approval_status": "AUTO_APPROVED",
        "retry_count": 0,
        "llm_call_count": 0,
        "audit_trail": []
    }

    final_state = scm_graph.invoke(init_state)
    assert final_state["optimized_plan"] is not None
    if final_state["optimized_plan"].total_recovery_cost > 5000.0:
        assert final_state["requires_human_approval"] is True
        assert final_state["approval_status"] == "PENDING"
