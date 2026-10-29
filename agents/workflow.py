"""LangGraph 5-Agent Resilience Workflow Orchestrator.

Constructs the multi-agent graph with:
- Monitor Agent -> Risk Assessor (Gemini 2.5 Flash) -> Routing Agent (Solver Core)
  -> Validator Agent (Groq Low Latency) -> [Self-Correction Loop back to Routing if rejected]
  -> Explainer Agent (Gemini 2.5 Flash).

Enterprise Features:
- SQL Database Audit Trail (MySQL with SQLite fallback): Saves every routing decision & agent step.
- Zero-Trust Guardrails: InputGuard (prompt & SQL injection defense) + OutputGuard (leak defense).
- Self-Correction Loop: Carrier rejection (e.g., port congestion) dynamically triggers replanning.
- Multi-Model Orchestration: Google Gemini 2.5 Flash for reasoning + Groq LPU for sub-15ms validation.
"""

from typing import Dict, Any, Optional, List, TypedDict
from langgraph.graph import StateGraph, END

from agents.state import DisruptionWorkflowState
from agents.monitor import monitor_agent_node
from agents.risk_agent import risk_agent_node
from agents.routing_agent import routing_agent_node
from agents.validator_agent import validator_agent_node
from agents.explainer_agent import explainer_agent_node
from agents.guards import SecurityGuards
from optimizer.resilience_solver import find_optimal_alternate_route

from database.db_manager import (
    init_database,
    save_order_history_record,
    save_routing_decision,
    save_security_audit_record,
    get_order_history
)

# Optional imports from nodes for legacy/test_runner compatibility
try:
    from agents.nodes import (
        user_interface_agent,
        supply_chain_intelligence_agent,
        compliance_agent,
        orchestration_agent,
        external_entities_node
    )
except ImportError:
    user_interface_agent = None
    supply_chain_intelligence_agent = None
    compliance_agent = None
    orchestration_agent = None
    external_entities_node = None


# ═══════════════════════════════════════════════════════════════════════════
# 1. FIVE-AGENT INDIAN RESILIENCE LANGGRAPH WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

def route_after_monitor(state: DisruptionWorkflowState) -> str:
    """Conditional branch after Monitor Agent."""
    if state.get("disruption_detected"):
        return "risk_assessor"
    return "explainer"


def route_after_routing(state: DisruptionWorkflowState) -> str:
    """Conditional branch after Routing Agent."""
    if state.get("status") == "FAILED" or not state.get("proposed_plan"):
        return "explainer"
    return "validator"


def route_after_validator(state: DisruptionWorkflowState) -> str:
    """Conditional branch after Validator Agent with self-correcting retry loop."""
    status = state.get("status")
    if status == "RETRYING":
        return "routing_agent"
    return "explainer"


def build_resilience_graph():
    """Build and compile the 5-Agent LangGraph StateGraph."""
    workflow = StateGraph(DisruptionWorkflowState)

    # 1. Add agent nodes
    workflow.add_node("monitor", monitor_agent_node)
    workflow.add_node("risk_assessor", risk_agent_node)
    workflow.add_node("routing_agent", routing_agent_node)
    workflow.add_node("validator", validator_agent_node)
    workflow.add_node("explainer", explainer_agent_node)

    # 2. Add entry point
    workflow.set_entry_point("monitor")

    # 3. Add conditional & direct transitions
    workflow.add_conditional_edges(
        "monitor",
        route_after_monitor,
        {
            "risk_assessor": "risk_assessor",
            "explainer": "explainer"
        }
    )

    workflow.add_edge("risk_assessor", "routing_agent")

    workflow.add_conditional_edges(
        "routing_agent",
        route_after_routing,
        {
            "validator": "validator",
            "explainer": "explainer"
        }
    )

    workflow.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "routing_agent": "routing_agent",  # Self-correction loop!
            "explainer": "explainer"
        }
    )

    workflow.add_edge("explainer", END)

    return workflow.compile()


resilience_graph = build_resilience_graph()


