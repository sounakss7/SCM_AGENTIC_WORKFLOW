import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import TypedDict, List
from langgraph.graph import StateGraph
from langgraph.graph.graph import START, END
from dotenv import load_dotenv

# --- NEW: Import LangChain Google GenAI ---
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from the .env file
load_dotenv()

# Initialize the Gemini LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, google_api_key=os.getenv("GEMINI_API_KEY"))

# 1. Initialize FastAPI and CORS
app = FastAPI(title="Agentic SCM Workflow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Update the Shared State 
class SCMState(TypedDict):
    order_id: str
    current_phase: str
    inventory_status: str
    detected_disruptions: List[str]
    audit_trail: List[dict]
    status: str
    requires_correction: bool 

# 3. Agent Nodes
def user_interface_agent(state: SCMState):
    state["current_phase"] = "Planning"
    state["audit_trail"].append({"agent": "UI", "action": "Order Received"})
    return state

# --- NEW: LLM-Powered Intelligence Agent ---
def supply_chain_intelligence_agent(state: SCMState):
    disruptions = state.get("detected_disruptions", [])
    
    if disruptions:
        # Ask Gemini to analyze the situation
        prompt = f"""
        You are a Supply Chain Intelligence Agent. 
        An order ({state['order_id']}) is facing these disruptions: {disruptions}.
        Does this require a routing correction or alternative supplier? 
        Answer with EXACTLY 'YES' or 'NO', followed by a one-sentence justification.
        """
        
        response = llm.invoke(prompt)
        llm_decision = response.content.strip()
        
        # Parse the LLM's response to drive the LangGraph routing
        if llm_decision.upper().startswith("YES"):
            state["requires_correction"] = True
            action_log = f"CRITICAL ALERT analyzed by Gemini: {llm_decision}"
        else:
            state["requires_correction"] = False
            action_log = f"Disruption analyzed by Gemini (No action needed): {llm_decision}"
            
        state["audit_trail"].append({"agent": "Intelligence", "action": action_log})
        
    else:
        state["requires_correction"] = False
        state["audit_trail"].append({
            "agent": "Intelligence", 
            "action": "Demand Analyzed. No disruptions detected. Route clear."
        })
        
    return state

def autonomous_correction_protocol(state: SCMState):
    state["current_phase"] = "Monitoring & Optimization"
    state["status"] = "Executing Self-Correction"
    state["audit_trail"].append({
        "agent": "Orchestration", 
        "action": "Autonomous Rerouting Initiated based on Intelligence report. Selected alternative carrier."
    })
    state["requires_correction"] = False 
    return state

def process_orchestration_agent(state: SCMState):
    state["current_phase"] = "Execution"
    state["audit_trail"].append({"agent": "Orchestration", "action": "Standard Route & Carrier Selected"})
    return state

def verification_compliance_agent(state: SCMState):
    state["audit_trail"].append({"agent": "Compliance", "action": "Regulatory checks passed."})
    return state

def external_entities_agent(state: SCMState):
    state["status"] = "Order Fulfilled"
    return state

# 4. The Routing Function for LangGraph
def route_disruptions(state: SCMState):
    if state.get("requires_correction"):
        return "needs_correction"
    return "all_clear"

# 5. Build the StateGraph
workflow = StateGraph(SCMState)

workflow.add_node("ui_agent", user_interface_agent)
workflow.add_node("intelligence_agent", supply_chain_intelligence_agent)
workflow.add_node("correction_node", autonomous_correction_protocol) 
workflow.add_node("orchestration_agent", process_orchestration_agent)
workflow.add_node("compliance_agent", verification_compliance_agent)
workflow.add_node("external_agent", external_entities_agent)

workflow.add_edge(START, "ui_agent")
workflow.add_edge("ui_agent", "intelligence_agent")

workflow.add_conditional_edges(
    "intelligence_agent",
    route_disruptions,
    {
        "needs_correction": "correction_node",
        "all_clear": "orchestration_agent"
    }
)

workflow.add_edge("correction_node", "compliance_agent")
workflow.add_edge("orchestration_agent", "compliance_agent")
workflow.add_edge("compliance_agent", "external_agent")
workflow.add_edge("external_agent", END)

workflow_app = workflow.compile()

# 6. API Endpoint
class OrderRequest(BaseModel):
    order_id: str
    simulate_disruption: bool = False

@app.post("/api/place_order")
async def place_order(order: OrderRequest):
    disruptions = ["severe weather warning at port"] if order.simulate_disruption else []
    
    initial_state = {
        "order_id": order.order_id,
        "current_phase": "Initiated",
        "inventory_status": "Pending",
        "detected_disruptions": disruptions,
        "audit_trail": [],
        "status": "Processing",
        "requires_correction": False
    }
    
    final_state = workflow_app.invoke(initial_state)
    return {"message": "Workflow completed", "state": final_state}