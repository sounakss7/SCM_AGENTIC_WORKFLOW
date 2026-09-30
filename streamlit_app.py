"""Streamlit Interactive Control Tower Dashboard for Multi-Echelon Supply Chain.

Features:
- Multi-echelon physical network topology (3 Suppliers -> 2 Warehouses -> 6 Stores)
- Live LangGraph agent negotiation trace (Demand, Procurement, Logistics, Resolver, Explainer)
- Injectable disruption scenarios with before/after cost and service level deltas
- Empirical benchmark policy comparison charts loaded directly from results/results.json
"""

import os
import json
import streamlit as st
import pandas as pd
import numpy as np

from core.network import get_default_network
from agents.state import DisruptionEvent
from agents.workflow import run_control_tower_pipeline
from forecasting.forecaster import forecaster

st.set_page_config(
    page_title="Supply Chain Control Tower",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌐 Multi-Echelon Supply Chain Control Tower")
st.caption(
    "Cooperating LangGraph Agents with a Deterministic PuLP MILP Optimization Core "
    "(Suppliers -> Warehouses -> Stores)"
)

net = get_default_network()

# Sidebar: Disruption Injection & Controls
st.sidebar.header("🕹️ Control & Disruption Panel")

disrupt_type = st.sidebar.selectbox(
    "Inject Operational Disruption",
    options=["NONE", "SUPPLIER_DELAY", "PORT_CONGESTION", "DEMAND_SPIKE", "WAREHOUSE_CAPACITY_LOSS"]
)

disruption_event = None
if disrupt_type == "SUPPLIER_DELAY":
    aff = st.sidebar.selectbox("Affected Supplier", ["S1", "S2", "S3"], index=0)
    sev = st.sidebar.slider("Lead Time Increase (Periods)", 1, 3, 2)
    disruption_event = DisruptionEvent(
        disruption_type="SUPPLIER_DELAY",
        affected_entity=aff,
        severity_factor=float(sev),
        duration_periods=2,
        description=f"Factory strike and backlog at {aff}; lead time increased by +{sev} periods."
    )
elif disrupt_type == "PORT_CONGESTION":
    lane = st.sidebar.selectbox("Choked Lane", ["S1->W1", "S2->W1", "S1->W2"], index=0)
    disruption_event = DisruptionEvent(
        disruption_type="PORT_CONGESTION",
        affected_entity=lane,
        severity_factor=0.3,
        duration_periods=2,
        description=f"Port container dwell time surge on {lane}; lane throughput throttled."
    )
elif disrupt_type == "DEMAND_SPIKE":
    store = st.sidebar.selectbox("Spike Retail Store", [f"R{i}" for i in range(1, 7)], index=0)
    spike_mult = st.sidebar.slider("Demand Spike Multiplier", 1.5, 3.0, 2.0, 0.1)
    disruption_event = DisruptionEvent(
        disruption_type="DEMAND_SPIKE",
        affected_entity=store,
        severity_factor=spike_mult,
        duration_periods=2,
        description=f"Panic buying surge of +{int((spike_mult-1)*100)}% at {store}."
    )
elif disrupt_type == "WAREHOUSE_CAPACITY_LOSS":
    wh = st.sidebar.selectbox("Affected Warehouse", ["W1", "W2"], index=0)
    disruption_event = DisruptionEvent(
        disruption_type="WAREHOUSE_CAPACITY_LOSS",
        affected_entity=wh,
        severity_factor=0.5,
        duration_periods=3,
        description=f"Sprinkler flooding at {wh}; usable storage capacity cut by 50%."
    )

st.sidebar.markdown("---")
max_rounds = st.sidebar.slider("Max Negotiation Rounds", 1, 4, 2)
run_pipeline_btn = st.sidebar.button("🚀 Run Agentic Control Tower", type="primary", use_container_width=True)

# Run Pipeline
if "state" not in st.session_state or run_pipeline_btn:
    with st.spinner("Executing Demand Agent -> Procurement Agent -> Logistics Agent -> Resolver MILP -> Explainer..."):
        st.session_state.state = run_control_tower_pipeline(
            network=net,
            disruption=disruption_event,
            max_rounds=max_rounds
        )

state = st.session_state.state
sol = state.get("joint_solution")

# Top KPI Metric Cards
if sol:
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Landed Cost", f"${sol.total_cost:,.2f}")
    with c2:
        st.metric("Service Level", f"{sol.service_level_pct:.1f}%")
    with c3:
        st.metric("Units Fulfilled", f"{sol.total_fulfilled_units:,.0f} / {sol.total_demand_units:,.0f}")
    with c4:
        st.metric("Stockout Rate", f"{sol.stockout_rate_pct:.1f}%", delta=f"{sol.total_stockout_units:,.0f} units unmet", delta_color="inverse")
    with c5:
        if disruption_event:
            delta = state.get("cost_delta", 0.0)
            st.metric("Disruption Delta", f"{'+' if delta >= 0 else ''}${delta:,.2f}", delta=f"{state.get('service_delta', 0.0):+.1f}% SLA", delta_color="inverse")
        else:
            st.metric("Disruption Delta", "$0.00", delta="Steady-state", delta_color="normal")

st.markdown("---")

# Navigation Tabs
tab_network, tab_negotiation, tab_plan, tab_briefing, tab_benchmark = st.tabs([
    "🗺️ Network Topology",
    "🤝 Live Agent Negotiation Trace",
    "📦 Optimal Replenishment Plan",
    "📄 Executive Briefing",
    "📊 Empirical Policy Benchmark"
])

# Tab 1: Network Topology
with tab_network:
    st.subheader("Physical Multi-Echelon Network Structure")
    col_s, col_w, col_r = st.columns(3)

    with col_s:
        st.markdown("#### 🏭 Tier 1: Suppliers")
        for s in net.suppliers:
            st.info(
                f"**{s.name}**\n"
                f"- Lead Time: {s.lead_time_periods} period(s)\n"
                f"- Capacity: {s.capacity_per_period} units/period\n"
                f"- Reliability: {s.reliability_score*100:.0f}%\n"
                f"- Unit Costs: SKU101: ${s.unit_procurement_costs['SKU_101']:.0f} | "
                f"SKU202: ${s.unit_procurement_costs['SKU_202']:.0f} | "
                f"SKU303: ${s.unit_procurement_costs['SKU_303']:.0f}"
            )

    with col_w:
        st.markdown("#### 🏬 Tier 2: Regional Hubs")
        for w in net.warehouses:
            st.warning(
                f"**{w.name}**\n"
                f"- Storage Capacity: {w.storage_capacity} units\n"
                f"- Holding Cost: ${w.holding_cost_per_unit_period:.2f}/unit/period\n"
                f"- Initial Stock: {sum(w.initial_inventory.values())} units"
            )

    with col_r:
        st.markdown("#### 🏪 Tier 3: Retail Stores")
        for r in net.stores:
            st.success(
                f"**{r.name}**\n"
                f"- Holding Cost: ${r.holding_cost_per_unit_period:.2f}/unit/period\n"
                f"- Initial Stock: {sum(r.initial_inventory.values())} units\n"
                f"- Stockout Penalty: ${r.stockout_penalty_per_unit['SKU_101']:.0f} - ${r.stockout_penalty_per_unit['SKU_303']:.0f}/unit"
            )

# Tab 2: Agent Negotiation Trace
with tab_negotiation:
    st.subheader("🤝 Multi-Agent Cooperative Negotiation Trace")
    st.caption("Procurement Agent and Logistics Agent propose conflicting plans; Resolver Agent mediates via PuLP MILP solver.")

    negotiation_log = state.get("negotiation_log", [])
    if negotiation_log:
        for entry in negotiation_log:
            with st.expander(f"Round {entry['round_index']} Mediation Log", expanded=True):
                st.write(f"**Procurement Strategy:** {entry['procurement_strategy']}")
                st.write(f"**Logistics Strategy:** {entry['logistics_strategy']}")
                st.error(f"**Conflict Identified:** {entry['conflict']}")
                st.success(f"**Resolver Action:** {entry['resolution']}")
                m_c1, m_c2, m_c3 = st.columns(3)
                m_c1.metric("Mediated Total Cost", f"${entry['joint_cost']:,.2f}")
                m_c2.metric("Service Level", f"{entry['service_level_pct']:.1f}%")
                m_c3.metric("Stockout Deficit", f"{entry['stockout_units']:,.0f} units")
    else:
        st.info("No negotiation rounds recorded.")

# Tab 3: Optimal Replenishment Plan
with tab_plan:
    st.subheader("Deterministic Replenishment & Sourcing Orders")
    if sol:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("#### Supplier Orders ($S \\to W$)")
            s_rows = [{"Shipment Lane & SKU": k, "Quantity (Units)": v} for k, v in sol.supplier_orders.items()]
            st.dataframe(pd.DataFrame(s_rows) if s_rows else pd.DataFrame(columns=["Shipment", "Quantity"]), use_container_width=True)

        with col_p2:
            st.markdown("#### Warehouse Replenishment ($W \\to R$)")
            w_rows = [{"Dispatch Lane & SKU": k, "Quantity (Units)": v} for k, v in sol.warehouse_orders.items()]
            st.dataframe(pd.DataFrame(w_rows) if w_rows else pd.DataFrame(columns=["Dispatch", "Quantity"]), use_container_width=True)

        st.markdown("#### Cost Breakdown")
        cost_df = pd.DataFrame([
            {"Cost Category": "Procurement Cost", "Amount ($)": sol.procurement_cost},
            {"Cost Category": "Transport & Freight Cost", "Amount ($)": sol.transport_cost},
            {"Cost Category": "Inventory Holding Cost", "Amount ($)": sol.holding_cost},
            {"Cost Category": "Stockout Penalty Cost", "Amount ($)": sol.stockout_cost},
            {"Cost Category": "Total Landed Cost", "Amount ($)": sol.total_cost}
        ])
        st.dataframe(cost_df, use_container_width=True)

# Tab 4: Executive Briefing
with tab_briefing:
    st.subheader("Operational & Executive Briefing")
    briefing_text = state.get("plain_english_briefing", "No briefing generated.")
    st.markdown(briefing_text)

# Tab 5: Benchmark
with tab_benchmark:
    st.subheader("📊 N=200 Empirical Policy Benchmark")
    st.caption("Live comparison across 4 policies from `results/results.json` over 200 randomized scenarios (seed=42).")

    res_path = os.path.join(os.path.dirname(__file__), "results", "results.json")
    if os.path.exists(res_path):
        with open(res_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        summary = data.get("summary", {})

        b_rows = []
        for policy, m in summary.items():
            b_rows.append({
                "Policy": policy,
                "Mean Total Cost ($)": f"${m['mean_total_cost_usd']:,.2f}",
                "Service Level (%)": f"{m['mean_service_level_pct']:.1f}%",
                "Stockout Rate (%)": f"{m['mean_stockout_rate_pct']:.1f}%",
                "Feasibility (%)": f"{m['plan_feasibility_rate_pct']:.1f}%",
                "Latency (s)": f"{m['mean_latency_sec']:.4f}s",
                "LLM Calls": m["mean_llm_calls_per_scenario"]
            })
        st.dataframe(pd.DataFrame(b_rows), use_container_width=True)

        # Plot Cost vs Service Level Tradeoff Chart
        chart_data = pd.DataFrame([
            {
                "Policy": policy,
                "Cost ($)": m["mean_total_cost_usd"],
                "Service Level (%)": m["mean_service_level_pct"],
                "Feasibility (%)": m["plan_feasibility_rate_pct"]
            }
            for policy, m in summary.items()
        ])

        st.markdown("#### Cost vs. Service Level Tradeoff")
        st.bar_chart(chart_data.set_index("Policy")[["Cost ($)"]])
        st.markdown("#### Plan Feasibility Rate (%)")
        st.bar_chart(chart_data.set_index("Policy")[["Feasibility (%)"]])
    else:
        st.warning("Benchmark results file not found. Run `python eval/run_benchmark.py --scenarios 200` to generate.")
