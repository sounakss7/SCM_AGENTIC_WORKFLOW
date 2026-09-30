from core.schema import PaymentMode
from core.data_loader import generate_indian_orders
from agents.workflow import run_indian_logistics_pipeline


def test_full_workflow_execution():
    orders = generate_indian_orders(count=10, seed=42)
    state = run_indian_logistics_pipeline(orders, hitl_approved=True)

    assert "dispatch_plan" in state
    plan = state["dispatch_plan"]
    assert plan is not None
    assert plan.parcels_dispatched > 0
    assert state.get("critic_passed") is True
    assert "briefing_en" in state
    assert "briefing_hi" in state
    assert len(state["briefing_hi"]) > 0


def test_workflow_hitl_flag_triggers_on_high_value():
    orders = generate_indian_orders(count=5, seed=42)
    # Inject high value COD order
    orders[0].payment_mode = PaymentMode.COD
    orders[0].order_value_inr = 8500.0
    orders[0].past_rto_count = 3  # Ensures high risk

    state = run_indian_logistics_pipeline(orders, hitl_approved=False)
    assert state.get("hitl_required") is True
    assert orders[0].order_id in state.get("hitl_flagged_orders", [])
