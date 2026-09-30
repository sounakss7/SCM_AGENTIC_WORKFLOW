"""Generates N=200 randomized multi-echelon scenarios with fixed seeds (normal + disrupted)."""

import random
from typing import List, Dict, Tuple, Any, Optional
from agents.state import DisruptionEvent
from core.demand_data import get_horizon_demand, STORES, SKUS


def generate_200_scenarios(seed: int = 42) -> List[Dict[str, Any]]:
    """Generate 200 deterministic multi-echelon evaluation scenarios.

    Distribution:
    - Scenarios 1-100: Normal stochastic demand operations
    - Scenarios 101-125: Supplier Delay disruption (S1 lead time +2 periods)
    - Scenarios 126-150: Port Congestion disruption (S1->W1 lane throttled)
    - Scenarios 151-175: Demand Spike disruption (+80% to +100% store demand surge)
    - Scenarios 176-200: Warehouse Capacity Loss disruption (W1 storage capacity cut by 50%)
    """
    rng = random.Random(seed)
    scenarios: List[Dict[str, Any]] = []

    for s_id in range(1, 201):
        s_seed = seed + s_id * 31

        disruption: Optional[DisruptionEvent] = None

        if 101 <= s_id <= 125:
            disruption = DisruptionEvent(
                disruption_type="SUPPLIER_DELAY",
                affected_entity="S1",
                severity_factor=2.0,
                duration_periods=2,
                description="Global supplier S1 factory strike; lead time increased from 2 to 4 periods."
            )
        elif 126 <= s_id <= 150:
            disruption = DisruptionEvent(
                disruption_type="PORT_CONGESTION",
                affected_entity="S1->W1",
                severity_factor=0.3,  # Lane capacity cut to 30%
                duration_periods=2,
                description="Container port congestion chokes S1->W1 inbound maritime lane."
            )
        elif 151 <= s_id <= 175:
            target_store = rng.choice(STORES)
            disruption = DisruptionEvent(
                disruption_type="DEMAND_SPIKE",
                affected_entity=target_store,
                severity_factor=1.85,  # +85% demand surge
                duration_periods=2,
                description=f"Regional promotion and panic buying surge at {target_store}."
            )
        elif 176 <= s_id <= 200:
            disruption = DisruptionEvent(
                disruption_type="WAREHOUSE_CAPACITY_LOSS",
                affected_entity="W1",
                severity_factor=0.5,  # 50% capacity cut
                duration_periods=3,
                description="Logistics hub W1 sprinkler pipe burst; storage capacity halved to 250 units."
            )

        # Generate ground truth demand for this scenario
        demand_mult = None
        if disruption and disruption.disruption_type == "DEMAND_SPIKE":
            demand_mult = {disruption.affected_entity: disruption.severity_factor}

        demand = get_horizon_demand(
            start_period=(s_id % 18) + 1,
            horizon_length=4,
            disruption_multiplier=demand_mult,
            seed=s_seed
        )

        scenarios.append({
            "scenario_id": s_id,
            "seed": s_seed,
            "disruption": disruption,
            "demand": demand
        })

    return scenarios
