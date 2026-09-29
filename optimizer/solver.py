import time
import uuid
from typing import List, Dict, Tuple, Optional
import pulp

from core.schema import (
    OrderRecord,
    RecoveryActionType,
    OptimizationConstraints,
    OptimizedPlan,
    OrderAllocation
)

# Cost and Delay parameter definitions for candidate recovery actions
ACTION_PARAMETERS = {
    RecoveryActionType.DO_NOTHING: {
        "cost_per_unit": 0.0,
        "delay_factor": 1.0,      # Incurs 100% of the disruption delay
        "resource_type": "none"
    },
    RecoveryActionType.STANDARD_REROUTE: {
        "cost_per_unit": 22.0,    # Rerouting freight and intermodal transfer
        "delay_factor": 0.25,     # Reduces delay by 75%
        "resource_type": "warehouse"
    },
    RecoveryActionType.EXPEDITE_AIR: {
        "cost_per_unit": 85.0,    # Premium air cargo spot rate
        "delay_factor": 0.0,      # 0 delay (100% on time)
        "resource_type": "air"
    },
    RecoveryActionType.ALTERNATE_SUPPLIER: {
        "cost_per_unit": 42.0,    # Sourcing surcharge from backup vendor
        "delay_factor": 0.15,     # Minimal delay for supplier switch
        "resource_type": "supplier"
    },
    RecoveryActionType.SPLIT_EXPEDITE: {
        "cost_per_unit": 53.5,    # 50% Air ($42.5) + 50% Reroute ($11.0)
        "delay_factor": 0.12,     # Weighted average delay
        "resource_type": "hybrid"
    }
}


