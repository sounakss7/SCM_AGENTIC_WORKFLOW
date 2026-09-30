"""Deterministic Multi-Echelon Supply Chain Mixed-Integer / Linear Programming Solver.

Formulates and solves the replenishment and routing optimization problem across
Suppliers -> Warehouses -> Stores over a multi-period planning horizon using PuLP / CBC.

Minimizes:
  Total Cost = Procurement Cost + Transport Cost + Holding Cost (WH + Store) + Stockout Penalty

Subject to:
  1. Multi-period warehouse inventory balance with lead-time delayed supplier arrivals
  2. Multi-period store inventory balance & demand fulfillment with lead-time delayed arrivals
  3. Supplier periodic capacity limits
  4. Warehouse storage capacity limits
  5. Lane throughput limits
  6. Non-negativity of inventory, shipments, and stockouts
"""

from typing import Dict, List, Tuple, Optional, Any
from pydantic import BaseModel, Field
import pulp

from core.network import MultiEchelonNetwork, get_default_network


class MultiEchelonSolution(BaseModel):
    status: str
    is_feasible: bool
    total_cost: float = Field(..., ge=0.0)
    procurement_cost: float = Field(..., ge=0.0)
    transport_cost: float = Field(..., ge=0.0)
    holding_cost: float = Field(..., ge=0.0)
    stockout_cost: float = Field(..., ge=0.0)
    total_demand_units: float = Field(..., ge=0.0)
    total_fulfilled_units: float = Field(..., ge=0.0)
    total_stockout_units: float = Field(..., ge=0.0)
    service_level_pct: float = Field(..., ge=0.0, le=100.0)
    stockout_rate_pct: float = Field(..., ge=0.0, le=100.0)
    supplier_orders: Dict[str, float] = Field(default_factory=dict)     # "S1->W1:SKU_101:t1": qty
    warehouse_orders: Dict[str, float] = Field(default_factory=dict)    # "W1->R1:SKU_101:t1": qty
    warehouse_inventory: Dict[str, float] = Field(default_factory=dict) # "W1:SKU_101:t1": qty
    store_inventory: Dict[str, float] = Field(default_factory=dict)     # "R1:SKU_101:t1": qty
    store_stockouts: Dict[str, float] = Field(default_factory=dict)     # "R1:SKU_101:t1": qty


