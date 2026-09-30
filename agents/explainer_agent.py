"""Explainer Agent (Agent 5 in Resilience Workflow).

Uses Google Gemini 2.5 Flash to synthesize an executive supply chain briefing in INR (₹).
Strict Guarantee: Does NOT compute or mutate numbers. Strictly presents the deterministic
solver's audited costs and transit milestones.
"""

from typing import Dict, Any
from agents.state import DisruptionWorkflowState
from agents.llm_client import llm_router
from core.network import CARRIERS_DB, WAREHOUSES_DB, SKUS_DB


def explainer_agent_node(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    """Generate executive summary using Gemini 2.5 Flash explaining the resilience decision in ₹."""
    logs = state.get("agent_logs", [])
    model_records = state.get("model_records", [])

    if not state.get("disruption_detected"):
        state["explanation"] = "Shipment proceeding on nominal schedule. No disruption detected."
        return state

    final_plan = state.get("final_plan")
    nominal_plan = state.get("nominal_plan", {})
    disruption = state.get("disruption", {})
    risk = state.get("risk_assessment", {})
    sku_id = state.get("sku_id", "SKU_01")
    sku_item = SKUS_DB.get(sku_id)
    sku_name = getattr(sku_item, "name", "Product") if sku_item else "Product"
    quantity = state.get("quantity", 100)

    if not final_plan or state.get("status") == "FAILED":
        explanation = (
            f"ALERT: Severe network disruption ({disruption.get('description')}). "
            f"All alternate route combinations breached SLA limits or carrier capacity. "
            f"Immediate human operator intervention required."
        )
        state["explanation"] = explanation
        logs.append({
            "agent": "Explainer Agent",
            "action": "Alert Summary Generated",
            "message": "Generated critical exception report for logistics director.",
            "status": "ALERT"
        })
        return state

    # Audited numbers (must be preserved verbatim)
    nominal_cost = nominal_plan.get("total_cost_inr", 0.0)
    final_cost = final_plan.get("total_cost_inr", 0.0)
    cost_delta = round(final_cost - nominal_cost, 2)
    nominal_transit = nominal_plan.get("total_transit_days", 0.0)
    final_transit = final_plan.get("total_transit_days", 0.0)
    transit_delta = round(final_transit - nominal_transit, 2)
    unattended_penalty = risk.get("unattended_penalty_inr", 0.0)
    unattended_delay = risk.get("unattended_delay_days", 0.0)
    carrier_item = CARRIERS_DB.get(final_plan.get("carrier"))
    carrier_name = getattr(carrier_item, "name", final_plan.get("carrier")) if carrier_item else final_plan.get("carrier")

    prompt = f"""
You are the Lead Logistics Explainer Agent for an Indian Supply Chain Control Tower.
Synthesize an executive disruption summary using the following audited numbers.
IMPORTANT: You MUST NOT change, recalculate, or alter any numbers. Present them verbatim.

Disruption Event:
- Description: {disruption.get('description')}
- Unattended Delay Risk: {unattended_delay} days
- Averted SLA Penalty Exposure: ₹{unattended_penalty:,.2f}

Mitigation Decision:
- Order: {quantity} units of {sku_name}
- Re-routed Path: {final_plan.get('supplier')} -> {final_plan.get('port', 'DIRECT')} -> {final_plan.get('warehouse')} -> {final_plan.get('retailer')}
- Carrier Switched To: {carrier_name} ({final_plan.get('carrier')})
- Baseline Landed Cost: ₹{nominal_cost:,.2f}
- Re-routed Landed Cost: ₹{final_cost:,.2f} (Delta: ₹{cost_delta:+,.2f})
- Re-routed Transit Time: {final_transit} days (Transit Delta: {transit_delta:+} days)

Write a 3-point bulleted briefing for the Chief Supply Chain Officer:
1. Incident & Exposure
2. Self-Correction Action
3. Financial & SLA Impact
"""

    mock_fallback = (
        f"**Executive Disruption Briefing**:\n"
        f"1. **Incident & Exposure**: {disruption.get('description')} threatened a {unattended_delay}-day delivery stoppage, exposing ₹{unattended_penalty:,.2f} in SLA late fees.\n"
        f"2. **Self-Correction Action**: Re-routed {quantity} units of {sku_name} via {carrier_name} through {final_plan.get('warehouse')}.\n"
        f"3. **Financial & SLA Impact**: Alternate landed cost settled at ₹{final_cost:,.2f} (Delta: ₹{cost_delta:+,.2f}) with arrival in {final_transit} days, saving ₹{unattended_penalty:,.2f} in stockout penalties."
    )

    response_text, record = llm_router.call_gemini_reasoning(
        agent_name="Explainer Agent",
        prompt=prompt,
        mock_fallback=mock_fallback
    )

    logs.append({
        "agent": "Explainer Agent",
        "action": "Briefing Synthesized (Gemini 2.5 Flash)",
        "message": f"Generated executive briefing preserving audited ₹{final_cost:,.2f} landed cost and ₹{cost_delta:+,.2f} delta.",
        "status": "SUCCESS"
    })
    model_records.append(record.model_dump())

    return {
        "explanation": response_text,
        "status": "COMPLETED",
        "final_plan": final_plan,
        "agent_logs": logs,
        "model_records": model_records
    }