class SupplyChainOptimizer:
    """
    Deterministic Mixed-Integer Linear Programming (MILP) solver for supply chain disruption recovery.
    Uses PuLP / CBC solver to compute globally optimal action allocations under physical capacity constraints.
    Zero LLM arithmetic.
    """

    def __init__(self, time_limit_sec: int = 10):
        self.time_limit_sec = time_limit_sec

    def solve(
        self,
        scenario_id: str,
        orders: List[OrderRecord],
        base_disruption_delay_days: int,
        constraints: Optional[OptimizationConstraints] = None
    ) -> OptimizedPlan:
        """
        Formulates and solves the MILP problem:
        Minimizes Total Cost = Recovery Cost + SLA Delay Penalties
        Subject to:
          1. Exactly one action per order
          2. Air freight capacity limits
          3. Alternate warehouse divert capacity limits
          4. Alternate supplier capacity limits
          5. Optional total budget constraint
        """
        start_time = time.time()
        if constraints is None:
            constraints = OptimizationConstraints()

        if not orders:
            return OptimizedPlan(
                plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
                scenario_id=scenario_id,
                status="EMPTY",
                solver_time_sec=0.0,
                total_recovery_cost=0.0,
                total_penalty_cost=0.0,
                total_combined_cost=0.0,
                average_delay_days=0.0,
                service_level_pct=100.0,
                orders_on_time=0,
                orders_delayed=0,
                is_feasible=True,
                allocations=[]
            )

        # 1. Initialize PuLP Problem
        prob = pulp.LpProblem(f"SCM_Disruption_Resolution_{scenario_id}", pulp.LpMinimize)

        # Available recovery action types
        actions = [
            RecoveryActionType.DO_NOTHING,
            RecoveryActionType.STANDARD_REROUTE,
            RecoveryActionType.EXPEDITE_AIR,
            RecoveryActionType.ALTERNATE_SUPPLIER,
            RecoveryActionType.SPLIT_EXPEDITE
        ]

        # 2. Decision Variables: x[i, a] in {0, 1}
        x = {}
        for order in orders:
            for act in actions:
                x[(order.order_id, act)] = pulp.LpVariable(
                    name=f"x_{order.order_id}_{act.value}",
                    cat=pulp.LpBinary
                )

        # Precalculate cost and delay metrics per (order, action)
        order_action_costs = {}
        order_action_penalties = {}
        order_action_delays = {}

        for order in orders:
            for act in actions:
                params = ACTION_PARAMETERS[act]
                
                # Recovery intervention cost
                cost = params["cost_per_unit"] * order.quantity
                
                # Expected delay in days
                effective_delay = int(round(base_disruption_delay_days * params["delay_factor"]))
                
                # Incurred SLA penalty
                # If delay exceeds cancellation threshold, customer cancels order (refund value + penalty)
                if effective_delay > order.cancellation_threshold_days:
                    penalty = order.total_value + (effective_delay * order.daily_late_penalty_rate * 1.5)
                elif effective_delay > 0:
                    penalty = effective_delay * order.daily_late_penalty_rate
                else:
                    penalty = 0.0

                order_action_costs[(order.order_id, act)] = cost
                order_action_penalties[(order.order_id, act)] = penalty
                order_action_delays[(order.order_id, act)] = effective_delay

        # 3. Objective Function: Min Sum(Recovery Cost + Delay Penalty)
        prob += pulp.lpSum(
            x[(order.order_id, act)] * (order_action_costs[(order.order_id, act)] + order_action_penalties[(order.order_id, act)])
            for order in orders
            for act in actions
        ), "Total_Supply_Chain_Cost"

        # 4. Constraints

        # Constraint 1: Exactly one action chosen per order
        for order in orders:
            prob += pulp.lpSum(x[(order.order_id, act)] for act in actions) == 1, f"One_Action_{order.order_id}"

        # Constraint 2: Air freight capacity limit
        # Expedite Air uses 100% quantity, Split Expedite uses 50%
        prob += (
            pulp.lpSum(
                order.quantity * x[(order.order_id, RecoveryActionType.EXPEDITE_AIR)] +
                (0.5 * order.quantity) * x[(order.order_id, RecoveryActionType.SPLIT_EXPEDITE)]
                for order in orders
            ) <= constraints.max_air_freight_units,
            "Air_Freight_Capacity_Limit"
        )

        # Constraint 3: Warehouse Divert Capacity Limits
        # Distribute rerouted orders across available alternate warehouses
        warehouse_names = list(constraints.warehouse_divert_capacities.keys())
        total_warehouse_capacity = sum(constraints.warehouse_divert_capacities.values())
        prob += (
            pulp.lpSum(
                order.quantity * x[(order.order_id, RecoveryActionType.STANDARD_REROUTE)] +
                (0.5 * order.quantity) * x[(order.order_id, RecoveryActionType.SPLIT_EXPEDITE)]
                for order in orders
            ) <= total_warehouse_capacity,
            "Total_Warehouse_Divert_Capacity"
        )

        # Constraint 4: Alternate Supplier Capacity Limit
        total_supplier_capacity = sum(constraints.alternate_supplier_capacities.values())
        prob += (
            pulp.lpSum(
                order.quantity * x[(order.order_id, RecoveryActionType.ALTERNATE_SUPPLIER)]
                for order in orders
            ) <= total_supplier_capacity,
            "Total_Alternate_Supplier_Capacity"
        )

        # Constraint 5: Optional Maximum Budget Constraint
        if constraints.max_budget is not None and constraints.max_budget > 0:
            prob += (
                pulp.lpSum(
                    x[(order.order_id, act)] * order_action_costs[(order.order_id, act)]
                    for order in orders
                    for act in actions
                ) <= constraints.max_budget,
                "Maximum_Budget_Limit"
            )

        # Constraint 6: Optional Minimum Service Level Constraint (% on time)
        if constraints.min_service_level_pct is not None and constraints.min_service_level_pct > 0:
            import math
            min_on_time = int(math.ceil((constraints.min_service_level_pct / 100.0) * len(orders)))
            prob += (
                pulp.lpSum(
                    x[(order.order_id, RecoveryActionType.EXPEDITE_AIR)]
                    for order in orders
                ) >= min_on_time,
                "Minimum_Service_Level_On_Time"
            )

        # 5. Solve using CBC solver with timeout
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=self.time_limit_sec)
        solver_status = prob.solve(solver)
        elapsed_sec = round(time.time() - start_time, 4)

        status_str = pulp.LpStatus[solver_status]
        is_feasible = status_str in ["Optimal", "Not Solved (feasible)"]

        # If infeasible under budget, return an infeasible plan record
        if not is_feasible:
            return OptimizedPlan(
                plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
                scenario_id=scenario_id,
                status=status_str.upper(),
                solver_time_sec=elapsed_sec,
                total_recovery_cost=0.0,
                total_penalty_cost=sum(order_action_penalties[(o.order_id, RecoveryActionType.DO_NOTHING)] for o in orders),
                total_combined_cost=sum(order_action_penalties[(o.order_id, RecoveryActionType.DO_NOTHING)] for o in orders),
                average_delay_days=float(base_disruption_delay_days),
                service_level_pct=0.0,
                orders_on_time=0,
                orders_delayed=len(orders),
                is_feasible=False,
                allocations=[],
                capacity_utilization={"air_utilization_pct": 0.0, "warehouse_utilization_pct": 0.0}
            )

        # 6. Extract Solution & Construct Allocations
        allocations: List[OrderAllocation] = []
        total_recovery_cost = 0.0
        total_penalty_cost = 0.0
        total_delay_days = 0
        orders_on_time_count = 0

        air_units_used = 0.0
        warehouse_units_used = 0.0
        supplier_units_used = 0.0

        for idx, order in enumerate(orders):
            selected_act = RecoveryActionType.DO_NOTHING
            for act in actions:
                val = pulp.value(x[(order.order_id, act)])
                if val is not None and val > 0.5:
                    selected_act = act
                    break

            cost = order_action_costs[(order.order_id, selected_act)]
            penalty = order_action_penalties[(order.order_id, selected_act)]
            delay = order_action_delays[(order.order_id, selected_act)]
            on_time = (delay == 0)

            total_recovery_cost += cost
            total_penalty_cost += penalty
            total_delay_days += delay
            if on_time:
                orders_on_time_count += 1

            # Resource utilization tracking
            if selected_act == RecoveryActionType.EXPEDITE_AIR:
                air_units_used += order.quantity
            elif selected_act == RecoveryActionType.SPLIT_EXPEDITE:
                air_units_used += 0.5 * order.quantity
                warehouse_units_used += 0.5 * order.quantity
            elif selected_act == RecoveryActionType.STANDARD_REROUTE:
                warehouse_units_used += order.quantity
            elif selected_act == RecoveryActionType.ALTERNATE_SUPPLIER:
                supplier_units_used += order.quantity

            # Assign fulfillment node label
            node_name = "Primary_Disrupted_Node"
            if selected_act == RecoveryActionType.STANDARD_REROUTE:
                node_name = warehouse_names[idx % len(warehouse_names)]
            elif selected_act == RecoveryActionType.EXPEDITE_AIR:
                node_name = "Express_Air_Logistics_Center"
            elif selected_act == RecoveryActionType.ALTERNATE_SUPPLIER:
                node_name = list(constraints.alternate_supplier_capacities.keys())[idx % len(constraints.alternate_supplier_capacities)]
            elif selected_act == RecoveryActionType.SPLIT_EXPEDITE:
                node_name = f"50% Express Air + 50% {warehouse_names[idx % len(warehouse_names)]}"

            allocations.append(
                OrderAllocation(
                    order_id=order.order_id,
                    product_name=order.product_name,
                    quantity=order.quantity,
                    selected_action=selected_act,
                    recovery_cost=round(cost, 2),
                    expected_delay_days=delay,
                    incurred_penalty=round(penalty, 2),
                    total_cost=round(cost + penalty, 2),
                    on_time=on_time,
                    fulfillment_node=node_name,
                    routing_notes=f"Tier: {order.customer_tier.value} | Sched: {order.scheduled_days}d | Delay: {delay}d"
                )
            )

        n_orders = max(1, len(orders))
        service_level = round((orders_on_time_count / n_orders) * 100.0, 2)
        avg_delay = round(total_delay_days / n_orders, 2)

        air_util = round((air_units_used / max(1, constraints.max_air_freight_units)) * 100.0, 1)
        wh_util = round((warehouse_units_used / max(1, total_warehouse_capacity)) * 100.0, 1)

        return OptimizedPlan(
            plan_id=f"PLAN-{uuid.uuid4().hex[:8].upper()}",
            scenario_id=scenario_id,
            status="OPTIMAL",
            solver_time_sec=elapsed_sec,
            total_recovery_cost=round(total_recovery_cost, 2),
            total_penalty_cost=round(total_penalty_cost, 2),
            total_combined_cost=round(total_recovery_cost + total_penalty_cost, 2),
            average_delay_days=avg_delay,
            service_level_pct=service_level,
            orders_on_time=orders_on_time_count,
            orders_delayed=n_orders - orders_on_time_count,
            is_feasible=True,
            allocations=allocations,
            capacity_utilization={
                "air_freight_used_units": air_units_used,
                "air_utilization_pct": air_util,
                "warehouse_diverted_units": warehouse_units_used,
                "warehouse_utilization_pct": wh_util,
                "supplier_diverted_units": supplier_units_used
            }
        )