def solve_multi_echelon_replenishment(
    network: MultiEchelonNetwork,
    demand: Dict[Tuple[str, str, int], float],  # (store_id, sku_id, period) -> demand units
    supplier_capacity_override: Optional[Dict[str, int]] = None,
    warehouse_capacity_override: Optional[Dict[str, int]] = None,
    supplier_lead_time_override: Optional[Dict[str, int]] = None,
    lane_capacity_override: Optional[Dict[Tuple[str, str], int]] = None,
    initial_in_transit_wh: Optional[Dict[Tuple[str, str, int], float]] = None,
    initial_in_transit_store: Optional[Dict[Tuple[str, str, int], float]] = None
) -> MultiEchelonSolution:
    """Solve the multi-echelon replenishment problem via linear/integer programming."""
    T = network.planning_periods
    periods = list(range(1, T + 1))

    suppliers = {s.supplier_id: s for s in network.suppliers}
    warehouses = {w.warehouse_id: w for w in network.warehouses}
    stores = {r.store_id: r for r in network.stores}
    skus = {k.sku_id: k for k in network.skus}

    s_ids = list(suppliers.keys())
    w_ids = list(warehouses.keys())
    r_ids = list(stores.keys())
    k_ids = list(skus.keys())

    # Build PuLP model
    model = pulp.LpProblem("Multi_Echelon_Replenishment_Optimization", pulp.LpMinimize)

    # 1. Decision Variables
    # X[s, w, k, t]: orders placed from supplier s to warehouse w in period t
    X = {}
    for s in s_ids:
        for w in w_ids:
            for k in k_ids:
                for t in periods:
                    X[(s, w, k, t)] = pulp.LpVariable(f"X_{s}_{w}_{k}_t{t}", lowBound=0, cat=pulp.LpContinuous)

    # Y[w, r, k, t]: replenishment dispatched from warehouse w to store r in period t
    Y = {}
    for w in w_ids:
        for r in r_ids:
            for k in k_ids:
                for t in periods:
                    Y[(w, r, k, t)] = pulp.LpVariable(f"Y_{w}_{r}_{k}_t{t}", lowBound=0, cat=pulp.LpContinuous)

    # InvW[w, k, t]: inventory at warehouse w at the end of period t
    InvW = {}
    for w in w_ids:
        for k in k_ids:
            for t in periods:
                InvW[(w, k, t)] = pulp.LpVariable(f"InvW_{w}_{k}_t{t}", lowBound=0, cat=pulp.LpContinuous)

    # InvR[r, k, t]: inventory at store r at the end of period t
    InvR = {}
    for r in r_ids:
        for k in k_ids:
            for t in periods:
                InvR[(r, k, t)] = pulp.LpVariable(f"InvR_{r}_{k}_t{t}", lowBound=0, cat=pulp.LpContinuous)

    # Stockout[r, k, t]: unmet demand at store r in period t
    Stockout = {}
    for r in r_ids:
        for k in k_ids:
            for t in periods:
                Stockout[(r, k, t)] = pulp.LpVariable(f"U_{r}_{k}_t{t}", lowBound=0, cat=pulp.LpContinuous)

    # 2. Objective Function:
    # Min (Procurement + Supplier-to-WH transport + WH-to-Store shipping + WH holding + Store holding + Stockout penalty)
    cost_proc = []
    cost_trans_wh = []
    cost_trans_store = []
    cost_holding_wh = []
    cost_holding_store = []
    cost_stockout = []

    for t in periods:
        for k in k_ids:
            # Supplier to Warehouse
            for s in s_ids:
                for w in w_ids:
                    unit_p = suppliers[s].unit_procurement_costs.get(k, 25.0)
                    trans_p = suppliers[s].transport_cost_to_warehouse.get(w, 2.5)
                    cost_proc.append(X[(s, w, k, t)] * unit_p)
                    cost_trans_wh.append(X[(s, w, k, t)] * trans_p)

            # Warehouse to Store
            for w in w_ids:
                for r in r_ids:
                    ship_p = warehouses[w].shipping_cost_to_stores.get(r, 4.0)
                    cost_trans_store.append(Y[(w, r, k, t)] * ship_p)

            # Warehouse Holding
            for w in w_ids:
                h_w = warehouses[w].holding_cost_per_unit_period
                cost_holding_wh.append(InvW[(w, k, t)] * h_w)

            # Store Holding & Stockout
            for r in r_ids:
                h_r = stores[r].holding_cost_per_unit_period
                penalty = stores[r].stockout_penalty_per_unit.get(k, 50.0)
                cost_holding_store.append(InvR[(r, k, t)] * h_r)
                cost_stockout.append(Stockout[(r, k, t)] * penalty)

    model += (
        pulp.lpSum(cost_proc) +
        pulp.lpSum(cost_trans_wh) +
        pulp.lpSum(cost_trans_store) +
        pulp.lpSum(cost_holding_wh) +
        pulp.lpSum(cost_holding_store) +
        pulp.lpSum(cost_stockout)
    )

    # 3. Constraints

    # (A) Warehouse Inventory Flow Balance
    for w in w_ids:
        for k in k_ids:
            for t in periods:
                prev_inv = warehouses[w].initial_inventory.get(k, 0.0) if t == 1 else InvW[(w, k, t - 1)]

                # Arrivals from suppliers arriving at time t
                arrivals = []
                for s in s_ids:
                    # Check lead time
                    lt = supplier_lead_time_override.get(s, suppliers[s].lead_time_periods) if supplier_lead_time_override else suppliers[s].lead_time_periods
                    order_period = t - lt
                    if order_period >= 1:
                        arrivals.append(X[(s, w, k, order_period)])
                    elif initial_in_transit_wh and (s, w, k, t) in initial_in_transit_wh:
                        arrivals.append(initial_in_transit_wh[(s, w, k, t)])

                # Outflow to stores
                outflows = [Y[(w, r, k, t)] for r in r_ids]

                model += (
                    InvW[(w, k, t)] == prev_inv + pulp.lpSum(arrivals) - pulp.lpSum(outflows),
                    f"FlowBal_WH_{w}_{k}_t{t}"
                )

    # (B) Store Inventory Flow Balance & Demand Satisfaction
    for r in r_ids:
        for k in k_ids:
            for t in periods:
                prev_inv = stores[r].initial_inventory.get(k, 0.0) if t == 1 else InvR[(r, k, t - 1)]

                # Arrivals from warehouses arriving at store at time t
                arrivals = []
                for w in w_ids:
                    lt = warehouses[w].lead_time_to_stores.get(r, 1)
                    dispatch_period = t - lt
                    if dispatch_period >= 1:
                        arrivals.append(Y[(w, r, k, dispatch_period)])
                    elif initial_in_transit_store and (w, r, k, t) in initial_in_transit_store:
                        arrivals.append(initial_in_transit_store[(w, r, k, t)])

                cur_demand = demand.get((r, k, t), 0.0)

                # Balance equation: Inv(t) - Stockout(t) = Inv(t-1) + Arrivals - Demand
                model += (
                    InvR[(r, k, t)] - Stockout[(r, k, t)] == prev_inv + pulp.lpSum(arrivals) - cur_demand,
                    f"FlowBal_Store_{r}_{k}_t{t}"
                )

    # (C) Supplier Periodic Capacity
    for s in s_ids:
        cap = supplier_capacity_override.get(s, suppliers[s].capacity_per_period) if supplier_capacity_override else suppliers[s].capacity_per_period
        for t in periods:
            model += (
                pulp.lpSum([X[(s, w, k, t)] for w in w_ids for k in k_ids]) <= cap,
                f"Cap_Supplier_{s}_t{t}"
            )

    # (D) Warehouse Storage Capacity
    for w in w_ids:
        cap = warehouse_capacity_override.get(w, warehouses[w].storage_capacity) if warehouse_capacity_override else warehouses[w].storage_capacity
        for t in periods:
            model += (
                pulp.lpSum([InvW[(w, k, t)] for k in k_ids]) <= cap,
                f"Cap_WH_Storage_{w}_t{t}"
            )

    # (E) Transport Lane Capacities (if specified)
    if lane_capacity_override:
        for (src, dst), l_cap in lane_capacity_override.items():
            for t in periods:
                if src in s_ids and dst in w_ids:
                    model += (pulp.lpSum([X[(src, dst, k, t)] for k in k_ids]) <= l_cap, f"LaneCap_{src}_{dst}_t{t}")
                elif src in w_ids and dst in r_ids:
                    model += (pulp.lpSum([Y[(src, dst, k, t)] for k in k_ids]) <= l_cap, f"LaneCap_{src}_{dst}_t{t}")

    # Solve with CBC
    solver = pulp.PULP_CBC_CMD(msg=False)
    status_code = model.solve(solver)
    status_str = pulp.LpStatus[status_code]
    is_feasible = status_str in ["Optimal", "Feasible"]

    if not is_feasible:
        return MultiEchelonSolution(
            status=status_str,
            is_feasible=False,
            total_cost=9999999.0,
            procurement_cost=0.0,
            transport_cost=0.0,
            holding_cost=0.0,
            stockout_cost=9999999.0,
            total_demand_units=sum(demand.values()),
            total_fulfilled_units=0.0,
            total_stockout_units=sum(demand.values()),
            service_level_pct=0.0,
            stockout_rate_pct=100.0
        )

    # Extract numerical results
    total_cost_val = float(pulp.value(model.objective) or 0.0)
    proc_cost_val = float(sum(pulp.value(c) for c in cost_proc) or 0.0)
    trans_cost_val = float(sum(pulp.value(c) for c in cost_trans_wh) + sum(pulp.value(c) for c in cost_trans_store) or 0.0)
    holding_cost_val = float(sum(pulp.value(c) for c in cost_holding_wh) + sum(pulp.value(c) for c in cost_holding_store) or 0.0)
    stockout_cost_val = float(sum(pulp.value(c) for c in cost_stockout) or 0.0)

    total_demand = sum(demand.values())
    total_stockout = sum(float(pulp.value(Stockout[(r, k, t)]) or 0.0) for r in r_ids for k in k_ids for t in periods)
    total_fulfilled = max(0.0, total_demand - total_stockout)

    service_level = (total_fulfilled / total_demand * 100.0) if total_demand > 0 else 100.0
    stockout_rate = (total_stockout / total_demand * 100.0) if total_demand > 0 else 0.0

    # Build shipment and inventory dictionaries
    supplier_orders = {}
    for s in s_ids:
        for w in w_ids:
            for k in k_ids:
                for t in periods:
                    val = float(pulp.value(X[(s, w, k, t)]) or 0.0)
                    if val > 0.01:
                        supplier_orders[f"{s}->{w}:{k}:t{t}"] = round(val, 1)

    warehouse_orders = {}
    for w in w_ids:
        for r in r_ids:
            for k in k_ids:
                for t in periods:
                    val = float(pulp.value(Y[(w, r, k, t)]) or 0.0)
                    if val > 0.01:
                        warehouse_orders[f"{w}->{r}:{k}:t{t}"] = round(val, 1)

    wh_inv = {}
    for w in w_ids:
        for k in k_ids:
            for t in periods:
                wh_inv[f"{w}:{k}:t{t}"] = round(float(pulp.value(InvW[(w, k, t)]) or 0.0), 1)

    store_inv = {}
    for r in r_ids:
        for k in k_ids:
            for t in periods:
                store_inv[f"{r}:{k}:t{t}"] = round(float(pulp.value(InvR[(r, k, t)]) or 0.0), 1)

    store_stockouts = {}
    for r in r_ids:
        for k in k_ids:
            for t in periods:
                val = float(pulp.value(Stockout[(r, k, t)]) or 0.0)
                if val > 0.01:
                    store_stockouts[f"{r}:{k}:t{t}"] = round(val, 1)

    return MultiEchelonSolution(
        status=status_str,
        is_feasible=True,
        total_cost=round(total_cost_val, 2),
        procurement_cost=round(proc_cost_val, 2),
        transport_cost=round(trans_cost_val, 2),
        holding_cost=round(holding_cost_val, 2),
        stockout_cost=round(stockout_cost_val, 2),
        total_demand_units=round(total_demand, 1),
        total_fulfilled_units=round(total_fulfilled, 1),
        total_stockout_units=round(total_stockout, 1),
        service_level_pct=round(service_level, 2),
        stockout_rate_pct=round(stockout_rate, 2),
        supplier_orders=supplier_orders,
        warehouse_orders=warehouse_orders,
        warehouse_inventory=wh_inv,
        store_inventory=store_inv,
        store_stockouts=store_stockouts
    )
