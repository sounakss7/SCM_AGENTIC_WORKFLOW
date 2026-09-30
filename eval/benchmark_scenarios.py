"""Generates 200 reproducible Indian e-commerce dispatch scenarios for empirical benchmarking."""

from typing import List
from core.schema import OrderRecord
from core.data_loader import generate_indian_orders


def generate_benchmark_batches(scenario_count: int = 200, batch_size: int = 15, seed: int = 42) -> List[List[OrderRecord]]:
    """Generate scenario_count batches of Indian e-commerce orders deterministically."""
    batches: List[List[OrderRecord]] = []
    for s_idx in range(scenario_count):
        batch = generate_indian_orders(count=batch_size, seed=seed + s_idx * 17)
        # Unique IDs per scenario
        for o in batch:
            o.order_id = f"SCN{s_idx:03d}-{o.order_id}"
        batches.append(batch)
    return batches
