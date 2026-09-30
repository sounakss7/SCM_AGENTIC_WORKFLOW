"""Unit tests for deterministic multi-echelon optimization core on hand-crafted cases with known optimal solutions."""

import pytest
from core.network import MultiEchelonNetwork, Supplier, Warehouse, Store, SKU
from optimizer.multi_echelon_solver import solve_multi_echelon_replenishment


def build_toy_network() -> MultiEchelonNetwork:
    """Build a minimal single-lane toy network with mathematically verified costs."""
    sku = SKU(
        sku_id="SKU_A",
        name="Test Item A",
        category="Test",
        base_price=20.0,
        stockout_penalty_per_unit=50.0
    )

    supplier = Supplier(
        supplier_id="S_TOY",
        name="Toy Supplier",
        unit_procurement_costs={"SKU_A": 10.0},
        capacity_per_period=100,
        lead_time_periods=0,
        transport_cost_to_warehouse={"W_TOY": 0.0}
    )

    warehouse = Warehouse(
        warehouse_id="W_TOY",
        name="Toy Warehouse",
        storage_capacity=100,
        holding_cost_per_unit_period=1.0,
        lead_time_to_stores={"R_TOY": 0},
        shipping_cost_to_stores={"R_TOY": 2.0},
        initial_inventory={"SKU_A": 0}
    )

    store = Store(
        store_id="R_TOY",
        name="Toy Store",
        holding_cost_per_unit_period=2.0,
        stockout_penalty_per_unit={"SKU_A": 50.0},
        initial_inventory={"SKU_A": 0}
    )

    return MultiEchelonNetwork(
        suppliers=[supplier],
        warehouses=[warehouse],
        stores=[store],
        skus=[sku],
        planning_periods=1
    )


def test_handcrafted_unconstrained_optimal():
    """Hand-crafted Case 1: Unconstrained demand fulfillment.

    Demand = 10 units.
    Cost breakdown:
      Procurement: 10 * $10 = $100
      Transport: 10 * $2 = $20
      Stockouts: 0 * $50 = $0
      Total mathematically known cost = $120.00
    """
    toy_net = build_toy_network()
    demand = {("R_TOY", "SKU_A", 1): 10.0}

    sol = solve_multi_echelon_replenishment(toy_net, demand)

    assert sol.is_feasible is True
    assert sol.total_cost == pytest.approx(120.0, abs=1e-2)
    assert sol.procurement_cost == pytest.approx(100.0, abs=1e-2)
    assert sol.transport_cost == pytest.approx(20.0, abs=1e-2)
    assert sol.stockout_cost == pytest.approx(0.0, abs=1e-2)
    assert sol.total_fulfilled_units == pytest.approx(10.0, abs=1e-2)
    assert sol.service_level_pct == pytest.approx(100.0, abs=1e-2)


def test_handcrafted_capacity_constrained_stockout():
    """Hand-crafted Case 2: Supplier capacity constrained to 6 units.

    Demand = 10 units.
    Available units = 6. Unmet stockout = 4 units.
    Cost breakdown:
      Procurement: 6 * $10 = $60
      Transport: 6 * $2 = $12
      Stockout Penalty: 4 * $50 = $200
      Total mathematically known cost = $272.00
    """
    toy_net = build_toy_network()
    demand = {("R_TOY", "SKU_A", 1): 10.0}

    # Override supplier capacity to 6 units
    sol = solve_multi_echelon_replenishment(
        toy_net,
        demand,
        supplier_capacity_override={"S_TOY": 6}
    )

    assert sol.is_feasible is True
    assert sol.total_cost == pytest.approx(272.0, abs=1e-2)
    assert sol.procurement_cost == pytest.approx(60.0, abs=1e-2)
    assert sol.transport_cost == pytest.approx(12.0, abs=1e-2)
    assert sol.stockout_cost == pytest.approx(200.0, abs=1e-2)
    assert sol.total_fulfilled_units == pytest.approx(6.0, abs=1e-2)
    assert sol.total_stockout_units == pytest.approx(4.0, abs=1e-2)
    assert sol.service_level_pct == pytest.approx(60.0, abs=1e-2)
