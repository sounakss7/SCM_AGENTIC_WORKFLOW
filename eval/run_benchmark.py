"""Evaluation Harness: Executes N=200 randomized multi-echelon scenarios across 4 policies.

Saves raw results to results/results.json and prints a clean ASCII summary table.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.network import get_default_network
from eval.benchmark_scenarios import generate_200_scenarios
from eval.baselines import (
    run_static_reorder_point,
    run_greedy_single_echelon,
    run_llm_only,
    run_agent_optimizer_system
)


def run_multi_echelon_benchmark(scenario_count: int = 200, seed: int = 42) -> Dict[str, Any]:
    """Execute comparative evaluation of the 4 multi-echelon policies."""
    print(f"Generating {scenario_count} multi-echelon scenarios (seed={seed})...")
    scenarios = generate_200_scenarios(seed=seed)[:scenario_count]
    network = get_default_network()

    policies = [
        "Static Reorder-Point (s,S)",
        "Greedy Single-Echelon",
        "LLM-Only (No Optimizer)",
        "Agents + MILP Solver (Ours)"
    ]

    aggregates = {
        p: {
            "total_cost": 0.0,
            "service_level_sum": 0.0,
            "stockout_rate_sum": 0.0,
            "feasible_count": 0,
            "negotiation_rounds_sum": 0,
            "total_latency_sec": 0.0,
            "total_llm_calls": 0,
            "scenario_runs": []
        }
        for p in policies
    }

    print(f"Running comparative benchmark across {scenario_count} scenarios...")
    for idx, scn in enumerate(scenarios, 1):
        if idx % 25 == 0 or idx == scenario_count:
            print(f"  Completed {idx}/{scenario_count} scenarios...")

        demand = scn["demand"]
        disruption = scn["disruption"]

        # 1. Static Reorder-Point
        res_static = run_static_reorder_point(network, demand, disruption)
        aggregates["Static Reorder-Point (s,S)"]["total_cost"] += res_static["total_cost"]
        aggregates["Static Reorder-Point (s,S)"]["service_level_sum"] += res_static["service_level_pct"]
        aggregates["Static Reorder-Point (s,S)"]["stockout_rate_sum"] += res_static["stockout_rate_pct"]
        aggregates["Static Reorder-Point (s,S)"]["feasible_count"] += (1 if res_static["plan_feasibility_rate_pct"] > 50 else 0)
        aggregates["Static Reorder-Point (s,S)"]["total_latency_sec"] += res_static["latency_sec"]

        # 2. Greedy Single-Echelon
        res_greedy = run_greedy_single_echelon(network, demand, disruption)
        aggregates["Greedy Single-Echelon"]["total_cost"] += res_greedy["total_cost"]
        aggregates["Greedy Single-Echelon"]["service_level_sum"] += res_greedy["service_level_pct"]
        aggregates["Greedy Single-Echelon"]["stockout_rate_sum"] += res_greedy["stockout_rate_pct"]
        aggregates["Greedy Single-Echelon"]["feasible_count"] += (1 if res_greedy["plan_feasibility_rate_pct"] > 50 else 0)
        aggregates["Greedy Single-Echelon"]["total_latency_sec"] += res_greedy["latency_sec"]

        # 3. LLM-Only
        res_llm = run_llm_only(network, demand, disruption, seed=seed + idx)
        aggregates["LLM-Only (No Optimizer)"]["total_cost"] += res_llm["total_cost"]
        aggregates["LLM-Only (No Optimizer)"]["service_level_sum"] += res_llm["service_level_pct"]
        aggregates["LLM-Only (No Optimizer)"]["stockout_rate_sum"] += res_llm["stockout_rate_pct"]
        aggregates["LLM-Only (No Optimizer)"]["feasible_count"] += (1 if res_llm["plan_feasibility_rate_pct"] > 50 else 0)
        aggregates["LLM-Only (No Optimizer)"]["negotiation_rounds_sum"] += res_llm["negotiation_rounds"]
        aggregates["LLM-Only (No Optimizer)"]["total_latency_sec"] += res_llm["latency_sec"]
        aggregates["LLM-Only (No Optimizer)"]["total_llm_calls"] += res_llm["llm_calls"]

        # 4. Agents + Solver (Ours)
        res_ours = run_agent_optimizer_system(network, demand, disruption)
        aggregates["Agents + MILP Solver (Ours)"]["total_cost"] += res_ours["total_cost"]
        aggregates["Agents + MILP Solver (Ours)"]["service_level_sum"] += res_ours["service_level_pct"]
        aggregates["Agents + MILP Solver (Ours)"]["stockout_rate_sum"] += res_ours["stockout_rate_pct"]
        aggregates["Agents + MILP Solver (Ours)"]["feasible_count"] += (1 if res_ours["plan_feasibility_rate_pct"] > 50 else 0)
        aggregates["Agents + MILP Solver (Ours)"]["negotiation_rounds_sum"] += res_ours["negotiation_rounds"]
        aggregates["Agents + MILP Solver (Ours)"]["total_latency_sec"] += res_ours["latency_sec"]
        aggregates["Agents + MILP Solver (Ours)"]["total_llm_calls"] += res_ours["llm_calls"]

    summary = {}
    N = float(scenario_count)

    for p, data in aggregates.items():
        summary[p] = {
            "mean_total_cost_usd": round(data["total_cost"] / N, 2),
            "mean_service_level_pct": round(data["service_level_sum"] / N, 2),
            "mean_stockout_rate_pct": round(data["stockout_rate_sum"] / N, 2),
            "plan_feasibility_rate_pct": round((data["feasible_count"] / N) * 100.0, 1),
            "mean_negotiation_rounds": round(data["negotiation_rounds_sum"] / N, 1),
            "mean_latency_sec": round(data["total_latency_sec"] / N, 4),
            "mean_llm_calls_per_scenario": round(data["total_llm_calls"] / N, 1)
        }

    # Save to results/results.json
    os.makedirs("results", exist_ok=True)
    out_path = os.path.join("results", "results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "scenario_count": scenario_count,
            "seed": seed,
            "summary": summary
        }, f, indent=2)

    print(f"\nRaw results successfully saved to: {out_path}\n")

    # Print ASCII table
    print("=" * 110)
    print(f"{'Policy':<30} | {'Total Cost ($)':<15} | {'Service Level':<14} | {'Stockout Rate':<14} | {'Feasibility':<12} | {'Latency':<8}")
    print("-" * 110)
    for p, m in summary.items():
        print(
            f"{p:<30} | "
            f"${m['mean_total_cost_usd']:>13,.2f} | "
            f"{m['mean_service_level_pct']:>12.1f}% | "
            f"{m['mean_stockout_rate_pct']:>12.1f}% | "
            f"{m['plan_feasibility_rate_pct']:>10.1f}% | "
            f"{m['mean_latency_sec']:>6.4f}s"
        )
    print("=" * 110)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Echelon Supply Chain Benchmark")
    parser.add_argument("--scenarios", type=int, default=200, help="Number of scenarios")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    run_multi_echelon_benchmark(scenario_count=args.scenarios, seed=args.seed)
