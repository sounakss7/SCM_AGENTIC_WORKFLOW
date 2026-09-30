"""Unit tests for Deterministic Decision Core with hand-computed known answers."""

import pytest
from core.network import get_default_indian_network
from core.disruptions import DisruptionEvent, DisruptionType, SeverityLevel
from optimizer.resilience_solver import (
    evaluate_end_to_end_route,
    find_optimal_alternate_route
)


def test_handcrafted_nominal_route_cost():
    """Hand-computed Case 1: Steady-state nominal route Pune -> JNPT -> Mumbai WH -> Mumbai Retail.

    SKU_01 (Atta), Quantity = 10 units.
    Calculation:
      Leg 1 (Pune -> JNPT via Safexpress): 145km * 0.08 * 10 = 116.0
      Leg 2 (JNPT -> WH Mumbai via Delhivery): 60km * 0.10 * 10 + 25 = 85.0
      Leg 3 (WH Mumbai -> Ret Mumbai via Delhivery): 40km * 0.10 * 10 + 25 = 65.0
      Total Freight = 266.0 INR
      Handling (JNPT 35 + WH Mum 25) * 10 = 600.0 INR
      Total Cost = 866.0 INR
      Total Transit Time = 1.0 + 0.5 + 0.5 = 2.0 days
    """
    net = get_default_indian_network()
    sku = net.skus[0]  # SKU_01

    plan = evaluate_end_to_end_route(
        network=net,
        supplier_id="SUP_PUNE",
        port_id="PORT_JNPT",
        warehouse_id="WH_MUMBAI",
        retailer_id="RET_MUMBAI",
        carrier_assignments={},
        sku=sku,
        quantity=10,
        disruption=None
    )

    assert plan.is_feasible is True
    assert plan.freight_cost_inr == pytest.approx(266.0, abs=1e-2)
    assert plan.handling_cost_inr == pytest.approx(600.0, abs=1e-2)
    assert plan.total_cost_inr == pytest.approx(866.0, abs=1e-2)
    assert plan.total_transit_days == pytest.approx(2.0, abs=1e-2)
    assert plan.delay_penalty_inr == pytest.approx(0.0, abs=1e-2)


def test_handcrafted_safexpress_strike_replan():
    """Hand-computed Case 2: Safexpress suffers critical strike (100% halted).

    Original plan becomes infeasible.
    Optimizer must dynamically switch Leg 1 to Delhivery:
      Leg 1 via Delhivery: 145km * 0.10 * 10 + 25 = 170.0 INR
      Leg 2 via Delhivery: 85.0 INR
      Leg 3 via Delhivery: 65.0 INR
      Total Freight = 320.0 INR
      Handling = 600.0 INR
      Mathematically exact optimal cost = 920.0 INR
    """
    net = get_default_indian_network()
    sku = net.skus[0]

    disruption = DisruptionEvent(
        event_id="TEST-DIS",
        disruption_type=DisruptionType.CARRIER_FAILURE,
        target_type="CARRIER",
        target_id="SAFEXPRESS",
        severity=SeverityLevel.CRITICAL,
        delay_days_added=5.0,
        cost_surcharge_pct=60.0,
        capacity_reduction_pct=100.0,
        description="Safexpress nationwide strike."
    )

    # Baseline evaluation with Safexpress must be infeasible
    baseline_plan = evaluate_end_to_end_route(
        network=net,
        supplier_id="SUP_PUNE",
        port_id="PORT_JNPT",
        warehouse_id="WH_MUMBAI",
        retailer_id="RET_MUMBAI",
        carrier_assignments={},
        sku=sku,
        quantity=10,
        disruption=disruption
    )
    assert baseline_plan.is_feasible is False

    # Optimizer must find alternate carrier (Delhivery) with exact cost 920.0 INR
    optimal_plan, _ = find_optimal_alternate_route(
        network=net,
        supplier_id="SUP_PUNE",
        retailer_id="RET_MUMBAI",
        sku=sku,
        quantity=10,
        disruption=disruption
    )

    assert optimal_plan.is_feasible is True
    assert optimal_plan.total_cost_inr == pytest.approx(920.0, abs=1e-2)
    assert optimal_plan.legs[0].carrier_id == "DELHIVERY"
