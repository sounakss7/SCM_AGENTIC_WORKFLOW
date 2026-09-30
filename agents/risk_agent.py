"""Risk Assessor Agent (Agent 2 in Resilience Workflow).

Uses Google Gemini 2.5 Flash for deep contextual reasoning on supply chain risk,
operational downtime, stockout liabilities, and SLA penalty exposure in INR (₹).
"""

import json
from typing import Dict, Any
from agents.state import DisruptionWorkflowState
from agents.llm_client import llm_router
from core.network import SKUS_DB


def risk_agent_node(state: DisruptionWorkflowState) -> DisruptionWorkflowState:
    """Assess disruption risk, projected delay impact, and penalty exposure using Gemini 2.5 Flash."""
    logs = state.get("agent_logs", [])
    model_records = state.get("model_records", [])

    if not state.get("disruption_detected"):
        return state

    disruption = state.get("disruption", {})
    nominal_plan = state.get("nominal_plan", {})
    sku_id = state.get("sku_id", "SKU_001")
    quantity = state.get("quantity", 100)

    sku_item = SKUS_DB.get(sku_id)
    if sku_item:
        sku_name = getattr(sku_item, "name", "Product SKU")
        unit_value_inr = getattr(sku_item, "unit_cost_inr", 100.0)
        penalty_per_day = getattr(sku_item, "delay_penalty_per_day_inr", 30.0)
    else:
        sku_name = "Product SKU"
        unit_value_inr = 100.0
        penalty_per_day = 30.0

    # Baseline mathematical exposure if unattended
    delay_impact_days = disruption.get("delay_days", 3.0)
    unattended_penalty_inr = round(quantity * penalty_per_day * delay_impact_days, 2)
    inventory_exposure_inr = round(quantity * unit_value_inr, 2)

    # Prompt for Gemini 2.5 Flash
    prompt = f"""
You are the Senior Risk Assessor Agent for an Indian Supply Chain Control Tower.
Evaluate the operational and financial risk of the following disruption:

Order Details:
- Order ID: {state.get('order_id')}
- SKU: {sku_name} ({sku_id})
- Shipment Volume: {quantity} units (Total Inventory Value: ₹{inventory_exposure_inr:,.2f})
- Baseline Route: {nominal_plan.get('supplier')} -> {nominal_plan.get('port', 'DIRECT')} -> {nominal_plan.get('warehouse')} -> {nominal_plan.get('retailer')}
- Carrier: {nominal_plan.get('carrier')}

Disruption Detected:
- Type: {disruption.get('disruption_type')}
- Description: {disruption.get('description')}
- Unmitigated Delay: {delay_impact_days} days
- Projected Penalty if unmitigated: ₹{unattended_penalty_inr:,.2f}

Provide an analytical risk evaluation containing:
1. Operational Severity (LOW, MEDIUM, HIGH, or CRITICAL)
2. Risk Score (0.0 to 10.0)
3. Concise risk rationale emphasizing Indian road/port conditions and SLA liability.
Output valid JSON:
{{"severity": "HIGH", "risk_score": 8.5, "rationale": "..."}}
"""

    mock_fallback = json.dumps({
        "severity": disruption.get("severity", "HIGH"),
        "risk_score": 8.2 if disruption.get("severity") in ["HIGH", "CRITICAL"] else 5.4,
        "rationale": f"Unmitigated disruption on {nominal_plan.get('carrier')} causes {delay_impact_days} days transit stall, risking ₹{unattended_penalty_inr:,.2f} in SLA delay penalties and retail stockout for {sku_name}."
    })

    # Call Gemini 2.5 Flash
    response_text, record = llm_router.call_gemini_reasoning(
        agent_name="Risk Assessor Agent",
        prompt=prompt,
        mock_fallback=mock_fallback
    )

    # Parse response
    try:
        # Clean potential markdown fences
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        parsed = json.loads(clean_text.strip())
    except Exception:
        parsed = {
            "severity": disruption.get("severity", "HIGH"),
            "risk_score": 8.0,
            "rationale": f"Delay exposure of {delay_impact_days} days incurs ₹{unattended_penalty_inr:,.2f} liability."
        }

    risk_data = {
        "severity": parsed.get("severity", "HIGH"),
        "risk_score": float(parsed.get("risk_score", 8.0)),
        "rationale": parsed.get("rationale", ""),
        "unattended_penalty_inr": unattended_penalty_inr,
        "unattended_delay_days": delay_impact_days,
        "inventory_exposure_inr": inventory_exposure_inr
    }

    logs.append({
        "agent": "Risk Assessor Agent",
        "action": "Risk Evaluated (Gemini 2.5 Flash)",
        "message": f"Assessed Severity: {risk_data['severity']} (Score: {risk_data['risk_score']}/10). SLA Exposure: ₹{unattended_penalty_inr:,.2f}.",
        "status": "SUCCESS"
    })
    model_records.append(record.model_dump())

    return {
        "risk_assessment": risk_data,
        "status": "RISK_EVALUATED",
        "agent_logs": logs,
        "model_records": model_records
    }
