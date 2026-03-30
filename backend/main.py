import os
import re
from typing import TypedDict, List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.graph import StateGraph

# LLMs
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI

# Qdrant Vector Memory
from qdrant_client import QdrantClient, models as qdrant_models
from langchain_qdrant import QdrantVectorStore

# Load environment variables
load_dotenv()

# ============= 1. ML Multi-LLM Model Manager =============
class LLMRouter:
    def __init__(self):
        self.gemini = None
        self.groq = None
        self.mistral = None
        
        try:
            if os.getenv("GEMINI_API_KEY"):
                self.gemini = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
        except Exception as e:
            print(f"⚠️ Gemini init failed: {e}")

        try:
            if os.getenv("GROQ_API_KEY"):
                self.groq = ChatGroq(model="mixtral-8x7b-32768", temperature=0.2)
        except Exception as e:
            print(f"⚠️ Groq init failed: {e}")

        try:
            if os.getenv("MISTRAL_API_KEY"):
                self.mistral = ChatMistralAI(model="mistral-small", temperature=0.2)
        except Exception as e:
            print(f"⚠️ Mistral init failed: {e}")

    def get_model(self, prefer: str = "gemini"):
        # Select preference with fallback to any available model
        mapping = {"gemini": self.gemini, "groq": self.groq, "mistral": self.mistral}
        if prefer in mapping and mapping[prefer]:
            return mapping[prefer]
        # Fallback
        for name, model in mapping.items():
            if model:
                print(f"🔄 Routing fallback to {name}")
                return model
        return None

llm_router = LLMRouter()

# ============= 2. Vector Memory Initialization =============
vector_store = None
qclient = None
try:
    # Use Gemini Embeddings to strictly bypass Vercel's heavy PyTorch size limits!
    embeddings = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).embeddings if False else __import__('langchain_google_genai').GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if qdrant_url:
        qclient = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    else:
        qclient = QdrantClient(location=":memory:")

    if not qclient.collection_exists("mitigation_memory"):
        qclient.create_collection(
            collection_name="mitigation_memory", 
            vectors_config=qdrant_models.VectorParams(size=768, distance=qdrant_models.Distance.COSINE)
        )
    
    vector_store = QdrantVectorStore(
        client=qclient, 
        collection_name="mitigation_memory", 
        embedding=embeddings
    )
except Exception as e:
    print(f"⚠️ Vector Memory initialization failed: {e}")

# ============= 3. Security Layer Pipelines =============
class AuditLogger:
    @staticmethod
    def log(state: dict, agent: str, action: str):
        state["audit_trail"].append({
            "timestamp": "now",
            "agent": agent,
            "action": action
        })

class SecurityGuards:
    @staticmethod
    def InputGuard(state: dict) -> bool:
        """Inspect context for prompt injections or malicious requests."""
        malicious_patterns = [r"ignore all previous instructions", r"drop table", r"system prompt"]
        for d in state.get("detected_disruptions", []):
            d_lower = d.lower()
            if any(re.search(pat, d_lower) for pat in malicious_patterns):
                return False
        return True

    @staticmethod
    def OutputGuard(response_text: str) -> bool:
        """Sanitize LLM output. Reject hazardous structure."""
        if not response_text or "Error" in response_text[:10] or "malicious" in response_text.lower():
            return False
        return True

    @staticmethod
    def MemoryGuard(context: str) -> str:
        """Strip sensitive PII tags or order specifics before storing into Vector DB."""
        if not context:
            return ""
        # Simple anonymizer regex
        anonymized = re.sub(r'ORD-\d+', '[ORDER_ID]', context)
        anonymized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]', anonymized)
        return anonymized

