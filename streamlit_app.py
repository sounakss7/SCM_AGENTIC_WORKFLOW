import os
import sys
import json
import time
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.config import settings
from core.schema import (
    DisruptionEvent,
    DisruptionType,
    OptimizationConstraints,
    CustomerTier
)
from core.data_loader import DataCoDataLoader
from core.database import (
    init_database,
    get_audit_trail,
    update_approval_status
)
from agents.workflow import scm_graph
from ui.styles import DARK_THEME_CSS

# Page Configuration
st.set_page_config(
    page_title="SCM Disruption Response Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Styling
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Initialize Session State
init_database()
if "last_plan_result" not in st.session_state:
    st.session_state.last_plan_result = None
if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = False
if "scenario_id" not in st.session_state:
    st.session_state.scenario_id = "SCEN-LIVE-01"

# Sidebar Configuration
with st.sidebar:
    st.image("ui/scm_logo.png", width=60)
    st.title("SCM Control Tower")
    st.caption("Deterministic Optimizer & Multi-Agent Disruption Engine")
    st.divider()

    st.subheader("🔑 Engine Settings")
    gemini_key = st.text_input("Gemini API Key", value=settings.GEMINI_API_KEY or "", type="password")
    groq_key = st.text_input("Groq API Key", value=settings.GROQ_API_KEY or "", type="password")
    
    if gemini_key:
        settings.GEMINI_API_KEY = gemini_key
    if groq_key:
        settings.GROQ_API_KEY = groq_key

    st.selectbox(
        "LLM Provider",
        options=["gemini", "groq"],
        index=0 if settings.ROUTING_PREFERENCE == "gemini" else 1,
        help="Used strictly for natural language explanation of solver output. Zero arithmetic performed by LLM."
    )

    st.divider()
    st.subheader("🛡️ Governance Policies")
    st.metric("HITL Approval Threshold", f"${settings.HITL_APPROVAL_THRESHOLD_USD:,.2f}")
    st.caption("Plans with recovery investment exceeding this threshold require dispatcher authorization.")
    
    st.divider()
    st.markdown("**Core Specifications:**")
    st.markdown("- **Dataset**: DataCo Smart Supply Chain (CC BY 4.0)")
    st.markdown("- **Optimizer**: PuLP Mixed-Integer Linear Program (MILP)")
    st.markdown("- **Orchestration**: LangGraph Cyclic StateGraph")

# Header Banner
st.markdown("""
<div class="header-container">
    <div class="header-title">⚡ SCM Autonomous Disruption Response Engine</div>
    <div class="header-subtitle">Multi-Agent Disruption Perception & Deterministic MILP Recovery Optimizer</div>
</div>
""", unsafe_allow_html=True)

tab_command, tab_audit, tab_benchmarks = st.tabs([
    "🚀 Disruption Command Center",
    "🛡️ Decision Audit Ledger",
    "📊 Empirical Benchmark (N=200)"
])

# ==========================================
# TAB 1: DISRUPTION COMMAND CENTER
# ==========================================
with tab_command:
    col_input, col_preview = st.columns([1, 1])

    with col_input:
        st.markdown("### 💥 Disruption Scenario Setup")
        disruption_type_str = st.selectbox(
            "Disruption Event Type",
            options=[d.value for d in DisruptionType],
            index=0
        )
        dtype = DisruptionType(disruption_type_str)

        col_loc, col_dur = st.columns(2)
        with col_loc:
            location = st.text_input("Disrupted Hub / Corridor", value="Port of Los Angeles")
        with col_dur:
            duration_days = st.slider("Estimated Disruption Duration (Days)", min_value=2, max_value=30, value=8)

        severity = st.slider("Disruption Severity Factor", min_value=0.1, max_value=1.0, value=0.85, step=0.05)
        description = st.text_area(
            "Disruption Bulletin / Description",
            value="Critical labor dispute and vessel backlog causing extensive container terminal congestion."
        )

        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            order_sample_count = st.number_input("At-Risk Shipments Count", min_value=5, max_value=50, value=12)
        with col_opt2:
            air_cap = st.number_input("Express Air Cargo Quota (Units)", min_value=20, max_value=500, value=150)

    with col_preview:
        st.markdown("### 📦 Vulnerable Cargo Preview (DataCo Dataset)")
        loader = DataCoDataLoader()
        preview_orders = loader.sample_active_orders(n=order_sample_count, random_seed=42)
        
        preview_data = []
        for o in preview_orders:
            preview_data.append({
                "Order ID": o.order_id,
                "Customer": o.customer_id,
                "Tier": o.customer_tier.value,
                "Product": o.product_name[:28] + "...",
                "Qty": o.quantity,
                "Value ($)": f"${o.total_value:,.2f}",
                "Sched Days": o.scheduled_days,
                "Penalty/Day": f"${o.daily_late_penalty_rate:,.2f}"
            })
        st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)

    st.markdown("---")
    
    if st.button("🚀 Execute Autonomous Multi-Agent Resolution", type="primary", use_container_width=True):
        scen_id = f"SCEN-{int(time.time()) % 100000:05d}"
        st.session_state.scenario_id = scen_id

        event = DisruptionEvent(
            event_id=f"EVT-{scen_id}",
            disruption_type=dtype,
            location=location,
            severity=severity,
            duration_days=duration_days,
            affected_warehouse="Pacific_Hub_LA",
            description=description
        )

        constraints = OptimizationConstraints(
            max_air_freight_units=int(air_cap)
        )

        init_state = {
            "scenario_id": scen_id,
            "disruption_event": event,
            "affected_orders": preview_orders,
            "risk_assessment": None,
            "constraints": constraints,
            "optimized_plan": None,
            "critic_verdict": None,
            "explanation": "",
            "requires_human_approval": False,
            "approval_status": "AUTO_APPROVED",
            "retry_count": 0,
            "llm_call_count": 0,
            "audit_trail": []
        }

        with st.spinner("Orchestrating agents (Monitor ➔ Risk Assessor ➔ PuLP Solver ➔ Critic ➔ Explainer)..."):
            final_state = scm_graph.invoke(init_state)
            st.session_state.last_plan_result = final_state

    # Render Results if Available
    if st.session_state.last_plan_result:
        res = st.session_state.last_plan_result
        plan = res.get("optimized_plan")
        risk = res.get("risk_assessment")
        critic = res.get("critic_verdict")

        st.markdown("## 📈 Resolution Metrics & Solver Telemetry")

        # KPI Metrics
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Total Landed Cost", f"${plan.total_combined_cost:,.2f}")
        with col_m2:
            st.metric("Recovery Investment", f"${plan.total_recovery_cost:,.2f}")
        with col_m3:
            net_saved = max(0.0, risk.base_penalty_exposure - plan.total_combined_cost) if risk else 0.0
            st.metric("Prevented Loss / Savings", f"${net_saved:,.2f}")
        with col_m4:
            st.metric("Service Level (% On-Time)", f"{plan.service_level_pct:.1f}%")

        col_sub1, col_sub2, col_sub3 = st.columns(3)
        with col_sub1:
            st.caption(f"**Solver Status**: `{plan.status}` (Runtime: {plan.solver_time_sec*1000:.1f}ms)")
        with col_sub2:
            air_u = plan.capacity_utilization.get("air_freight_used_units", 0)
            st.caption(f"**Air Freight Utilized**: `{air_u} / {air_cap} units`")
        with col_sub3:
            st.caption(f"**Feasibility**: `{'Verified Feasible' if plan.is_feasible else 'Infeasible'}`")

        # Human-in-the-Loop (HITL) Governance Card
        if res.get("requires_human_approval"):
            st.warning("⚠️ **Human-in-the-Loop Governance Triggered**: High-value recovery investment exceeds policy threshold ($5,000.00).")
            col_hitl_info, col_hitl_act1, col_hitl_act2 = st.columns([3, 1, 1])
            with col_hitl_info:
                st.markdown(f"**Plan ID:** `{plan.plan_id}` | **Current Status:** `{res.get('approval_status')}`")
            with col_hitl_act1:
                if st.button("✅ Approve Plan", type="primary", use_container_width=True):
                    update_approval_status(res["scenario_id"], "APPROVED")
                    res["approval_status"] = "APPROVED"
                    res["requires_human_approval"] = False
                    st.success("Plan Approved and logged to immutable audit ledger!")
                    time.sleep(0.5)
                    st.rerun()
            with col_hitl_act2:
                if st.button("❌ Reject Plan", use_container_width=True):
                    update_approval_status(res["scenario_id"], "REJECTED")
                    res["approval_status"] = "REJECTED"
                    res["requires_human_approval"] = False
                    st.error("Plan Rejected by dispatcher.")
                    time.sleep(0.5)
                    st.rerun()

        # Explainer Card
        st.markdown("### 📝 Plain-English Operational Rationale")
        st.info(res.get("explanation", "Rationale unavailable."))

        # Allocations Table
        st.markdown("### 📋 Mathematical Order Allocations (PuLP Output)")
        alloc_rows = []
        for a in plan.allocations:
            alloc_rows.append({
                "Order ID": a.order_id,
                "Product": a.product_name,
                "Qty": a.quantity,
                "Recovery Action": a.selected_action.value,
                "Intervention Cost ($)": f"${a.recovery_cost:,.2f}",
                "Delay Days": f"{a.expected_delay_days}d",
                "Penalty ($)": f"${a.incurred_penalty:,.2f}",
                "Total Loss ($)": f"${a.total_cost:,.2f}",
                "Fulfillment Node": a.fulfillment_node,
                "On-Time": "✅ Yes" if a.on_time else "❌ No"
            })
        st.dataframe(pd.DataFrame(alloc_rows), use_container_width=True, hide_index=True)

        # Execution Trace Expander
        with st.expander("🔄 View Multi-Agent State Execution Trace"):
            for entry in res.get("audit_trail", []):
                st.markdown(f"**[{entry.get('phase')}]** `{entry.get('agent')}`: {entry.get('action')}")
                st.caption(entry.get('details', ''))

