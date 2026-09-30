"""Validator Agent (Agent 4 in Resilience Workflow).

Uses Groq (Llama 3.3 70B / 8B) for ultra-low latency plan validation,
cross-checking physical node capacity, carrier vehicle limits, and delivery SLA windows.
Triggers a self-correcting re-routing loop if constraints are breached.
"""

import json
from typing import Dict, Any, List
from agents.state import DisruptionWorkflowState
from agents.llm_client import llm_router
from core.network import WAREHOUSES_DB, CARRIERS_DB


def validator_agent_node(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    """Validate proposed recovery plan using Groq for low-latency verification."""
    logs = state.get("agent_logs", [])
    model_records = state.get("model_records", [])

    if not state.get("disruption_detected"):
        return state

    proposed_plan = state.get("proposed_plan")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if not proposed_plan:
        logs.append({
            "agent": "Validator Agent",
            "action": "Rejected",
            "message": "No proposed plan received to validate. Re-route failed.",
            "status": "FAILED"
        })
        return {
            "validation_result": {"is_valid": False, "violations": ["No plan proposed"]},
            "status": "FAILED",
            "agent_logs": logs,
            "model_records": model_records
        }

    carrier_id = proposed_plan.get("carrier")
    warehouse_id = proposed_plan.get("warehouse")
    transit_days = proposed_plan.get("total_transit_days", 0.0)
    quantity = state.get("quantity", 100)

    # Hard physical checks
    violations: List[str] = []

    # 1. Carrier check
    carrier_info = CARRIERS_DB.get(carrier_id)
    if not carrier_info:
        violations.append(f"Carrier '{carrier_id}' is not in certified network registry.")
    else:
        carrier_cap = getattr(carrier_info, "daily_capacity_units", getattr(carrier_info, "capacity_per_day_units", 500))
        carrier_name = getattr(carrier_info, "name", carrier_id)
        if quantity > carrier_cap:
            violations.append(
                f"Quantity ({quantity}) exceeds carrier {carrier_name} daily vehicle allocation ({carrier_cap})."
            )

    # 2. Warehouse check
    warehouse_info = WAREHOUSES_DB.get(warehouse_id)
    if not warehouse_info:
        violations.append(f"Warehouse '{warehouse_id}' not found.")
    else:
        wh_cap = getattr(warehouse_info, "capacity_units", 10000)
        wh_name = getattr(warehouse_info, "name", warehouse_id)
        if quantity > wh_cap:
            violations.append(
                f"Quantity ({quantity}) exceeds warehouse {wh_name} max buffer ({wh_cap})."
            )

    # 3. SLA Max Lead Time (e.g. 7.5 days max threshold)
    MAX_SLA_DAYS = 7.5
    if transit_days > MAX_SLA_DAYS:
        violations.append(
            f"Total transit duration {transit_days} days exceeds Indian retail SLA ceiling ({MAX_SLA_DAYS} days)."
        )

    # Formulate validation prompt for Groq
    prompt = f"""
[Groq Low-Latency Validator]
Inspect proposed supply chain route plan:
- Carrier: {carrier_id}
- Warehouse: {warehouse_id}
- Order Quantity: {quantity}
- Total Transit: {transit_days} days
- Physical Violation Flags: {json.dumps(violations)}

Determine if plan is APPROVED or REJECTED.
Respond in valid JSON:
{{"is_valid": true/false, "verdict": "APPROVED/REJECTED", "comments": "..."}}
"""

    mock_fallback = json.dumps({
        "is_valid": len(violations) == 0,
        "verdict": "APPROVED" if len(violations) == 0 else "REJECTED",
        "comments": "All capacity and SLA requirements satisfied." if len(violations) == 0 else " | ".join(violations)
    })

    # Call Groq for fast validation
    response_text, record = llm_router.call_groq_fast_validator(
        agent_name="Validator Agent",
        prompt=prompt,
        mock_fallback=mock_fallback
    )

    try:
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        parsed = json.loads(clean_text.strip())
        llm_valid = bool(parsed.get("is_valid", len(violations) == 0))
    except Exception:
        llm_valid = (len(violations) == 0)

    # Deterministic safety rule: if physical violations exist, it MUST be rejected
    is_valid = llm_valid and (len(violations) == 0)

    model_records.append(record.model_dump())

    if is_valid:
        logs.append({
            "agent": "Validator Agent",
            "action": "Plan Approved (Groq Low-Latency)",
            "message": f"Verified feasible via {record.model_name} in {record.latency_sec * 1000:.1f}ms. Capacity and SLA satisfied.",
            "status": "APPROVED"
        })
        return {
            "validation_result": {
                "is_valid": True,
                "violations": [],
                "attempts": retry_count + 1
            },
            "final_plan": proposed_plan,
            "status": "VALIDATED",
            "agent_logs": logs,
            "model_records": model_records
        }
    else:
        new_retry = retry_count + 1
        will_retry = new_retry < max_retries
        logs.append({
            "agent": "Validator Agent",
            "action": f"Plan Rejected (Attempt {new_retry}/{max_retries})",
            "message": f"Violations: {'; '.join(violations)}. {'Triggering solver retry.' if will_retry else 'Exceeded max retries.'}",
            "status": "RETRY" if will_retry else "FAILED"
        })
        return {
            "validation_result": {
                "is_valid": False,
                "violations": violations,
                "attempts": new_retry
            },
            "retry_count": new_retry,
            "status": "RETRYING" if will_retry else "FAILED",
            "agent_logs": logs,
            "model_records": model_records
        }