def run_resilience_workflow(
    order_id: str,
    sku_id: str,
    quantity: int,
    source_supplier: str,
    target_retailer: str,
    disruption: Optional[Dict[str, Any]] = None,
    nominal_plan: Optional[Dict[str, Any]] = None,
    max_retries: int = 3
) -> DisruptionWorkflowState:
    """
    Execute the full 5-agent LangGraph workflow for an order under disruption.
    - Validates inputs against Prompt Injection & SQL Injection (InputGuard).
    - Executes self-correcting retry loop if carrier rejects booking.
    - Sanitizes executive explanation (OutputGuard).
    - Persists every routing decision and agent step to SQL database (MySQL / SQLite).
    """
    # 0. Ensure Database Tables Exist
    init_database()

    # 1. Zero-Trust Security Gate: InputGuard (blocks prompt/SQL injection)
    is_safe = SecurityGuards.InputGuard(
        order_id,
        sku_id,
        source_supplier,
        target_retailer,
        disruption
    )
    if not is_safe:
        threat_msg = f"⚠️ SECURITY THREAT INTERCEPTED: Malicious prompt/SQL injection detected in order {order_id}."
        save_security_audit_record(
            order_id=order_id,
            threat_type="PROMPT_OR_SQL_INJECTION",
            payload=str(disruption or f"{order_id}_{sku_id}"),
            agent_name="InputGuard",
            action_taken="QUARANTINED"
        )
        save_order_history_record(
            order_id=order_id,
            phase="Order Intake Phase",
            agent_name="SecurityGuard",
            action=threat_msg,
            model_used="Deterministic Guard",
            cost_savings="$0.00",
            live_location="System Quarantine"
        )
        return {
            "order_id": order_id,
            "sku_id": sku_id,
            "quantity": quantity,
            "source_supplier": source_supplier,
            "target_retailer": target_retailer,
            "disruption_detected": True,
            "status": "Security Exception",
            "explanation": threat_msg,
            "agent_logs": [{
                "agent": "SecurityGuard",
                "action": "Blocked",
                "message": threat_msg,
                "status": "QUARANTINED"
            }],
            "model_records": []
        }

    # 2. Compute baseline nominal plan if not supplied
    if not nominal_plan:
        initial_solution, _ = find_optimal_alternate_route(
            supplier_id=source_supplier,
            retailer_id=target_retailer,
            sku_id=sku_id,
            quantity=quantity
        )
        if initial_solution:
            nominal_plan = initial_solution.to_dict()

    initial_state: DisruptionWorkflowState = {
        "order_id": order_id,
        "sku_id": sku_id,
        "quantity": quantity,
        "source_supplier": source_supplier,
        "target_retailer": target_retailer,
        "nominal_plan": nominal_plan,
        "disruption": disruption,
        "disruption_detected": False,
        "risk_assessment": None,
        "proposed_plan": None,
        "validation_result": None,
        "retry_count": 0,
        "max_retries": max_retries,
        "explanation": None,
        "final_plan": nominal_plan,
        "status": "INITIALIZED",
        "agent_logs": [],
        "model_records": []
    }

    # 3. Log Initial Ingestion to SQL Audit Trail
    save_order_history_record(
        order_id=order_id,
        phase="Order Ingestion Phase",
        agent_name="Monitor Agent",
        action=f"Order {order_id} ({quantity} units of {sku_id}) queued for monitoring.",
        model_used="Deterministic Engine",
        cost_savings="₹0.00",
        live_location=source_supplier
    )

    if nominal_plan:
        save_routing_decision(
            order_id=order_id,
            cycle=0,
            plan_dict=nominal_plan,
            status="NOMINAL_BASELINE",
            rejection_reason=None
        )

    # 4. Invoke LangGraph 5-Agent Resilience Workflow
    final_state = resilience_graph.invoke(initial_state)

    # 5. OutputGuard: Sanitize LLM Generated Output
    explanation = final_state.get("explanation")
    if explanation:
        if not SecurityGuards.OutputGuard(explanation):
            final_state["explanation"] = "Audited recovery plan verified and dispatched according to deterministic constraints."

    # 6. Persist All Intermediate Agent Steps to SQL Database
    agent_logs = final_state.get("agent_logs", [])
    savings_str = "₹0.00"
    if final_state.get("final_plan") and nominal_plan:
        savings_val = final_state["final_plan"].get("cost_delta_inr", 0.0)
        savings_str = f"₹{abs(savings_val):,.2f} ({'Cost Delta' if savings_val >= 0 else 'Savings'})"

    for log in agent_logs:
        agent_name = log.get("agent", "Agent")
        action = log.get("action", "Execution")
        msg = log.get("message", "")
        status = log.get("status", "SUCCESS")
        model = "Gemini 2.5 Flash" if "Gemini" in msg or "Explainer" in agent_name or "Risk" in agent_name else (
            "Groq LPU" if "Groq" in msg or "Validator" in agent_name else "Deterministic Solver"
        )
        save_order_history_record(
            order_id=order_id,
            phase=f"{agent_name} Execution",
            agent_name=agent_name,
            action=f"[{status}] {action}: {msg}",
            model_used=model,
            cost_savings=savings_str,
            live_location=final_state.get("final_plan", {}).get("warehouse", target_retailer)
        )

    # 7. Persist Final Routing Decision to SQL Database
    if final_state.get("final_plan"):
        v_res = final_state.get("validation_result") or {}
        rej_reason = " | ".join(v_res.get("violations", [])) if not v_res.get("is_valid", True) else None
        save_routing_decision(
            order_id=order_id,
            cycle=final_state.get("retry_count", 0),
            plan_dict=final_state["final_plan"],
            status=final_state.get("status", "COMPLETED"),
            rejection_reason=rej_reason
        )

    return final_state


