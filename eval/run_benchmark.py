"""Empirical Comparative Benchmark Harness for Indian E-Commerce Logistics.

Runs N=200 randomized scenarios comparing 4 strategies:
1. Blind Dispatch (Single default 3PL)
2. Heuristic Rule-Based
3. LLM-Only Planner (Simulated)
4. Agents + PuLP MILP Solver (Our System)

Outputs raw results to results/results.json and prints ASCII summary table.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eval.benchmark_scenarios import generate_benchmark_batches
from eval.baselines import (
    run_blind_dispatch,
    run_heuristic_greedy,
    run_llm_only,
    run_agents_and_solver
)


def run_full_benchmark(scenario_count: int = 200, batch_size: int = 15, seed: int = 42) -> Dict[str, Any]:
    """Execute comparative benchmark across all scenarios."""
    print(f"Generating {scenario_count} Indian e-commerce dispatch scenarios (batch size: {batch_size}, seed: {seed})...")
    scenarios = generate_benchmark_batches(scenario_count=scenario_count, batch_size=batch_size, seed=seed)

    strategies = [
        "Blind Dispatch",
        "Rule-based Greedy",
        "LLM-Only Planner",
        "Agents + MILP Solver (Ours)"
    ]

    aggregates = {
        strat: {
            "total_cost_inr": 0.0,
            "total_shipping_spend_inr": 0.0,
            "total_rto_loss_inr": 0.0,
            "parcels_dispatched": 0,
            "parcels_cancelled": 0,
            "upi_converted": 0,
            "feasible_count": 0,
            "total_latency_sec": 0.0,
            "scenario_runs": []
        }
        for strat in strategies
    }

    print(f"Executing comparative evaluations...")
    for idx, batch in enumerate(scenarios, 1):
        if idx % 20 == 0 or idx == scenario_count:
            print(f"  Processed {idx}/{scenario_count} scenarios...")

        # 1. Blind Dispatch
        res_blind = run_blind_dispatch(batch)
        aggregates["Blind Dispatch"]["total_cost_inr"] += res_blind["total_cost_inr"]
        aggregates["Blind Dispatch"]["total_shipping_spend_inr"] += res_blind["total_shipping_spend_inr"]
        aggregates["Blind Dispatch"]["total_rto_loss_inr"] += res_blind["total_rto_loss_inr"]
        aggregates["Blind Dispatch"]["parcels_dispatched"] += res_blind["parcels_dispatched"]
        aggregates["Blind Dispatch"]["feasible_count"] += (1 if res_blind["quota_feasible"] else 0)
        aggregates["Blind Dispatch"]["total_latency_sec"] += res_blind["latency_sec"]

        # 2. Rule-based Greedy
        res_greedy = run_heuristic_greedy(batch)
        aggregates["Rule-based Greedy"]["total_cost_inr"] += res_greedy["total_cost_inr"]
        aggregates["Rule-based Greedy"]["total_shipping_spend_inr"] += res_greedy["total_shipping_spend_inr"]
        aggregates["Rule-based Greedy"]["total_rto_loss_inr"] += res_greedy["total_rto_loss_inr"]
        aggregates["Rule-based Greedy"]["parcels_dispatched"] += res_greedy["parcels_dispatched"]
        aggregates["Rule-based Greedy"]["parcels_cancelled"] += res_greedy["parcels_cancelled"]
        aggregates["Rule-based Greedy"]["feasible_count"] += (1 if res_greedy["quota_feasible"] else 0)
        aggregates["Rule-based Greedy"]["total_latency_sec"] += res_greedy["latency_sec"]

        # 3. LLM-Only
        res_llm = run_llm_only(batch, seed=seed + idx)
        aggregates["LLM-Only Planner"]["total_cost_inr"] += res_llm["total_cost_inr"]
        aggregates["LLM-Only Planner"]["total_shipping_spend_inr"] += res_llm["total_shipping_spend_inr"]
        aggregates["LLM-Only Planner"]["total_rto_loss_inr"] += res_llm["total_rto_loss_inr"]
        aggregates["LLM-Only Planner"]["parcels_dispatched"] += res_llm["parcels_dispatched"]
        aggregates["LLM-Only Planner"]["feasible_count"] += (1 if res_llm["quota_feasible"] else 0)
        aggregates["LLM-Only Planner"]["total_latency_sec"] += res_llm["latency_sec"]

        # 4. Agents + Solver (Ours)
        res_ours = run_agents_and_solver(batch)
        aggregates["Agents + MILP Solver (Ours)"]["total_cost_inr"] += res_ours["total_cost_inr"]
        aggregates["Agents + MILP Solver (Ours)"]["total_shipping_spend_inr"] += res_ours["total_shipping_spend_inr"]
        aggregates["Agents + MILP Solver (Ours)"]["total_rto_loss_inr"] += res_ours["total_rto_loss_inr"]
        aggregates["Agents + MILP Solver (Ours)"]["parcels_dispatched"] += res_ours["parcels_dispatched"]
        aggregates["Agents + MILP Solver (Ours)"]["parcels_cancelled"] += res_ours["parcels_cancelled"]
        aggregates["Agents + MILP Solver (Ours)"]["upi_converted"] += res_ours["upi_converted"]
        aggregates["Agents + MILP Solver (Ours)"]["feasible_count"] += (1 if res_ours["quota_feasible"] else 0)
        aggregates["Agents + MILP Solver (Ours)"]["total_latency_sec"] += res_ours["latency_sec"]

    # Calculate summary metrics
    summary = {}
    blind_cost = aggregates["Blind Dispatch"]["total_cost_inr"]

    for strat, data in aggregates.items():
        total_c = round(data["total_cost_inr"], 2)
        shipping_c = round(data["total_shipping_spend_inr"], 2)
        rto_loss = round(data["total_rto_loss_inr"], 2)
        feas_pct = round((data["feasible_count"] / scenario_count) * 100.0, 1)
        mean_lat = round(data["total_latency_sec"] / scenario_count, 4)
        savings_pct = round(((blind_cost - total_c) / blind_cost) * 100.0, 1) if blind_cost > 0 else 0.0

        summary[strat] = {
            "total_cost_inr": total_c,
            "total_shipping_spend_inr": shipping_c,
            "total_rto_loss_inr": rto_loss,
            "cost_reduction_vs_blind_pct": savings_pct,
            "parcels_dispatched": data["parcels_dispatched"],
            "parcels_cancelled": data["parcels_cancelled"],
            "upi_converted": data["upi_converted"],
            "feasibility_rate_pct": feas_pct,
            "mean_latency_sec": mean_lat
        }

    # Save to results/results.json
    os.makedirs("results", exist_ok=True)
    out_path = os.path.join("results", "results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "scenario_count": scenario_count,
            "batch_size": batch_size,
            "seed": seed,
            "summary": summary
        }, f, indent=2)

    print(f"\nRaw results successfully saved to: {out_path}\n")

    # Print ASCII Table
    print("=" * 95)
    print(f"{'Strategy':<30} | {'Total Cost (INR)':<16} | {'RTO Loss (INR)':<14} | {'Feasibility':<12} | {'Latency':<8}")
    print("-" * 95)
    for strat, m in summary.items():
        print(
            f"{strat:<30} | "
            f"INR {m['total_cost_inr']:>12,.2f} | "
            f"INR {m['total_rto_loss_inr']:>10,.2f} | "
            f"{m['feasibility_rate_pct']:>10.1f}% | "
            f"{m['mean_latency_sec']:>6.4f}s"
        )
    print("=" * 95)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Indian e-commerce logistics comparative benchmark")
    parser.add_argument("--scenarios", type=int, default=200, help="Number of scenarios to simulate")
    parser.add_argument("--batch-size", type=int, default=15, help="Number of orders per batch")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    run_full_benchmark(scenario_count=args.scenarios, batch_size=args.batch_size, seed=args.seed)