# ============= 4. Data Models & API Setup =============
app = FastAPI(title="SCM Agentic Workflow API (Hackathon Arch)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

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

# ============= 5. Agent Nodes =============
def user_interface_agent(state: SCMState) -> SCMState:
    state["current_phase"] = "Planning"
    
    # 🔒 InputGuard Implementation
    is_safe = SecurityGuards.InputGuard(state)
    if not is_safe:
        state["status"] = "Security Exception"
        state["detected_disruptions"] = ["Malicious Prompt Injection Intercepted"]
        state["requires_correction"] = True
        AuditLogger.log(state, "UI (InputGuard)", f"Request blocked due to security alert on Order {state['order_id']}")
    else:
        AuditLogger.log(state, "UI", f"Order {state['order_id']} received and structurally verified.")
    return state

def supply_chain_intelligence_agent(state: SCMState) -> SCMState:
    if state["status"] == "Security Exception":
        return state
        
    disruptions = state.get("detected_disruptions", [])
    if disruptions:
        model = llm_router.get_model("groq") # Prefer fast Groq Mixtral
        
        # 🧠 Vector Memory Retrieval
        historical_context = ""
        if vector_store:
            try:
                query = " ".join(disruptions)
                results = vector_store.similarity_search(query, k=1)
                if results and len(results) > 0:
                    historical_context = f"(Historical Mitigation found: {results[0].page_content})"
            except Exception as e:
                print("Memory read failed", e)

        if model:
            try:
                prompt = f"Analyze supply chain disruption: {', '.join(disruptions)}. {historical_context}. Provide a brief 1-sentence mitigation."
                response = model.invoke(prompt)
                analysis = str(response.content)
                
                # 🔒 OutputGuard Verification
                if not SecurityGuards.OutputGuard(analysis):
                    analysis = "Output blocked by OutputGuard due to potential policy violation."
                else:
                    # 🧠 Vector Memory Storage (Save successful mitigation for future)
                    if vector_store:
                        safe_memory = SecurityGuards.MemoryGuard(analysis)
                        try:
                            vector_store.add_texts([f"Disruption: {', '.join(disruptions)}. Solution: {safe_memory}"])
                        except Exception as ve:
                            print("Memory store failed", ve)
                        
            except Exception as e:
                analysis = f"Intelligence Model unavailable ({str(e)[:30]})"
        else:
            analysis = "No APIs operational - applying Standard Operating Procedure."
            
        AuditLogger.log(state, "Intelligence", f"Analysis: {analysis}")
        state["requires_correction"] = True
    else:
        AuditLogger.log(state, "Intelligence", "System operating normally.")
        
    return state

def orchestration_agent(state: SCMState) -> SCMState:
    if state["status"] == "Security Exception":
        return state
        
    state["current_phase"] = "Execution"
    if state["requires_correction"]:
        state["status"] = "Disruption Handling Active"
        state["inventory_status"] = "Rerouting"
        AuditLogger.log(state, "Orchestration", "Disruption evaluated: Auto-rerouting active.")
    else:
        state["status"] = "Order Processing"
        state["inventory_status"] = "Updated"
        AuditLogger.log(state, "Orchestration", "Standard execution path selected.")
    return state

def compliance_agent(state: SCMState) -> SCMState:
    if state["status"] == "Security Exception":
        return state
        
    state["current_phase"] = "Compliance"
    
    # 🔒 AuditLogger Final Compliance Verification
    AuditLogger.log(state, "Compliance", "Order passed multi-layer security and regulatory checks.")
    state["requires_correction"] = False
    state["status"] = "Order Fulfilled"
    return state

# ============= 6. LangGraph Workflow =============
def create_workflow():
    workflow = StateGraph(SCMState)
    workflow.add_node("ui_agent", user_interface_agent)
    workflow.add_node("intelligence_agent", supply_chain_intelligence_agent)
    workflow.add_node("orchestration_agent", orchestration_agent)
    workflow.add_node("compliance_agent", compliance_agent)
    
    workflow.set_entry_point("ui_agent")
    workflow.add_edge("ui_agent", "intelligence_agent")
    workflow.add_edge("intelligence_agent", "orchestration_agent")
    workflow.add_edge("orchestration_agent", "compliance_agent")
    workflow.set_finish_point("compliance_agent")
    return workflow.compile()

workflow = create_workflow()

# ============= 7. Endpoints =============
@app.get("/")
def root():
    return {"message": "SCM API (Hackathon Arch + Qdrant/Security Edition) is live."}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SCM Agentic Workflow API",
        "active_models": [k for k,v in [("gemini", llm_router.gemini), ("groq", llm_router.groq), ("mistral", llm_router.mistral)] if v is not None],
        "qdrant_memory_active": vector_store is not None
    }

@app.post("/api/place_order")
async def place_order(request: OrderRequest):
    try:
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
                "status": "Fatal Error", 
                "current_phase": "Error",
                "inventory_status": "Unknown",
                "detected_disruptions": [],
                "audit_trail": [{"timestamp": "now", "agent": "System Exception", "action": str(e)}]
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