# ═══════════════════════════════════════════════════════════════════════════
# 2. GLOBAL / SCMSTATE WORKFLOW WITH SELF-CORRECTING PORT CONGESTION (LA -> SEATTLE)
# ═══════════════════════════════════════════════════════════════════════════

class SCMState(TypedDict, total=False):
    order_id: str
    customer_id: str
    customer_tier: str
    current_phase: str
    inventory_status: str
    route_selected: str
    carrier_status: str
    optimization_cycles: int
    detected_disruptions: List[str]
    audit_trail: List[Dict[str, Any]]
    status: str
    requires_correction: bool
    simulate_disruption: bool
    cost_savings: str
    live_location: str
    agent_thoughts: Dict[str, str]


def route_after_ui_scm(state: SCMState) -> str:
    """Short-circuit workflow on security quarantine."""
    if state.get("status") == "Security Exception":
        return END
    return "intelligence_agent"


def route_after_external_scm(state: SCMState) -> str:
    """Self-correction loop: if carrier rejects booking, loop back to orchestration agent."""
    carrier_status = state.get("carrier_status", "")
    cycles = state.get("optimization_cycles", 0)
    if "Booking Rejected" in carrier_status and cycles <= 2:
        return "orchestration_agent"  # Self-correction loop!
    return END


def wrap_logged_node(node_fn, node_name: str, phase_name: str):
    """Decorator that wraps an agent node to log its execution step into SQL database."""
    def wrapper(state: SCMState) -> SCMState:
        res = node_fn(state)
        order_id = res.get("order_id", "UNKNOWN")
        thoughts = res.get("agent_thoughts", {}).get(node_name, f"{node_name} executed")
        save_order_history_record(
            order_id=order_id,
            phase=res.get("current_phase", phase_name),
            agent_name=node_name,
            action=str(thoughts)[:300],
            model_used="Deterministic / LLM",
            cost_savings=res.get("cost_savings", "$0.00"),
            live_location=res.get("live_location", "Transit")
        )
        return res
    return wrapper


def build_scm_workflow():
    """Build and compile the multi-agent SCM workflow with self-correcting port congestion reroute."""
    if not user_interface_agent or not supply_chain_intelligence_agent:
        raise ImportError("agents.nodes must be available to build SCM workflow")

    init_database()
    workflow = StateGraph(SCMState)

    workflow.add_node("ui_agent", wrap_logged_node(user_interface_agent, "ui_agent", "Order Intake Phase"))
    workflow.add_node("intelligence_agent", wrap_logged_node(supply_chain_intelligence_agent, "intelligence_agent", "Order Assessment Phase"))
    workflow.add_node("compliance_agent", wrap_logged_node(compliance_agent, "compliance_agent", "Regulatory Sandbox Verification"))
    workflow.add_node("orchestration_agent", wrap_logged_node(orchestration_agent, "orchestration_agent", "Logistics Planning Phase"))
    workflow.add_node("external_entities", wrap_logged_node(external_entities_node, "external_entities", "Autonomous Execution Phase"))

    workflow.set_entry_point("ui_agent")

    workflow.add_conditional_edges(
        "ui_agent",
        route_after_ui_scm,
        {
            "intelligence_agent": "intelligence_agent",
            END: END
        }
    )

    workflow.add_edge("intelligence_agent", "compliance_agent")
    workflow.add_edge("compliance_agent", "orchestration_agent")
    workflow.add_edge("orchestration_agent", "external_entities")

    workflow.add_conditional_edges(
        "external_entities",
        route_after_external_scm,
        {
            "orchestration_agent": "orchestration_agent",  # Self-correction loop!
            END: END
        }
    )

    return workflow.compile()
