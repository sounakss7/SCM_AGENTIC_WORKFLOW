"""100-Scenario Disruption Benchmark Harness for Indian Supply Chain Resilience.

Compares:
(A) No Re-planning (Static Disrupted Route - unmitigated carrier stalls, port dwelling, SLA penalties)
(B) 5-Agent Resilience System (Automated LangGraph workflow with deterministic OR core)

Outputs complete factual metrics to results/results.json with seed=42 for strict reproducibility.
"""

import os
import sys
import json
import random
import time
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.network import get_default_indian_network, IndianLogisticsNetwork, SKUItem
from core.disruptions import (
    DisruptionEvent, DisruptionType, SeverityLevel, get_predefined_disruptions
)
from optimizer.resilience_solver import evaluate_end_to_end_route, find_optimal_alternate_route
from agents.workflow import run_resilience_workflow


def run_100_scenario_benchmark(seed: int = 42, output_file: str = "results/results.json") -> Dict[str, Any]:
    """Run 100 synthetic disruption scenarios and measure performance deltas."""
    random.seed(seed)
    network = get_default_indian_network()

    suppliers = [s.node_id for s in network.suppliers]
    retailers = [r.node_id for r in network.retailers]
    skus = network.skus

    # Base disruption templates
    disruption_catalog = [
        {"type": DisruptionType.CARRIER_FAILURE, "target_type": "CARRIER", "target_id": "SAFEXPRESS", "delay": 5.0, "surcharge": 60.0, "cap_cut": 100.0, "desc": "Safexpress national transporter strike; all depots locked down."},
        {"type": DisruptionType.PORT_CONGESTION, "target_type": "PORT", "target_id": "PORT_JNPT", "delay": 3.5, "surcharge": 40.0, "cap_cut": 70.0, "desc": "Berth congestion and customs server outage at Nhava Sheva (JNPT)."},
        {"type": DisruptionType.CARRIER_FAILURE, "target_type": "CARRIER", "target_id": "DELHIVERY", "delay": 4.0, "surcharge": 45.0, "cap_cut": 90.0, "desc": "Delhivery fleet breakdown on Western Golden Quadrilateral corridor."},
        {"type": DisruptionType.PORT_CONGESTION, "target_type": "PORT", "target_id": "PORT_MUNDRA", "delay": 3.0, "surcharge": 35.0, "cap_cut": 65.0, "desc": "Severe monsoon cyclone warnings and vessel queueing at Mundra Port."},
        {"type": DisruptionType.ROUTE_CLOSURE, "target_type": "LINK", "target_id": "L_JNPT_DEL", "delay": 4.5, "surcharge": 50.0, "cap_cut": 85.0, "desc": "Flooding on NH-48 Delhi-Mumbai expressway section near Surat/Bharuch."},
        {"type": DisruptionType.CARRIER_FAILURE, "target_type": "CARRIER", "target_id": "TCI_EXPRESS", "delay": 3.5, "surcharge": 30.0, "cap_cut": 80.0, "desc": "TCI Express multimodal rail-rake allocation shortage in Northern zone."},
    ]

    scenarios_data: List[Dict[str, Any]] = []

    total_cost_saved_inr = 0.0
    total_delay_days_saved = 0.0
    successful_remediations = 0

    gemini_calls_total = 0
    groq_calls_total = 0
    gemini_latency_sum = 0.0
    groq_latency_sum = 0.0

    print(f"Starting 100-scenario resilience benchmark (seed={seed})...")
    start_time = time.perf_counter()

    for idx in range(1, 101):
        order_id = f"SCENARIO-{idx:03d}"
        supplier = random.choice(suppliers)
        retailer = random.choice(retailers)
        sku = random.choice(skus)
        quantity = random.choice([50, 75, 100, 150, 200, 250])

        template = random.choice(disruption_catalog)
        disruption_obj = DisruptionEvent(
            event_id=f"DIS-{idx:03d}",
            disruption_type=template["type"],
            target_type=template["target_type"],
            target_id=template["target_id"],
            severity=SeverityLevel.HIGH if template["delay"] < 4.5 else SeverityLevel.CRITICAL,
            delay_days_added=template["delay"],
            cost_surcharge_pct=template["surcharge"],
            capacity_reduction_pct=template["cap_cut"],
            description=template["desc"]
        )

        # 1. Baseline: calculate nominal optimal route WITHOUT disruption
        nominal_plan, _ = find_optimal_alternate_route(
            network=network,
            supplier_id=supplier,
            retailer_id=retailer,
            sku=sku,
            quantity=quantity,
            disruption=None
        )

        if not nominal_plan:
            continue

        # Baseline unattended: what happens if we stay on nominal plan under this disruption?
        disrupted_baseline_plan = evaluate_end_to_end_route(
            network=network,
            supplier_id=supplier,
            port_id=nominal_plan.port_id,
            warehouse_id=nominal_plan.warehouse_id,
            retailer_id=retailer,
            carrier_assignments={},
            sku=sku,
            quantity=quantity,
            disruption=disruption_obj,
            max_allowed_delay_days=15.0
        )

        unattended_cost_inr = disrupted_baseline_plan.total_cost_inr
        unattended_transit_days = disrupted_baseline_plan.total_transit_days

        # If baseline plan became completely halted/infeasible, delay blows out
        if not disrupted_baseline_plan.is_feasible:
            unattended_transit_days = nominal_plan.total_transit_days + disruption_obj.delay_days_added + 4.0
            unattended_cost_inr = (
                nominal_plan.freight_cost_inr * (1.0 + disruption_obj.cost_surcharge_pct / 100.0) +
                nominal_plan.handling_cost_inr +
                (unattended_transit_days - nominal_plan.total_transit_days) * sku.delay_penalty_per_day_inr * quantity
            )

        # 2. Run 5-Agent Resilience Workflow
        workflow_res = run_resilience_workflow(
            order_id=order_id,
            sku_id=sku.sku_id,
            quantity=quantity,
            source_supplier=supplier,
            target_retailer=retailer,
            disruption=disruption_obj.to_dict(),
            nominal_plan=nominal_plan.to_dict()
        )

        final_plan = workflow_res.get("final_plan")
        is_remediated = (workflow_res.get("status") in ["COMPLETED", "VALIDATED", "NOMINAL"]) and (final_plan is not None)

        if is_remediated:
            remediated_cost_inr = final_plan.get("total_cost_inr", unattended_cost_inr)
            remediated_transit_days = final_plan.get("total_transit_days", unattended_transit_days)
            cost_saved_inr = max(0.0, unattended_cost_inr - remediated_cost_inr)
            delay_saved_days = max(0.0, unattended_transit_days - remediated_transit_days)
            successful_remediations += 1
        else:
            remediated_cost_inr = unattended_cost_inr
            remediated_transit_days = unattended_transit_days
            cost_saved_inr = 0.0
            delay_saved_days = 0.0

        total_cost_saved_inr += cost_saved_inr
        total_delay_days_saved += delay_saved_days

        # Aggregate model telemetry
        for rec in workflow_res.get("model_records", []):
            if "Gemini" in rec["target_provider"]:
                gemini_calls_total += 1
                gemini_latency_sum += rec["latency_sec"]
            elif "Groq" in rec["target_provider"]:
                groq_calls_total += 1
                groq_latency_sum += rec["latency_sec"]

        scenarios_data.append({
            "scenario_id": idx,
            "order_id": order_id,
            "sku_id": sku.sku_id,
            "sku_name": sku.name,
            "quantity": quantity,
            "supplier": supplier,
            "retailer": retailer,
            "disruption_type": disruption_obj.disruption_type.value,
            "disruption_target": disruption_obj.target_id,
            "unattended_cost_inr": round(unattended_cost_inr, 2),
            "unattended_transit_days": round(unattended_transit_days, 2),
            "remediated_cost_inr": round(remediated_cost_inr, 2),
            "remediated_transit_days": round(remediated_transit_days, 2),
            "cost_saved_inr": round(cost_saved_inr, 2),
            "delay_saved_days": round(delay_saved_days, 2),
            "reassigned_carrier": final_plan.get("carrier") if final_plan else "NONE",
            "is_successful": is_remediated,
            "agent_steps": len(workflow_res.get("agent_logs", []))
        })

    elapsed_total = round(time.perf_counter() - start_time, 2)

    summary = {
        "benchmark_metadata": {
            "total_scenarios": 100,
            "random_seed": seed,
            "currency": "INR (₹)",
            "network_nodes": {
                "suppliers": 3,
                "ports": 3,
                "warehouses": 3,
                "retailers": 4,
                "carriers": 4,
                "skus": len(skus)
            },
            "elapsed_seconds": elapsed_total
        },
        "resilience_performance": {
            "resolution_success_rate_pct": round((successful_remediations / 100) * 100, 1),
            "total_cost_saved_inr": round(total_cost_saved_inr, 2),
            "avg_cost_saved_per_order_inr": round(total_cost_saved_inr / 100, 2),
            "total_delay_days_avoided": round(total_delay_days_saved, 1),
            "avg_delay_days_avoided_per_order": round(total_delay_days_saved / 100, 2),
            "avg_agent_steps_per_incident": round(sum(s["agent_steps"] for s in scenarios_data) / 100, 1)
        },
        "model_routing_telemetry": {
            "gemini_reasoning_calls": gemini_calls_total,
            "groq_validator_calls": groq_calls_total,
            "avg_gemini_latency_ms": round((gemini_latency_sum / max(1, gemini_calls_total)) * 1000, 1),
            "avg_groq_latency_ms": round((groq_latency_sum / max(1, groq_calls_total)) * 1000, 1)
        },
        "scenarios": scenarios_data
    }

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Benchmark completed successfully in {elapsed_total}s.")
    print(f"Success Rate: {summary['resilience_performance']['resolution_success_rate_pct']}%")
    print(f"Total Cost Saved: INR {summary['resilience_performance']['total_cost_saved_inr']:,.2f}")
    print(f"Avg Cost Saved / Order: INR {summary['resilience_performance']['avg_cost_saved_per_order_inr']:,.2f}")
    print(f"Avg Delay Avoided: {summary['resilience_performance']['avg_delay_days_avoided_per_order']} days")
    print(f"Gemini Calls: {gemini_calls_total} | Groq Calls: {groq_calls_total}")
    print(f"Saved results to: {output_file}")

    return summary


if __name__ == "__main__":
    run_100_scenario_benchmark()
