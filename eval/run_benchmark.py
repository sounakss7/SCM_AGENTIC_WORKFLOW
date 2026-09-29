import os
import sys
import json
import time
from typing import Dict, Any, List

# Ensure repository root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from eval.benchmark_scenarios import generate_benchmark_scenarios
from eval.baselines import (
    evaluate_do_nothing,
    evaluate_greedy,
    evaluate_llm_only,
    evaluate_agentic_solver
)

def run_evaluation_benchmark(num_scenarios: int = 200, seed: int = 42) -> Dict[str, Any]:
    """
    Executes the full evaluation harness comparing 4 strategies across N randomized disruption scenarios.
    Saves raw results to results/results.json.
    """
    print(f"\n" + "="*80)
    print(f"=== SCM DISRUPTION RESPONSE ENGINE: BENCHMARK HARNESS (N={num_scenarios}, Seed={seed}) ===")
    print(f"="*80)

    print(f"Generating {num_scenarios} randomized scenarios from DataCo dataset...")
    scenarios = generate_benchmark_scenarios(n=num_scenarios, seed=seed)
    print(f"Generated {len(scenarios)} scenarios successfully.")

    strategies = [
        ("Do Nothing", evaluate_do_nothing),
        ("Rule-based Greedy", evaluate_greedy),
        ("LLM-Only Planner", lambda s: evaluate_llm_only(s, seed=seed)),
        ("Agents + Solver (Ours)", evaluate_agentic_solver)
    ]

    all_scenario_results: List[Dict[str, Any]] = []
    strategy_aggregates: Dict[str, Dict[str, Any]] = {}

    for strat_name, _ in strategies:
        strategy_aggregates[strat_name] = {
            "total_cost": 0.0,
            "total_recovery_cost": 0.0,
            "total_penalty_cost": 0.0,
            "total_delay_days": 0.0,
            "total_service_level": 0.0,
            "feasible_count": 0,
            "total_llm_calls": 0,
            "total_latency_sec": 0.0
        }

    total_runs = num_scenarios * len(strategies)
    run_idx = 0
    start_benchmark_time = time.time()

    print("\nExecuting comparative evaluation across all strategies...")
    for s_idx, scenario in enumerate(scenarios):
        scen_record = {
            "scenario_id": scenario["scenario_id"],
            "disruption_type": scenario["disruption_event"].disruption_type.value,
            "location": scenario["disruption_event"].location,
            "orders_count": len(scenario["affected_orders"]),
            "strategies": {}
        }

        for strat_name, eval_fn in strategies:
            run_idx += 1
            res = eval_fn(scenario)
            scen_record["strategies"][strat_name] = res

            agg = strategy_aggregates[strat_name]
            agg["total_cost"] += res["total_cost"]
            agg["total_recovery_cost"] += res.get("recovery_cost", 0.0)
            agg["total_penalty_cost"] += res.get("penalty_cost", 0.0)
            agg["total_delay_days"] += res["avg_delay_days"]
            agg["total_service_level"] += res["service_level_pct"]
            agg["feasible_count"] += 1 if res["is_feasible"] else 0
            agg["total_llm_calls"] += res["llm_calls"]
            agg["total_latency_sec"] += res["latency_sec"]

        all_scenario_results.append(scen_record)
        
        if (s_idx + 1) % 25 == 0 or s_idx == num_scenarios - 1:
            pct = ((s_idx + 1) / num_scenarios) * 100
            print(f"  Progress: {s_idx + 1}/{num_scenarios} scenarios completed ({pct:.0f}%)...")

    benchmark_duration = round(time.time() - start_benchmark_time, 2)

    # Compute Final Summary Table Metrics
    summary_table = []
    for strat_name, _ in strategies:
        agg = strategy_aggregates[strat_name]
        avg_cost = agg["total_cost"] / num_scenarios
        avg_delay = agg["total_delay_days"] / num_scenarios
        avg_service = agg["total_service_level"] / num_scenarios
        feasibility_rate = (agg["feasible_count"] / num_scenarios) * 100.0
        avg_llm_calls = agg["total_llm_calls"] / num_scenarios
        avg_latency = agg["total_latency_sec"] / num_scenarios

        summary_table.append({
            "Strategy": strat_name,
            "Total Cost ($)": round(agg["total_cost"], 2),
            "Avg Cost / Scenario ($)": round(avg_cost, 2),
            "Avg Delay (Days)": round(avg_delay, 2),
            "Service Level (%)": round(avg_service, 2),
            "Plan Feasibility (%)": round(feasibility_rate, 2),
            "Avg LLM Calls": round(avg_llm_calls, 2),
            "Avg Latency (s)": round(avg_latency, 4)
        })

    results_payload = {
        "benchmark_metadata": {
            "num_scenarios": num_scenarios,
            "random_seed": seed,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_benchmark_duration_sec": benchmark_duration
        },
        "summary": summary_table,
        "scenarios": all_scenario_results
    }

    # Save to results/results.json
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))
    os.makedirs(results_dir, exist_ok=True)
    results_path = os.path.join(results_dir, "results.json")

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    print(f"\n" + "="*80)
    print(f"BENCHMARK RESULTS SUMMARY (Saved to {results_path})")
    print(f"="*80)
    
    # Print formatted markdown table
    print(generate_markdown_table(summary_table))
    print(f"\nCompleted in {benchmark_duration:.2f} seconds.\n")

    return results_payload


def generate_markdown_table(summary_table: List[Dict[str, Any]]) -> str:
    """Formats summary dictionary into GitHub-flavored markdown table."""
    headers = [
        "Strategy",
        "Total Cost ($)",
        "Avg Cost / Scenario ($)",
        "Avg Delay (Days)",
        "Service Level (%)",
        "Plan Feasibility (%)",
        "Avg LLM Calls",
        "Avg Latency (s)"
    ]
    
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join([":---"] + [":---:"] * (len(headers) - 1)) + " |"
    ]

    for row in summary_table:
        line = (
            f"| **{row['Strategy']}** "
            f"| ${row['Total Cost ($)']:,.2f} "
            f"| ${row['Avg Cost / Scenario ($)']:,.2f} "
            f"| {row['Avg Delay (Days)']:.2f}d "
            f"| {row['Service Level (%)']:.1f}% "
            f"| {row['Plan Feasibility (%)']:.1f}% "
            f"| {row['Avg LLM Calls']:.1f} "
            f"| {row['Avg Latency (s)']:.4f}s |"
        )
        lines.append(line)

    return "\n".join(lines)


if __name__ == "__main__":
    run_evaluation_benchmark(num_scenarios=200, seed=42)
