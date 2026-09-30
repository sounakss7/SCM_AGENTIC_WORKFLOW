"""Unit tests for Deterministic PuLP MILP Carrier Allocation Solver."""

from core.data_loader import generate_indian_orders
from core.config import get_default_carrier_rate_cards
from core.schema import CarrierName
from optimizer.carrier_solver import optimize_carrier_allocation


def test_carrier_solver_empty_orders():
    plan = optimize_carrier_allocation(orders=[], rto_risk_scores={})
    assert plan.parcels_dispatched == 0
    assert plan.total_cost_inr == 0.0


def test_carrier_solver_allocates_all_orders():
    orders = generate_indian_orders(count=15, seed=42)
    risk_scores = {o.order_id: 0.25 for o in orders}

    plan = optimize_carrier_allocation(orders=orders, rto_risk_scores=risk_scores)

    assert plan.parcels_dispatched == 15
    assert len(plan.allocations) == 15
    assert plan.total_cost_inr > 0.0
    assert plan.solver_status == "Optimal"


def test_carrier_solver_respects_daily_hub_quotas():
    # Set artificial tight quota on Shadowfax
    rate_cards = get_default_carrier_rate_cards()
    rate_cards[CarrierName.SHADOWFAX].daily_hub_capacity = 3

    orders = generate_indian_orders(count=20, seed=10)
    risk_scores = {o.order_id: 0.20 for o in orders}

    plan = optimize_carrier_allocation(orders=orders, rto_risk_scores=risk_scores, rate_cards=rate_cards)

    shadowfax_assigned = plan.carrier_utilization.get(CarrierName.SHADOWFAX.value, 0)
    assert shadowfax_assigned <= 3
