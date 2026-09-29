import random
from typing import List, Dict, Any
import numpy as np

from core.schema import (
    DisruptionEvent,
    DisruptionType,
    OptimizationConstraints,
    OrderRecord
)
from core.data_loader import DataCoDataLoader

DISRUPTION_LOCATIONS = [
    ("Port of Los Angeles", "Pacific_Hub_LA", DisruptionType.PORT_CONGESTION),
    ("Long Beach Container Terminal", "Pacific_Hub_LA", DisruptionType.PORT_CONGESTION),
    ("Chicago Rail Logistics Intermodal", "Midwest_Hub_Chicago", DisruptionType.CARRIER_FAILURE),
    ("Newark Marine Terminal", "EastCoast_Hub_NJ", DisruptionType.PORT_CONGESTION),
    ("Dallas-Fort Worth Freight Corridor", "South_Hub_Dallas", DisruptionType.SEVERE_WEATHER),
    ("Rotterdam Deep-Sea Harbor", "Europe_Hub_Rotterdam", DisruptionType.PORT_CONGESTION),
    ("Midwest Component Fabrication Plant", "Midwest_Hub_Chicago", DisruptionType.SUPPLIER_DELAY),
    ("Shenzhen Pacific Sea Route", "Pacific_Hub_LA", DisruptionType.SEVERE_WEATHER),
    ("National Express Ground Fleet Strike", "South_Hub_Dallas", DisruptionType.CARRIER_FAILURE),
    ("Regional Distribution Surge", "Midwest_Hub_Chicago", DisruptionType.DEMAND_SPIKE)
]

def generate_benchmark_scenarios(n: int = 200, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generates N randomized, reproducible disruption scenarios with fixed random seed.
    Each scenario contains:
      - scenario_id
      - disruption_event
      - affected_orders (sampled from DataCo dataset)
      - optimization_constraints (with varied physical limits)
    """
    rng = np.random.default_rng(seed)
    py_rng = random.Random(seed)
    
    loader = DataCoDataLoader()
    scenarios: List[Dict[str, Any]] = []

    for idx in range(1, n + 1):
        scen_id = f"SCEN-{idx:03d}"
        
        # Pick location and disruption type
        loc_info = py_rng.choice(DISRUPTION_LOCATIONS)
        loc_name, wh_node, dtype = loc_info
        
        # Duration between 3 and 18 days
        duration = int(rng.integers(3, 19))
        severity = float(round(rng.uniform(0.50, 0.95), 2))
        
        event = DisruptionEvent(
            event_id=f"EVT-{idx:03d}",
            disruption_type=dtype,
            location=loc_name,
            severity=severity,
            duration_days=duration,
            affected_warehouse=wh_node,
            description=f"Automated benchmark disruption: {dtype.value} event at {loc_name} (est. {duration} days duration)."
        )

        # Sample between 6 and 22 active orders affected by this disruption
        order_count = int(rng.integers(6, 23))
        orders = loader.sample_active_orders(
            n=order_count,
            origin_warehouse=wh_node,
            random_seed=int(rng.integers(1, 1000000))
        )

        # Varied capacity constraints to test real bottleneck conditions
        air_cap = int(rng.choice([60, 90, 120, 160, 200]))
        wh_cap = int(rng.choice([150, 200, 280, 350]))
        
        # In 20% of scenarios, inject a tight budget constraint to stress test feasibility
        has_budget = bool(rng.random() < 0.20)
        total_order_val = sum(o.total_value for o in orders)
        budget = round(total_order_val * 0.45, 2) if has_budget else None

        constraints = OptimizationConstraints(
            max_budget=budget,
            max_air_freight_units=air_cap,
            warehouse_divert_capacities={
                "Midwest_Hub_Chicago": wh_cap,
                "EastCoast_Hub_NJ": int(wh_cap * 0.8),
                "South_Hub_Dallas": int(wh_cap * 0.8),
                "Europe_Hub_Rotterdam": int(wh_cap * 0.5)
            },
            alternate_supplier_capacities={
                "Supplier_Alpha_Domestic": int(wh_cap * 0.4),
                "Supplier_Beta_Regional": int(wh_cap * 0.3)
            }
        )

        scenarios.append({
            "scenario_id": scen_id,
            "disruption_event": event,
            "affected_orders": orders,
            "constraints": constraints
        })

    return scenarios
