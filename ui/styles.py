# CSS Styles for SCM Agentic Workflow (Premium Default Dark Theme)

DARK_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Overall Page Theming */
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', sans-serif;
        background-color: #0B0F19 !important;
        color: #E2E8F0 !important;
    }
    
    /* Header/Top Bar adjustment */
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* Sidebar styling: Dark slate with a subtle right-border */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090D16 0%, #0F172A 100%) !important;
        color: #94A3B8 !important;
        border-right: 1px solid #1E293B !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #1E293B !important;
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #94A3B8 !important;
    }
    
    /* Input inputs styling in Sidebar */
    .stTextInput>div>div>input {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    .stTextInput>div>div>input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 1px #3B82F6 !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        color: #F8FAFC !important;
        font-weight: 600 !important;
    }
    
    /* Hero/Header Banner */
    .header-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #1D4ED8 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 16px;
        border: 1px solid #2563EB;
        box-shadow: 0 10px 30px -10px rgba(37, 99, 235, 0.4);
        margin-bottom: 2rem;
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
        background: linear-gradient(to right, #FFFFFF, #93C5FD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .header-subtitle {
        font-size: 1.1rem;
        font-weight: 300;
        opacity: 0.9;
        color: #93C5FD;
    }
    
    /* Custom Premium Glassmorphic Cards */
    .scm-card {
        background-color: #0F172A !important;
        border: 1px solid #1E293B !important;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 1.25rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .scm-card:hover {
        border-color: #2563EB !important;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.2);
        transform: translateY(-2px);
    }
    .scm-card-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #F8FAFC;
        margin-bottom: 0.75rem;
        border-bottom: 1px solid #1E293B;
        padding-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Custom Metric Tiles */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-tile {
        background: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 1.25rem;
        text-align: center;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    .metric-tile:hover {
        background: #1E293B;
        border-color: #3B82F6;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #3B82F6;
        margin-bottom: 0.25rem;
        letter-spacing: -0.01em;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94A3B8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Vertical Timeline/Step visualizer */
    .timeline-container {
        position: relative;
        padding-left: 2rem;
        border-left: 2px solid #1E293B;
        margin-left: 1rem;
        margin-top: 1.5rem;
    }
    .timeline-item {
        position: relative;
        margin-bottom: 2.25rem;
    }
    .timeline-item::before {
        content: '';
        position: absolute;
        left: -2.62rem;
        top: 0.2rem;
        width: 1.2rem;
        height: 1.2rem;
        border-radius: 50%;
        background-color: #1E293B;
        border: 3px solid #0B0F19;
        box-shadow: 0 0 0 1px #334155;
    }
    .timeline-item.active::before {
        background-color: #10B981;
        box-shadow: 0 0 10px 2px rgba(16, 185, 129, 0.4);
        animation: pulse-glow 1.5s infinite;
    }
    .timeline-item.completed::before {
        background-color: #3B82F6;
        box-shadow: 0 0 0 1px #3B82F6;
    }
    .timeline-item.failed::before {
        background-color: #EF4444;
        box-shadow: 0 0 8px 1px rgba(239, 68, 68, 0.4);
    }
    .timeline-title {
        font-weight: 600;
        color: #F8FAFC;
        font-size: 1.05rem;
    }
    .timeline-meta {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 0.15rem;
        margin-bottom: 0.5rem;
        display: flex;
        gap: 1rem;
    }
    .timeline-content {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 0.85rem 1.2rem;
        font-size: 0.9rem;
        color: #CBD5E1;
        line-height: 1.55;
    }
    
    @keyframes pulse-glow {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.15); opacity: 0.8; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Styled badges */
    .badge {
        padding: 0.25rem 0.6rem;
        font-size: 0.72rem;
        font-weight: 600;
        border-radius: 9999px;
        text-transform: uppercase;
        display: inline-block;
    }
    .badge-vip { background-color: #450A0A; color: #FCA5A5; border: 1px solid #991B1B; }
    .badge-premium { background-color: #451A03; color: #FCD34D; border: 1px solid #92400E; }
    .badge-standard { background-color: #0C4A6E; color: #7DD3FC; border: 1px solid #0369A1; }
    .badge-success { background-color: #064E3B; color: #6EE7B7; border: 1px solid #065F46; }
    .badge-warning { background-color: #451A03; color: #FCD34D; border: 1px solid #92400E; }
    .badge-error { background-color: #450A0A; color: #FCA5A5; border: 1px solid #991B1B; }
    .badge-info { background-color: #0C4A6E; color: #7DD3FC; border: 1px solid #0369A1; }
    
    /* Streamlit widgets overrides to match dark mode */
    .stForm {
        background-color: #0F172A !important;
        border: 1px solid #1E293B !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
    }
    .stDataFrame {
        border: 1px solid #1E293B !important;
        border-radius: 10px !important;
        background-color: #0F172A !important;
    }
    
    /* Buttons styling */
    .stButton>button {
        background-color: #1E3A8A !important;
        color: #F8FAFC !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        background-color: #2563EB !important;
        border-color: #60A5FA !important;
        box-shadow: 0 0 10px 0 rgba(59, 130, 246, 0.4) !important;
    }
</style>
"""

def render_timeline_html(history):
    if not history:
        return "<div class='timeline-container'><div class='timeline-item'><div class='timeline-title'>No active history records</div></div></div>"
    timeline_html = "<div class='timeline-container'>"
    for idx, step in enumerate(history):
        if not isinstance(step, dict):
            continue
        is_last = (idx == len(history) - 1)
        carrier_status = step.get("carrier_status", "")
        live_loc = step.get("live_location", "Origin Point")
        current_phase = step.get("current_phase", "Processing Phase")
        agent_thoughts = step.get("agent_thoughts", {})
        if not isinstance(agent_thoughts, dict):
            agent_thoughts = {}
        
        # Select timeline classes
        if is_last:
            status_class = "active"
        elif carrier_status == "Booking Rejected (Port Overcapacity/Strike)":
            status_class = "failed"
        else:
            status_class = "completed"
            
        agent_name = ""
        thought = ""
        
        # Fetch appropriate thoughts
        if idx == 0:
            agent_name = "👤 User Interface / Order Intake Agent"
            thought = agent_thoughts.get("ui_agent", "")
        elif idx == 1:
            agent_name = "🧠 Supply Chain Intelligence Agent"
            thought = agent_thoughts.get("intelligence_agent", "")
        elif idx == 2:
            agent_name = "🛡️ Verification & Compliance Agent"
            thought = agent_thoughts.get("compliance_agent", "")
        elif idx == 3:
            agent_name = "⚙️ Process Orchestration Agent"
            thought = agent_thoughts.get("orchestration_agent", "")
        elif idx == 4:
            agent_name = "🚢 External Entities / Carrier Logistics Node"
            thought = agent_thoughts.get("external_entities", "")
        elif idx == 5:
            agent_name = "🔄 Process Orchestration (Dynamic Route Correction)"
            thought = agent_thoughts.get("orchestration_agent", "")
        elif idx == 6:
            agent_name = "🚢 External Carrier Logistics (Rerouted Gate Confirmed)"
            thought = agent_thoughts.get("external_entities", "")
        else:
            agent_name = f"SCM Node ({current_phase})"
            thought = "Processing SCM state parameters."
            
        badge_color = "success" if ("Delivered" in live_loc or "Intake" in live_loc) else "warning"
        if "Congested" in live_loc or "Quarantine" in live_loc or "Rejected" in live_loc:
            badge_color = "error"
            
        formatted_thought = thought.replace('\n', '<br>')
        
        timeline_html += f"""
            <div class="timeline-item {status_class}">
                <div class="timeline-title">{agent_name}</div>
                <div class="timeline-meta">
                    <span>📍 Location: <span class="badge badge-{badge_color}">{live_loc}</span></span>
                    <span>🔑 Routing Node: {current_phase}</span>
                </div>
                <div class="timeline-content">{formatted_thought}</div>
            </div>
        """
    timeline_html += "</div>"
    return timeline_html

def render_metrics_html(state):
    if not isinstance(state, dict):
        state = {}
    status_label = state.get('status', 'Standby')
    savings = state.get('cost_savings', '$0.00')
    cycles = state.get('optimization_cycles', 0)
    sla_risk = "< 0.1%" if status_label == "Execution Fulfilled" else ("100%" if status_label == "Security Exception" else "Moderate")
    
    metrics_html = f"""
        <div class="metric-grid">
            <div class="metric-tile">
                <div class="metric-value">{status_label}</div>
                <div class="metric-label">Execution Status</div>
            </div>
            <div class="metric-tile">
                <div class="metric-value">{savings}</div>
                <div class="metric-label">Operational Savings</div>
            </div>
            <div class="metric-tile">
                <div class="metric-value">{cycles}</div>
                <div class="metric-label">Rerouting Cycles</div>
            </div>
            <div class="metric-tile">
                <div class="metric-value">{sla_risk}</div>
                <div class="metric-label">SLA Breach Risk</div>
            </div>
        </div>
    """
    return metrics_html

