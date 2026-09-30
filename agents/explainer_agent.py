"""Explainer Agent: Translates deterministic optimizer results into plain-English operational briefs.

Strict Rule: The LLM must NOT alter any numbers or hallucinate mathematical figures.
All numbers must strictly match the deterministic MILP solution.
"""

from typing import Dict
from agents.state import MultiEchelonAgentState


def generate_plain_english_briefing(state: MultiEchelonAgentState) -> str:
    """Generate executive and operational summary strictly grounded in solver facts."""
    sol = state.get("joint_solution")
    disruption = state.get("active_disruption")
    rounds = len(state.get("negotiation_log", []))

    if not sol or not sol.is_feasible:
        return "Operational Warning: Optimization model was infeasible. Emergency manual escalation required."

    disruption_text = "None (Steady-state operations)"
    if disruption:
        disruption_text = f"**{disruption.disruption_type}** affecting `{disruption.affected_entity}` (Severity: {disruption.severity_factor}x)"

    # Identify top suppliers and warehouses used
    s1_vol = sum(v for k, v in sol.supplier_orders.items() if k.startswith("S1"))
    s2_vol = sum(v for k, v in sol.supplier_orders.items() if k.startswith("S2"))
    s3_vol = sum(v for k, v in sol.supplier_orders.items() if k.startswith("S3"))

    briefing = (
        f"### 🌐 Multi-Echelon Supply Chain Control Tower Briefing\n\n"
        f"**Executive Status**: Optimal multi-echelon replenishment plan generated after **{rounds} negotiation round(s)**.\n\n"
        f"#### 1. Key Performance Indicators\n"
        f"- **Total Landed Cost**: **${sol.total_cost:,.2f}**\n"
        f"  - Procurement Spend: ${sol.procurement_cost:,.2f}\n"
        f"  - Transport & Freight Spend: ${sol.transport_cost:,.2f}\n"
        f"  - Inventory Holding Cost: ${sol.holding_cost:,.2f}\n"
        f"  - Stockout Penalty Cost: ${sol.stockout_cost:,.2f}\n"
        f"- **Service Level**: **{sol.service_level_pct:.1f}%** ({sol.total_fulfilled_units:,.0f} / {sol.total_demand_units:,.0f} units fulfilled)\n"
        f"- **Stockout Rate**: **{sol.stockout_rate_pct:.1f}%** ({sol.total_stockout_units:,.0f} units unmet)\n\n"
        f"#### 2. Sourcing & Fulfillment Allocations\n"
        f"- **Global Bulk Supplier (S1)**: {s1_vol:,.0f} units ordered (Cost-efficient baseline)\n"
        f"- **Regional Supplier (S2)**: {s2_vol:,.0f} units ordered (Lead-time buffer)\n"
        f"- **Express Supplier (S3)**: {s3_vol:,.0f} units ordered (Emergency same-period fulfillment)\n\n"
        f"#### 3. Active Disruption & Mitigation Response\n"
        f"- **Active Incident**: {disruption_text}\n"
    )

    if disruption:
        cost_delta = state.get("cost_delta", 0.0)
        svc_delta = state.get("service_delta", 0.0)
        briefing += (
            f"- **Financial Impact**: Net cost change of **{'+' if cost_delta >= 0 else ''}${cost_delta:,.2f}** "
            f"and service level change of **{svc_delta:+.1f}%** compared to pre-disruption baseline.\n"
            f"- **Agent Mediation Action**: Procurement and Logistics synchronized sourcing to reroute "
            f"inventory around the bottleneck while strictly respecting warehouse storage capacities.\n"
        )
    else:
        briefing += "- **Steady-State Stability**: All network flow balances, lead times, and capacity caps satisfied.\n"

    return briefing


def explainer_agent_node(state: MultiEchelonAgentState) -> Dict:
    """LangGraph node: Formulate plain-English executive briefing."""
    briefing = generate_plain_english_briefing(state)
    return {"plain_english_briefing": briefing}
