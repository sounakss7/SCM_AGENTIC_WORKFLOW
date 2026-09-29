import pytest
from core.schema import (
    OrderRecord,
    CustomerTier,
    ShippingMode,
    RecoveryActionType,
    OptimizationConstraints
)
from optimizer.solver import SupplyChainOptimizer

def make_test_order(order_id: str, qty: int, price: float, tier: CustomerTier = CustomerTier.STANDARD) -> OrderRecord:
    return OrderRecord(
        order_id=order_id,
        customer_id="CUST-TEST",
        customer_state="CA",
        customer_country="United States",
        customer_tier=tier,
        product_id=101,
        product_name="Test Product",
        category_name="Testing",
        quantity=qty,
        unit_price=price,
        total_value=qty * price,
        shipping_mode=ShippingMode.STANDARD,
        scheduled_days=4,
        real_days=4,
        late_delivery_risk=0,
        origin_warehouse="Pacific_Hub_LA",
        destination="CA",
        status="PENDING",
        daily_late_penalty_rate=20.0,
        cancellation_threshold_days=8
    )

def test_optimizer_empty_orders():
    solver = SupplyChainOptimizer()
    plan = solver.solve("scen_empty", orders=[], base_disruption_delay_days=5)
    assert plan.status == "EMPTY"
    assert plan.total_combined_cost == 0.0
    assert plan.is_feasible is True

def test_optimizer_feasibility_and_optimality():
    solver = SupplyChainOptimizer()
    orders = [
        make_test_order("ORD-1", qty=2, price=100.0, tier=CustomerTier.VIP),
        make_test_order("ORD-2", qty=5, price=40.0, tier=CustomerTier.STANDARD),
        make_test_order("ORD-3", qty=1, price=300.0, tier=CustomerTier.PREMIUM)
    ]
    constraints = OptimizationConstraints(max_air_freight_units=100)
    plan = solver.solve("scen_test", orders=orders, base_disruption_delay_days=7, constraints=constraints)

    assert plan.status == "OPTIMAL"
    assert plan.is_feasible is True
    assert len(plan.allocations) == 3
    assert plan.total_combined_cost > 0.0
    # Every order must have an assigned action
    for alloc in plan.allocations:
        assert alloc.selected_action in RecoveryActionType

def test_optimizer_respects_air_capacity_constraint():
    solver = SupplyChainOptimizer()
    # 5 orders of 20 units = 100 units total. Max air capacity is only 20 units.
    orders = [make_test_order(f"ORD-{i}", qty=20, price=200.0, tier=CustomerTier.VIP) for i in range(1, 6)]
    constraints = OptimizationConstraints(max_air_freight_units=20)

    plan = solver.solve("scen_air_cap", orders=orders, base_disruption_delay_days=10, constraints=constraints)
    assert plan.status == "OPTIMAL"
    
    air_units_used = plan.capacity_utilization.get("air_freight_used_units", 0)
    assert air_units_used <= constraints.max_air_freight_units, f"Used {air_units_used} > {constraints.max_air_freight_units}"

def test_optimizer_infeasible_constraints():
    solver = SupplyChainOptimizer()
    orders = [make_test_order("ORD-EXPENSIVE", qty=50, price=100.0)]
    # Set impossible constraints: 100% on-time delivery required, but air freight capacity is 0
    constraints = OptimizationConstraints(min_service_level_pct=100.0, max_air_freight_units=0)
    
    plan = solver.solve("scen_infeasible", orders=orders, base_disruption_delay_days=5, constraints=constraints)
    assert plan.is_feasible is False
    assert plan.status in ["INFEASIBLE", "NOT SOLVED"]
