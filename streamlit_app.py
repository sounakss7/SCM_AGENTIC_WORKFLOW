import streamlit as st
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load Environment Variables (.env)
load_dotenv()

# Modular SCM imports
from database.db_manager import (
    test_mysql_server,
    init_database,
    seed_database,
    get_customer,
    get_orders_by_customer,
    get_order_history,
    get_all_order_history,
    save_order_history_record,
    insert_new_order,
    update_order_status,
    get_last_ai_report,
    save_ai_report,
    get_mysql_connection,
    insert_new_customer
)
from agents.workflow import SCMState, scm_workflow_graph, orchestration_edge_router
from agents.nodes import (
    get_llm_client,
    user_interface_agent,
    supply_chain_intelligence_agent,
    compliance_agent,
    orchestration_agent,
    external_entities_node
)
from ui.styles import DARK_THEME_CSS, render_timeline_html, render_metrics_html

# ==========================================
# 1. UI CONFIGURATION & THEME INJECTION
# ==========================================
st.set_page_config(
    page_title="SCM Agentic Workflow Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Premium Dark Theme Styles
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# ==========================================
# 2. SESSION STATE INITIALIZATION
# ==========================================
if "use_sqlite" not in st.session_state:
    st.session_state.use_sqlite = True
if "mysql_host" not in st.session_state:
    st.session_state.mysql_host = "localhost"
if "mysql_port" not in st.session_state:
    st.session_state.mysql_port = "3306"
if "mysql_user" not in st.session_state:
    st.session_state.mysql_user = "root"
if "mysql_password" not in st.session_state:
    st.session_state.mysql_password = ""
if "mysql_database" not in st.session_state:
    st.session_state.mysql_database = "scm_agentic_db"
if "db_initialized" not in st.session_state:
    st.session_state.db_initialized = False

# LLM API Keys
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY", "")
if "routing_preference" not in st.session_state:
    st.session_state.routing_preference = "gemini"

# Simulation runtime variables
if "selected_customer" not in st.session_state:
    st.session_state.selected_customer = None
if "workflow_history" not in st.session_state:
    st.session_state.workflow_history = []
if "agent_running" not in st.session_state:
    st.session_state.agent_running = ""

# Auto-initialize SQLite Sandbox if MySQL is not setup yet
if not st.session_state.db_initialized:
    try:
        init_database()
        seed_database()
        st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Failed to auto-initialize SQLite Sandbox: {e}")

# ==========================================
# 3. SIDEBAR CONFIGURATION
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/color/120/000000/supply-chain.png", width=65)
    st.title("SCM Agent Control")
    st.markdown("Configure SCM Multi-Agent network parameters and storage layers.")
    
    st.markdown("---")
    st.subheader("🔑 LLM Credentials")
    
    gemini_key_input = st.text_input(
        "Gemini API Key", 
        value=st.session_state.gemini_api_key, 
        type="password",
        help="Required for Gemini 2.5-flash agent modeling and AI executive summaries."
    )
    if gemini_key_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = gemini_key_input
        
    groq_key_input = st.text_input(
        "Groq API Key", 
        value=st.session_state.groq_api_key, 
        type="password",
        help="Required for Groq Mixtral speed-routing logic and text analysis."
    )
    if groq_key_input != st.session_state.groq_api_key:
        st.session_state.groq_api_key = groq_key_input
        
    st.session_state.routing_preference = st.selectbox(
        "Preferred AI Router",
        options=["gemini", "groq"],
        format_func=lambda x: "Google Gemini (Recommended)" if x == "gemini" else "Groq Mixtral Network"
    )
    
    st.markdown("---")
    st.subheader("💾 Database Selection")
    
    db_mode = st.radio(
        "Select Storage Layer",
        options=["MySQL Server", "Local SQLite Sandbox (Dev Mode)"],
        index=0 if not st.session_state.use_sqlite else 1
    )
    
    is_sqlite = (db_mode == "Local SQLite Sandbox (Dev Mode)")
    if is_sqlite != st.session_state.use_sqlite:
        st.session_state.use_sqlite = is_sqlite
        st.session_state.db_initialized = False
        st.rerun()
        
    if not st.session_state.use_sqlite:
        st.markdown("**MySQL Configuration Parameters:**")
        mysql_host = st.text_input("MySQL Host", value=st.session_state.mysql_host)
        mysql_port = st.text_input("MySQL Port", value=st.session_state.mysql_port)
        mysql_user = st.text_input("MySQL User", value=st.session_state.mysql_user)
        mysql_pass = st.text_input("MySQL Password", value=st.session_state.mysql_password, type="password")
        mysql_db = st.text_input("Database Name", value=st.session_state.mysql_database)
        
        # Save credentials in session state
        st.session_state.mysql_host = mysql_host
        st.session_state.mysql_port = mysql_port
        st.session_state.mysql_user = mysql_user
        st.session_state.mysql_password = mysql_pass
        st.session_state.mysql_database = mysql_db
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔌 Test Connection", use_container_width=True):
                success, msg = test_mysql_server(mysql_host, mysql_port, mysql_user, mysql_pass)
                if success:
                    st.success("Connection Successful!")
                else:
                    st.error(f"Connection Errored: {msg}")
        with col2:
            if st.button("🏗️ Initialize Schema", use_container_width=True):
                try:
                    init_database()
                    success, msg = seed_database()
                    if success:
                        st.success("MySQL schema seeded!")
                        st.session_state.db_initialized = True
                        st.rerun()
                    else:
                        st.error(msg)
                except Exception as e:
                    st.error(f"Init Error: {e}")
                    
    else:
        st.info("ℹ️ Running SQLite Sandbox database. It is self-contained and pre-seeded automatically.")
        if st.button("🔄 Reset SQLite Database", use_container_width=True):
            if os.path.exists("local_orders.db"):
                try:
                    os.remove("local_orders.db")
                except:
                    pass
            st.session_state.db_initialized = False
            st.rerun()
            
    st.markdown("---")
    st.caption("🌐 Built with LangGraph & Streamlit 1.45")

# ==========================================
# 4. HEADER DESIGN
# ==========================================
st.markdown("""
    <div class="header-container">
        <div class="header-title">🌐 Autonomous Supply Chain Intelligence Engine</div>
        <div class="header-subtitle">Multi-Agent SCM Orchestration System powered by LangGraph, Gemini & Groq</div>
    </div>
""", unsafe_allow_html=True)

# Connection diagnostics
api_status_cols = st.columns(3)
with api_status_cols[0]:
    if st.session_state.gemini_api_key:
        st.success("🟢 Gemini API Connection Enabled")
    else:
        st.warning("🟡 Gemini API Key is missing. Using Fallbacks.")
with api_status_cols[1]:
    if st.session_state.groq_api_key:
        st.success("🟢 Groq API Connection Enabled")
    else:
        st.warning("🟡 Groq API Key is missing. Using Fallbacks.")
with api_status_cols[2]:
    if st.session_state.use_sqlite:
        st.info("📦 Storage: SQLite Sandbox Active")
    else:
        try:
            conn = get_mysql_connection()
            conn.close()
            st.success(f"🟢 Storage: MySQL Connected ({st.session_state.mysql_database})")
        except:
            st.error("🔴 Storage: MySQL Connection Failed. Check credentials in sidebar.")

# ==========================================
# 5. MAIN NAVIGATION TABS
# ==========================================
tab_control, tab_audit, tab_report = st.tabs([
    "📈 SCM Control Center", 
    "🛡️ Decision Audit Trail Logs", 
    "📄 Executive AI Analytics Report"
])

# -----------------
# TAB 1: SCM CONTROL CENTER
# -----------------
with tab_control:
    st.markdown("### 🔍 Customer Order Profiler")
    
    # Customer Search
    col_search, col_suggest = st.columns([2, 3])
    with col_search:
        cust_id_input = st.text_input(
            "Enter Customer ID:", 
            value="CUST-1001",
            placeholder="e.g. CUST-1001",
            help="Input a customer ID to load their profiles and active orders."
        )
    with col_suggest:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        st.markdown("**Sample Customer Guides:** `CUST-1001` (VIP) | `CUST-1002` (Premium) | `CUST-1003` (Standard) | `CUST-1004` (VIP)")

    if cust_id_input:
        customer = get_customer(cust_id_input)
        if customer:
            st.session_state.selected_customer = customer
            
            # Display Customer Profile Card
            st.markdown(f"""
                <div class="scm-card">
                    <div class="scm-card-title">👤 Customer Profile: {customer['name']}</div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 0.5rem;">
                        <div><strong>Customer ID:</strong> {customer['customer_id']}</div>
                        <div><strong>Company:</strong> {customer['company']}</div>
                        <div><strong>Email:</strong> {customer['email']}</div>
                        <div><strong>SLA Tier:</strong> <span class="badge badge-{customer['tier'].lower()}">{customer['tier']}</span></div>
                    </div>
                    <div style="margin-top: 0.75rem;"><strong>Primary Shipping Address:</strong> {customer['address']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Fetch orders
            orders = get_orders_by_customer(customer['customer_id'])
            
            col_orders, col_simulator = st.columns([1, 1])
            
            with col_orders:
                st.markdown("#### 📦 Order Logistics Book")
                if orders:
                    formatted_orders = []
                    for o in orders:
                        status_badge = ""
                        if o['status'] in ["Fulfilled", "Delivered"]:
                            status_badge = f"🟢 {o['status']}"
                        elif o['status'] in ["Rerouted", "Processing"]:
                            status_badge = f"🟡 {o['status']}"
                        else:
                            status_badge = f"🔴 {o['status']}"
                        
                        formatted_orders.append({
                            "Order ID": o['order_id'],
                            "Product Name": o['product_name'],
                            "Qty": o['quantity'],
                            "Total Value": f"${float(o['total_price']):,.2f}",
                            "SLA Status": status_badge,
                            "Order Date": o['order_date']
                        })
                    st.dataframe(formatted_orders, use_container_width=True, hide_index=True)
                else:
                    st.warning("No orders found for this customer.")
                
                # Order booking form
                st.markdown("#### ➕ Create New Ship Order")
                with st.form("new_order_form"):
                    prod_name = st.selectbox(
                        "Select Product Item",
                        ["Enterprise Server Array Model X", "IoT Temperature Sensor Hubs", "Robotic Sorting Arms", "Multi-Gigabit Router Units"]
                    )
                    qty = st.number_input("Order Quantity", min_value=1, max_value=5000, value=10)
                    price_map = {
                        "Enterprise Server Array Model X": 15000.00,
                        "IoT Temperature Sensor Hubs": 30.00,
                        "Robotic Sorting Arms": 24000.00,
                        "Multi-Gigabit Router Units": 900.00
                    }
                    unit_price = price_map[prod_name]
                    total_price = unit_price * qty
                    
                    st.markdown(f"**Unit Price:** ${unit_price:,.2f} | **Total Order Est. Cost:** ${total_price:,.2f}")
                    
                    submitted = st.form_submit_button("🛒 Submit & Book Logistics Order")
                    if submitted:
                        new_ord_id = f"ORD-{int(time.time()) % 100000}"
                        insert_new_order(new_ord_id, customer['customer_id'], prod_name, qty, total_price)
                        st.success(f"Order {new_ord_id} successfully saved to DB. Ready for SCM Agent evaluation!")
                        time.sleep(0.5)
                        st.rerun()
            
            with col_simulator:
                st.markdown("#### ⚙️ Agentic SCM Runner")
                st.markdown("Configure agentic variables to test system resiliency during port or logistics delays.")
                
                order_options = [o['order_id'] for o in orders if o['status'] != "Fulfilled"]
                all_order_options = [o['order_id'] for o in orders]
                
                if not order_options:
                    order_options = all_order_options
                
                if order_options:
                    selected_order_id = st.selectbox("Select Order ID for AI Assessment:", options=order_options)
                    simulate_disruption = st.checkbox(
                        "💥 Simulate External Port Congestion (SLA Risk)", 
                        value=False,
                        help="Check this to simulate a carrier rejection / port overcapacity event. This triggers the agent's self-correcting routing loop!"
                    )
                    
                    if st.button("🚀 Execute Multi-Agent Workflow", type="primary", use_container_width=True):
                        # Initialize states
                        initial_state: SCMState = {
                            "order_id": selected_order_id,
                            "customer_id": customer['customer_id'],
                            "customer_tier": customer['tier'],
                            "current_phase": "Initializing",
                            "inventory_status": "Checking",
                            "route_selected": "Pending Evaluation",
                            "carrier_status": "Standby",
                            "optimization_cycles": 0,
                            "detected_disruptions": ["Severe Port Congestion (LA Port Terminal overload)"] if simulate_disruption else [],
                            "audit_trail": [],
                            "status": "Processing",
                            "requires_correction": False,
                            "simulate_disruption": simulate_disruption,
                            "cost_savings": "$0.00 (Calculating...)",
                            "live_location": "System Initiation",
                            "agent_thoughts": {}
                        }
                        
                        st.markdown("#### 🟢 Active Agent Operations Panel")
                        timeline_placeholder = st.empty()
                        metrics_placeholder = st.empty()
                        
                        with st.spinner("Agentic SCM Workflow processing..."):
                            st.session_state.workflow_history = []
                            current_state = dict(initial_state)
                            
                            # Stream from compiled LangGraph StateGraph
                            for event in scm_workflow_graph.stream(initial_state):
                                for node_name, state_updates in event.items():
                                    current_state.update(state_updates)
                                    
                                    # Select details for ledger logging
                                    agent_display_name = ""
                                    phase_name = current_state["current_phase"]
                                    action_text = ""
                                    model_used = "Deterministic Engine"
                                    
                                    if node_name == "ui_agent":
                                        agent_display_name = "UI (Customer Layer)"
                                        action_text = current_state["agent_thoughts"].get("ui_agent", "")
                                    elif node_name == "intelligence_agent":
                                        agent_display_name = "Supply Chain Intelligence"
                                        action_text = current_state["agent_thoughts"].get("intelligence_agent", "")
                                        _, model_used = get_llm_client(prefer=st.session_state.routing_preference)
                                        if not current_state["detected_disruptions"]:
                                            model_used = "Deterministic Engine"
                                    elif node_name == "compliance_agent":
                                        agent_display_name = "Verification & Compliance"
                                        action_text = current_state["agent_thoughts"].get("compliance_agent", "")
                                        model_used = "Regulatory Sandbox Ruleset"
                                    elif node_name == "orchestration_agent":
                                        agent_display_name = "Process Orchestration"
                                        action_text = current_state["agent_thoughts"].get("orchestration_agent", "")
                                        model_used = "Graph Node Algorithm"
                                        if current_state["optimization_cycles"] > 0:
                                            phase_name += " (Correction)"
                                    elif node_name == "external_entities":
                                        agent_display_name = "External Entities Node"
                                        action_text = current_state["agent_thoughts"].get("external_entities", "")
                                        model_used = "Supply Chain Sim Port Engine"
                                        if current_state["optimization_cycles"] > 0 and current_state["carrier_status"] != "Booking Rejected (Port Overcapacity/Strike)":
                                            phase_name += " (Final Booking)"
                                            
                                    # Log each agent node execution to DB
                                    save_order_history_record(
                                        current_state["order_id"],
                                        phase_name,
                                        agent_display_name,
                                        action_text,
                                        model_used,
                                        current_state["cost_savings"],
                                        current_state["live_location"]
                                    )
                                    
                                    # Append state for UI timeline rendering
                                    st.session_state.workflow_history.append(dict(current_state))
                                    timeline_placeholder.markdown(render_timeline_html(st.session_state.workflow_history), unsafe_allow_html=True)
                                    metrics_placeholder.markdown(render_metrics_html(current_state), unsafe_allow_html=True)
                                    
                                    # Add custom visual delays between agent steps
                                    if node_name == "ui_agent":
                                        time.sleep(0.8)
                                    elif node_name == "intelligence_agent":
                                        time.sleep(1.0)
                                    elif node_name == "compliance_agent":
                                        time.sleep(0.6)
                                    elif node_name == "orchestration_agent":
                                        time.sleep(0.8)
                                    elif node_name == "external_entities":
                                        if current_state["carrier_status"] == "Booking Rejected (Port Overcapacity/Strike)":
                                            st.warning("🔄 Disruption Event Detected: Loopback Self-Correction Protocol Triggered!")
                                        time.sleep(0.8)
                                        
                            update_order_status(current_state["order_id"], current_state["status"])
                            
                        st.success(f"SCM Workflow assessment complete for Order {selected_order_id}!")
                        
                        # Render metrics and timeline
                        metrics_placeholder.markdown(render_metrics_html(current_state), unsafe_allow_html=True)
                        timeline_placeholder.markdown(render_timeline_html(st.session_state.workflow_history), unsafe_allow_html=True)
                        
                else:
                    st.info("No orders currently active. Create an order above to test.")
        else:
            st.error(f"❌ Customer ID '{cust_id_input}' not found in the database.")
            st.markdown("### 👤 Register New SCM Customer")
            st.markdown("Complete the form below to add this customer to the database.")
            
            with st.form("register_customer_form"):
                reg_cust_id = st.text_input("Customer ID", value=cust_id_input, disabled=True)
                reg_name = st.text_input("Full Name", placeholder="e.g. John Doe")
                reg_company = st.text_input("Company Name", placeholder="e.g. Apex Industries")
                reg_email = st.text_input("Email Address", placeholder="e.g. john@apex.com")
                reg_address = st.text_area("Primary Shipping Address", placeholder="e.g. 100 Main St, Austin, TX 78701")
                reg_tier = st.selectbox("SLA Priority Tier", ["VIP", "Premium", "Standard"])
                
                submitted_reg = st.form_submit_button("💾 Register & Save Customer")
                if submitted_reg:
                    if not reg_name or not reg_address:
                        st.error("Please fill in the Full Name and Shipping Address fields.")
                    else:
                        success, msg = insert_new_customer(cust_id_input, reg_name, reg_email, reg_company, reg_address, reg_tier)
                        if success:
                            st.success(msg)
                            time.sleep(1.0)
                            st.rerun()
                        else:
                            st.error(msg)

# -----------------
# TAB 2: DECISION AUDIT TRAIL LOGS
# -----------------
with tab_audit:
    st.markdown("### 🛡️ Immutable SCM Ledger Audit Trail")
    st.markdown("Every node decision, safety guard assessment, and external status update is securely recorded to the MySQL database engine.")
    
    col_audit_opt, _ = st.columns([2, 3])
    with col_audit_opt:
        search_filter = st.text_input("Filter logs by Order ID / Agent Name:", placeholder="e.g. ORD-5003")
        
    logs = get_all_order_history()
    
    if logs:
        filtered_logs = []
        for l in logs:
            if search_filter:
                match_str = f"{l['order_id']} {l['agent_name']} {l['phase']} {l['action']}".lower()
                if search_filter.lower() not in match_str:
                    continue
            filtered_logs.append({
                "Timestamp": l['timestamp'],
                "Order ID": l['order_id'],
                "Phase": l['phase'],
                "Agent Name": l['agent_name'],
                "Model Used": l['model_used'],
                "Carrier Location": l['live_location'],
                "Dynamic Savings": l['cost_savings'],
                "Agent Core Action & Details": l['action']
            })
            
        if filtered_logs:
            st.dataframe(filtered_logs, use_container_width=True, hide_index=True)
        else:
            st.info("No logs match the search query.")
    else:
        st.warning("Decision ledger is currently empty. Run SCM simulation cycles to generate logs.")

# -----------------
# TAB 3: EXECUTIVE AI ANALYTICS REPORT
# -----------------
with tab_report:
    st.markdown("### 📄 Executive Supply Chain SCM AI Report")
    st.markdown("Generate a high-fidelity intelligence report analyzing recent shipping logs, disruption histories, and route optimizations for the selected customer.")
    
    if st.session_state.selected_customer:
        customer = st.session_state.selected_customer
        saved_report = get_last_ai_report(customer['customer_id'])
        
        col_rep_btn, col_rep_info = st.columns([1, 2])
        with col_rep_btn:
            if st.button("🧠 Generate Executive AI Summary", type="primary", use_container_width=True):
                # Fetch customer orders & log history
                cust_orders = get_orders_by_customer(customer['customer_id'])
                all_logs = []
                for o in cust_orders:
                    all_logs.extend(get_order_history(o['order_id']))
                
                order_summary_str = ""
                for o in cust_orders:
                    order_summary_str += f"- Order {o['order_id']}: Product={o['product_name']}, Qty={o['quantity']}, Value=${o['total_price']}, Status={o['status']}\n"
                    
                logs_summary_str = ""
                for l in all_logs[:15]:
                    logs_summary_str += f"- [{l['timestamp']}] Order {l['order_id']} | Agent: {l['agent_name']} | Action: {l['action']} | Location: {l['live_location']} | Savings: {l['cost_savings']} | Model: {l['model_used']}\n"
                
                model, model_name = get_llm_client(prefer=st.session_state.routing_preference)
                if model:
                    with st.spinner("Compiling database records and generating analysis report..."):
                        try:
                            prompt = f"""
                            You are the Director of Autonomous SCM Analytics. Generate an executive Supply Chain Health & Resiliency Report for the following customer.
                            
                            ### CUSTOMER PROFILE
                            - Name: {customer['name']}
                            - Company: {customer['company']}
                            - Tier: {customer['tier']}
                            - Address: {customer['address']}
                            
                            ### ACTIVE & PAST ORDERS
                            {order_summary_str}
                            
                            ### LOGISTICS AUDIT TRAIL LOGS
                            {logs_summary_str}
                            
                            ### REPORT REQUIREMENT INSTRUCTIONS:
                            Write a highly professional, elegant and comprehensive Supply Chain Performance Report in markdown format. Use bullet points and clean structure:
                            1. **Executive Operational Summary**: SCM health evaluation and overall reliability index (e.g. 98%).
                            2. **Risk & Sourcing Vulnerability Assessment**: Highlight recent disruption events (like port congestion), and how agents resolved them autonomously.
                            3. **Cost-Savings & Return-On-Investment (ROI)**: Quantify accumulated savings from dynamic rerouting, carriers volume discount, and SLA penalty avoidance.
                            4. **Strategic Recommendations**: Provide actionable next-quarter sourcing recommendations based on customer tier rules and global trade forecasts.
                            
                            Maintain an extremely polished corporate tone. Do not use conversational filler.
                            """
                            response = model.invoke(prompt)
                            report_content = str(response.content)
                            
                            save_ai_report(customer['customer_id'], report_content, model_name)
                            st.success("Executive AI Report compiled and saved to database!")
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Report generation errored: {e}")
                else:
                    st.error("❌ No LLM API connection active. Please input a Gemini or Groq API Key in the sidebar to enable AI Report generation.")
                    
        with col_rep_info:
            if saved_report:
                st.markdown(f"**Last Compiled:** `{saved_report['created_at']}` | **Model Engine:** `{saved_report['model_used']}`")
            else:
                st.info("No report exists in database for this customer yet. Click the button to compile one.")
                
        st.markdown("---")
        
        if saved_report:
            st.markdown(f"""
                <div style="background-color: #0F172A; border: 1px solid #1E293B; border-radius: 12px; padding: 2rem; margin-top: 1rem; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.2);">
                    {saved_report['report_text']}
                </div>
            """, unsafe_allow_html=True)
            
            st.download_button(
                label="📥 Download Report as Markdown Text",
                data=saved_report['report_text'],
                file_name=f"SCM_Executive_Report_{customer['customer_id']}.md",
                mime="text/markdown",
                use_container_width=True
            )
    else:
        st.warning("Select or search a valid Customer ID on the Control Center tab first.")
