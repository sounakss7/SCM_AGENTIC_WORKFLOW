"""Unit tests for disruption injection and re-negotiation re-optimization."""

from core.network import get_default_network
from agents.state import DisruptionEvent
from agents.workflow import run_control_tower_pipeline


def test_supplier_delay_disruption_impact():
    net = get_default_network()
    event = DisruptionEvent(
        disruption_type="SUPPLIER_DELAY",
        affected_entity="S1",
        severity_factor=2.0,
        duration_periods=2,
        description="Supplier S1 delayed by 2 periods."
    )

    state = run_control_tower_pipeline(network=net, disruption=event, max_rounds=2)

    assert state["active_disruption"] is not None
    assert state["before_disruption_solution"] is not None
    assert state["joint_solution"] is not None

    # Disruption must record non-zero impact and negotiation rounds
    assert len(state["negotiation_log"]) >= 1
    assert "CRITICAL DISRUPTION" in state["conflict_reason"]
    assert state["joint_solution"].is_feasible is True


def test_warehouse_capacity_loss_disruption():
    net = get_default_network()
    event = DisruptionEvent(
        disruption_type="WAREHOUSE_CAPACITY_LOSS",
        affected_entity="W1",
        severity_factor=0.5,
        duration_periods=3,
        description="W1 capacity cut by 50%."
    )

    state = run_control_tower_pipeline(network=net, disruption=event, max_rounds=2)

    assert state["joint_solution"].is_feasible is True
    # Verify warehouse storage constraint was satisfied (W1 storage <= 250)
    for k, v in state["joint_solution"].warehouse_inventory.items():
        if k.startswith("W1"):
            assert v <= 250.0 + 1e-3
