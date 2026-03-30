import os
from typing import TypedDict, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.graph import StateGraph
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# ============= LLM Initialization =============
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
except Exception as e:
    print(f"⚠️ Warning: LLM initialization failed: {e}")
    llm = None

# ============= FastAPI Setup =============
app = FastAPI(
    title="SCM Agentic Workflow API",
    version="1.0.0",
    description="AI-powered Supply Chain Management with LangGraph"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
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
    """UI Agent: Initiate order placement and validation."""
    state["current_phase"] = "Planning"
    state["audit_trail"].append({
        "timestamp": "now",
        "agent": "UI",
        "action": f"Order {state['order_id']} received and validated"
    })
    return state

def supply_chain_intelligence_agent(state: SCMState) -> SCMState:
    """Intelligence Agent: AI-powered analysis of supply chain disruptions."""
    disruptions = state.get("detected_disruptions", [])
    
    if disruptions and llm:
        try:
            prompt = (
                f"Analyze these supply chain disruptions and provide brief mitigation: "
                f"{', '.join(disruptions)}"
            )
            response = llm.invoke(prompt)
            analysis = response.content if response else "Standard protocol applied"
        except Exception as e:
            analysis = f"LLM unavailable - applying standard protocols ({str(e)[:30]})"
    else:
        analysis = "System operating normally - no disruptions detected"
    
    state["audit_trail"].append({
        "timestamp": "now",
        "agent": "Intelligence",
        "action": f"Analysis: {analysis[:150]}"
    })
    
    if disruptions:
        state["requires_correction"] = True
    
    return state

def orchestration_agent(state: SCMState) -> SCMState:
    """Orchestration Agent: Workflow execution and routing logic."""
    state["current_phase"] = "Execution"
    
    if state["requires_correction"]:
        state["status"] = "Disruption Handling Active"
        state["inventory_status"] = "Rerouting"
        state["audit_trail"].append({
            "timestamp": "now",
            "agent": "Orchestration",
            "action": "Disruption detected: Rerouting via alternative carrier"
        })
    else:
        state["status"] = "Order Processing"
        state["inventory_status"] = "Updated"
        state["audit_trail"].append({
            "timestamp": "now",
            "agent": "Orchestration",
            "action": "Standard delivery route selected"
        })
    
    return state

def compliance_agent(state: SCMState) -> SCMState:
    """Compliance Agent: Regulatory and compliance verification."""
    state["current_phase"] = "Compliance"
    state["audit_trail"].append({
        "timestamp": "now",
        "agent": "Compliance",
        "action": "Order validated - regulatory and compliance checks passed"
    })
    
    # Clear correction flag after compliance check
    state["requires_correction"] = False
    state["status"] = "Order Fulfilled"
    
    return state

# ============= LangGraph Workflow =============

def create_workflow():
    """Build the LangGraph state machine workflow."""
    workflow = StateGraph(SCMState)
    
    # Add nodes
    workflow.add_node("ui_agent", user_interface_agent)
    workflow.add_node("intelligence_agent", supply_chain_intelligence_agent)
    workflow.add_node("orchestration_agent", orchestration_agent)
    workflow.add_node("compliance_agent", compliance_agent)
    
    # Add edges (linear flow)
    workflow.set_entry_point("ui_agent")
    workflow.add_edge("ui_agent", "intelligence_agent")
    workflow.add_edge("intelligence_agent", "orchestration_agent")
    workflow.add_edge("orchestration_agent", "compliance_agent")
    workflow.set_finish_point("compliance_agent")
    
    return workflow.compile()

# Compile workflow once
workflow = create_workflow()

# ============= API Endpoints =============

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SCM Agentic Workflow API",
        "llm_available": llm is not None
    }

@app.post("/api/place_order")
async def place_order(request: OrderRequest):
    """Execute supply chain workflow for an order."""
    try:
        # Initialize workflow state
        initial_state: SCMState = {
            "order_id": request.order_id,
            "current_phase": "Initializing",
            "inventory_status": "Checking",
            "detected_disruptions": (
                ["Supplier delay", "Port congestion"] 
                if request.simulate_disruption 
                else []
            ),
            "audit_trail": [],
            "status": "Processing",
            "requires_correction": False,
            "simulate_disruption": request.simulate_disruption
        }
        
        # Execute workflow
        final_state = workflow.invoke(initial_state)
        
        return {
            "success": True,
            "order_id": final_state["order_id"],
            "state": {
                "status": final_state["status"],
                "current_phase": final_state["current_phase"],
                "inventory_status": final_state["inventory_status"],
                "detected_disruptions": final_state["detected_disruptions"],
                "audit_trail": final_state["audit_trail"]
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "order_id": request.order_id,
            "state": {
                "status": "Error",
                "current_phase": "Error",
                "inventory_status": "Unknown",
                "detected_disruptions": [str(e)],
                "audit_trail": [
                    {
                        "timestamp": "now",
                        "agent": "System",
                        "action": f"Error occurred: {str(e)}"
                    }
                ]
            }
        }

@app.get("/api/workflows")
def list_workflows():
    """List available supply chain workflows."""
    return {
        "workflows": [
            {
                "name": "Supply Chain Management Workflow",
                "description": "AI-powered autonomous workflow with order processing, disruption detection, and compliance",
                "agents": ["UI", "Intelligence", "Orchestration", "Compliance"],
                "status": "active"
            }
        ]
    }

@app.get("/api/system/health")
def system_health():
    """Get detailed system health information."""
    return {
        "system": "SCM Agentic Workflow",
        "status": "operational",
        "components": {
            "api": "healthy",
            "workflow_engine": "healthy",
            "llm": "available" if llm else "unavailable"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