# ==========================================
# TAB 2: DECISION AUDIT LEDGER
# ==========================================
with tab_audit:
    st.markdown("### 🛡️ Immutable SCM Decision Audit Ledger")
    st.markdown("Every agent action, solver execution, and Human-in-the-Loop decision is logged with timestamps.")

    logs = get_audit_trail(limit=50)
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    else:
        st.info("No audit logs recorded yet. Execute a disruption scenario to populate the ledger.")

# ==========================================
# TAB 3: EMPIRICAL BENCHMARK (N=200)
# ==========================================
with tab_benchmarks:
    st.markdown("### 📊 Empirical Benchmark Evaluation Suite (N=200 Scenarios)")
    st.markdown("Controlled comparison across 4 strategies generated from fixed random seeds (`seed=42`) on the DataCo dataset.")

    results_path = os.path.join(os.path.dirname(__file__), "results", "results.json")
    if os.path.exists(results_path):
        with open(results_path, "r", encoding="utf-8") as f:
            bench_data = json.load(f)

        summary_rows = bench_data.get("summary", [])
        meta = bench_data.get("benchmark_metadata", {})

        st.caption(f"**Evaluated Scenarios**: {meta.get('num_scenarios', 200)} | **Random Seed**: {meta.get('random_seed', 42)} | **Execution Time**: {meta.get('total_benchmark_duration_sec', 0):.2f}s")
        
        # Summary Table
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

        # Comparative Visualizations
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### 💰 Total Landed Cost Comparison ($)")
            cost_df = pd.DataFrame({
                "Strategy": [r["Strategy"] for r in summary_rows],
                "Total Cost ($)": [r["Total Cost ($)"] for r in summary_rows]
            }).set_index("Strategy")
            st.bar_chart(cost_df)

        with col_c2:
            st.markdown("#### 🛡️ Constraint Feasibility Rate (%)")
            feas_df = pd.DataFrame({
                "Strategy": [r["Strategy"] for r in summary_rows],
                "Plan Feasibility (%)": [r["Plan Feasibility (%)"] for r in summary_rows]
            }).set_index("Strategy")
            st.bar_chart(feas_df)

    else:
        st.warning("Benchmark results file not found. Click below to execute the 200-scenario benchmark suite.")
        if st.button("🧪 Run N=200 Benchmark Suite Now"):
            from eval.run_benchmark import run_evaluation_benchmark
            with st.spinner("Executing 200 comparative scenarios..."):
                run_evaluation_benchmark(num_scenarios=200, seed=42)
            st.success("Benchmark completed! Reloading dashboard...")
            st.rerun()
