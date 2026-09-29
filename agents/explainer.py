import os
from typing import Dict, Any, Optional
from core.config import settings
from core.database import log_audit_entry
from agents.state import DisruptionState

def get_llm_instance():
    """Retrieves an active Chat model (Gemini 2.5 Flash or Groq Llama 3.3) with fallback."""
    if settings.ROUTING_PREFERENCE == "gemini" and settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1
            ), "Gemini 2.5 Flash"
        except Exception:
            pass

    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=settings.GROQ_API_KEY,
                temperature=0.1
            ), "Groq Llama 3.3"
        except Exception:
            pass

    if settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.1
            ), "Gemini 2.5 Flash"
        except Exception:
            pass

    return None, "Deterministic Fallback Explainer"


def explainer_node(state: DisruptionState) -> Dict[str, Any]:
    """
    Explainer Agent:
    The LLM writes the plain-English rationale from the solver's output ONLY.
    The LLM does NOT do arithmetic or calculate costs; it translates the mathematical
    trade-offs of the MILP solution into an executive briefing for logistics managers.
    """
    plan = state.get("optimized_plan")
    event = state["disruption_event"]
    scenario_id = state["scenario_id"]
    risk = state.get("risk_assessment")
    orders = state.get("affected_orders", [])
    llm_calls = state.get("llm_call_count", 0)

    if not plan or not plan.is_feasible:
        explanation = (
            f"The optimization engine was unable to formulate a feasible recovery plan under the given capacity limits. "
            f"Manual intervention by logistics dispatchers is required to renegotiate carrier allotments."
        )
        return {"explanation": explanation}

    # Extract exact metrics computed by the solver
    total_orders = len(orders)
    on_time = plan.orders_on_time
    service_level = plan.service_level_pct
    recovery_cost = plan.total_recovery_cost
    penalty_cost = plan.total_penalty_cost
    combined_cost = plan.total_combined_cost
    base_exposure = risk.base_penalty_exposure if risk else (penalty_cost * 2.5)
    net_savings = max(0.0, base_exposure - combined_cost)
    air_units = plan.capacity_utilization.get("air_freight_used_units", 0)
    wh_units = plan.capacity_utilization.get("warehouse_diverted_units", 0)

    # Action counts
    action_counts = {}
    for a in plan.allocations:
        action_counts[a.selected_action.value] = action_counts.get(a.selected_action.value, 0) + 1

    actions_summary = ", ".join(f"{cnt} via {act}" for act, cnt in action_counts.items())

    llm, model_name = get_llm_instance()
    
    if llm is not None:
        try:
            prompt = f"""
            You are the Chief Logistics Communications Officer for an autonomous supply chain control tower.
            Write an executive explanation for corporate logistics leaders based STRICTLY on the deterministic solver results below.
            
            DISRUPTION CONTEXT:
            - Disruption: {event.disruption_type.value} at {event.location}
            - Severity: {event.severity:.2f}, Est. Delay Without Mitigation: {event.duration_days} days
            - Cargo Value at Risk: ${risk.total_value_at_risk if risk else 0:,.2f}
            - Unmitigated SLA Penalty Exposure: ${base_exposure:,.2f}
            
            SOLVER METRICS (DO NOT ALTER THESE NUMBERS):
            - Total Orders Managed: {total_orders}
            - Orders Delivered 100% On-Time: {on_time} ({service_level:.1f}% Service Level)
            - Interventions Selected: {actions_summary}
            - Resource Utilization: {air_units} units via air freight, {wh_units} units diverted through alternate hubs
            - Total Recovery Investment: ${recovery_cost:,.2f}
            - Residual Penalty Cost: ${penalty_cost:,.2f}
            - Total Combined Cost: ${combined_cost:,.2f}
            - Net Prevented Losses / Savings: ${net_savings:,.2f}
            
            RULES:
            1. Use ONLY the exact numbers provided above. DO NOT invent or alter any figures.
            2. Explain WHY the optimizer selected high-cost air freight for priority shipments while routing others to alternate regional warehouses.
            3. Highlight the net financial protection (${net_savings:,.2f} saved vs unmitigated SLA penalties).
            4. Keep the summary concise (2 short paragraphs).
            """
            response = llm.invoke(prompt)
            explanation = str(response.content).strip()
            llm_calls += 1
        except Exception as e:
            model_name = f"Deterministic Fallback (LLM Exception: {e})"
            explanation = (
                f"The deterministic MILP solver mitigated the {event.disruption_type.value} disruption at {event.location} "
                f"by allocating {actions_summary}. This strategy achieved a {service_level:.1f}% service level ({on_time}/{total_orders} on time) "
                f"for a total recovery investment of ${recovery_cost:,.2f}. By strategically utilizing {air_units} units of air freight "
                f"for critical orders and diverting {wh_units} units through secondary distribution centers, the system prevented "
                f"${net_savings:,.2f} in potential SLA breach penalties."
            )
    else:
        explanation = (
            f"The deterministic MILP solver mitigated the {event.disruption_type.value} disruption at {event.location} "
            f"by allocating {actions_summary}. This strategy achieved a {service_level:.1f}% service level ({on_time}/{total_orders} on time) "
            f"for a total recovery investment of ${recovery_cost:,.2f}. By strategically utilizing {air_units} units of air freight "
            f"for critical orders and diverting {wh_units} units through secondary distribution centers, the system prevented "
            f"${net_savings:,.2f} in potential SLA breach penalties."
        )

    log_audit_entry(
        scenario_id=scenario_id,
        phase="EXECUTIVE_EXPLANATION",
        agent_name="Explainer_Agent",
        action_taken=f"Synthesized solver rationale via {model_name}",
        model_used=model_name,
        cost_impact=0.0,
        requires_approval=False,
        approval_status="AUTO_APPROVED",
        details=explanation[:300] + "..."
    )

    trail = list(state.get("audit_trail", []))
    trail.append({
        "phase": "Explanation",
        "agent": "Explainer_Agent",
        "action": f"Generated plain-English explanation via {model_name}",
        "details": explanation
    })

    return {
        "explanation": explanation,
        "llm_call_count": llm_calls,
        "audit_trail": trail
    }
