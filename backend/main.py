import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import TypedDict, List
from langgraph.graph import StateGraph
from langgraph.graph.graph import START, END
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize LLM (optional - graceful fallback)
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        google_api_key=os.getenv("GEMINI_API_KEY", "")
    )
except:
    llm = None

# ============= FastAPI Setup =============
app = FastAPI(
    title="SCM Agentic Workflow API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= Data Models =============
class OrderRequest(BaseModel):
    order_id: str
    simulate_disruption: bool = False

class SCMState(TypedDict):
    order_id: str
    current_phase: str
    inventory_status: str
    detected_disruptions: List[str]
    audit_trail: List[dict]
    status: str
    requires_correction: bool
    simulate_disruption: bool

# ============= Agent Nodes =============

def user_interface_agent(state: SCMState) -> SCMState:
    """Initiate order placement."""
    state["current_phase"] = "Planning"
    state["audit_trail"].append({
        "agent": "UI",
        "action": f"Order {state['order_id']} received"
    })
    return state

def supply_chain_intelligence_agent(state: SCMState) -> SCMState:
    """AI-powered intelligence analysis."""
    disruptions = state.get("detected_disruptions", [])
    
    analysis = "System operating normally"
    if disruptions and llm:
        try:
            prompt = f"Analyze these supply chain disruptions: {', '.join(disruptions)}. Provide brief mitigation."
            response = llm.invoke(prompt)
            analysis = response.content if response else "Standard protocol"
        except:
            analysis = "LLM unavailable - applying standard protocols"
    
    state["audit_trail"].append({
        "agent": "Intelligence",
        "action": f"Analysis: {analysis[:100]}"
    })
    
    if disruptions:
        state["requires_correction"] = True
    
    return state

def orchestration_agent(state: SCMState) -> SCMState:
    """Workflow orchestration and execution."""
    state["current_phase"] = "Execution"
    
    if state["requires_correction"]:
        state["status"] = "Disruption Handling"
        state["audit_trail"].append({
            "agent": "Orchestration",
            "action": "Rerouting via alternative carrier"
        })
    else:
        state["status"] = "Order Processing"
        state["inventory_status"] = "Updated"
        state["audit_trail"].append({
            "agent": "Orchestration",
            "action": "Standard route selected"
        })
    
    return state

def compliance_agent(state: SCMState) -> SCMState:
    """Compliance verification."""
    state["current_phase"] = "Compliance"
    state["audit_trail"].append({
        "agent": "Compliance",
        "action": "Order validated - regulatory compliant"
    })
    
    if state["requires_correction"]:
        state["requires_correction"] = False
    
    state["status"] = "Order Fulfilled"
    
    return state

# ============= LangGraph Workflow =============

def create_workflow():
    """Build the LangGraph workflow."""
    workflow = StateGraph(SCMState)
    
    # Add nodes
    workflow.add_node("ui_agent", user_interface_agent)
    workflow.add_node("intelligence_agent", supply_chain_intelligence_agent)
    workflow.add_node("orchestration_agent", orchestration_agent)
    workflow.add_node("compliance_agent", compliance_agent)
    
    # Add edges
    workflow.add_edge(START, "ui_agent")
    workflow.add_edge("ui_agent", "intelligence_agent")
    workflow.add_edge("intelligence_agent", "orchestration_agent")
    workflow.add_edge("orchestration_agent", "compliance_agent")
    workflow.add_edge("compliance_agent", END)
    
    return workflow.compile()

workflow = create_workflow()

# ============= API Endpoints =============

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "SCM API"}

@app.post("/api/place_order")
async def place_order(request: OrderRequest):
    """Execute order workflow."""
    try:
        # Initialize state
        initial_state: SCMState = {
            "order_id": request.order_id,
            "current_phase": "Initializing",
            "inventory_status": "Checking",
            "detected_disruptions": ["Supplier delay"] if request.simulate_disruption else [],
            "audit_trail": [],
            "status": "Processing",
            "requires_correction": False,
            "simulate_disruption": request.simulate_disruption
        }
        
        # Run workflow
        final_state = workflow.invoke(initial_state)
        
        return {
            "order_id": final_state["order_id"],
            "state": {
                "status": final_state["status"],
                "current_phase": final_state["current_phase"],
                "detected_disruptions": final_state["detected_disruptions"],
                "audit_trail": final_state["audit_trail"]
            }
        }
    
    except Exception as e:
        return {
            "order_id": request.order_id,
            "state": {
                "status": "Error",
                "current_phase": "Error",
                "detected_disruptions": [str(e)],
                "audit_trail": [{"agent": "System", "action": f"Error: {str(e)}"}]
            }
        }

@app.get("/api/workflows")
def list_workflows():
    """List available workflows."""
    return {
        "workflows": [{
            "name": "Supply Chain Workflow",
            "agents": ["UI", "Intelligence", "Orchestration", "Compliance"]
        }]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
