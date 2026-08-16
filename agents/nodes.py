import os
import re
import json
import streamlit as st
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from agents.guards import SecurityGuards

# Dynamic LLM Client Loader
def get_llm_client(prefer: str = None):
    """Instantiate the requested LLM with fallback options"""
    if prefer is None:
        try:
            if hasattr(st, "session_state"):
                prefer = st.session_state.get("routing_preference", "gemini")
        except Exception:
            prefer = os.getenv("ROUTING_PREFERENCE", "gemini")
    prefer = (prefer or "gemini").lower()

    gemini_key = ""
    groq_key = ""
    try:
        if hasattr(st, "session_state"):
            gemini_key = st.session_state.get("gemini_api_key", "").strip()
            groq_key = st.session_state.get("groq_api_key", "").strip()
    except Exception:
        pass

    if not gemini_key:
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not groq_key:
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
    
    if prefer == "gemini" and gemini_key:
        try:
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=gemini_key,
                temperature=0.1
            ), "Gemini 2.5 Flash"
        except Exception as e:
            if hasattr(st, "warning"):
                st.warning(f"Failed to initialize Gemini, falling back to Groq. Error: {e}")
            
    if groq_key:
        try:
            return ChatGroq(
                model="mixtral-8x7b-32768", 
                groq_api_key=groq_key,
                temperature=0.1
            ), "Groq Mixtral"
        except Exception as e:
            if hasattr(st, "warning"):
                st.warning(f"Failed to initialize Groq. Error: {e}")
            
    if gemini_key:
        try:
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=gemini_key,
                temperature=0.1
            ), "Gemini 2.5 Flash"
        except Exception:
            pass
            
    return None, "Deterministic Fallback"

# Robust JSON Extractor & Parser
def parse_json_response(content: str, default_val: dict) -> dict:
    if not content or not isinstance(content, str):
        return default_val
    try:
        # Strip markdown code fences if present
        clean_content = re.sub(r"^```(?:json)?\s*", "", content.strip(), flags=re.MULTILINE)
        clean_content = re.sub(r"```\s*$", "", clean_content, flags=re.MULTILINE).strip()
        
        # Search for first { and last }
        start_idx = clean_content.find('{')
        end_idx = clean_content.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = clean_content[start_idx:end_idx+1]
            return json.loads(json_str)
        return json.loads(clean_content)
    except Exception as e:
        print(f"JSON Parse Error: {e}. Raw content: {content}")
        return default_val

# Helper to safely update agent_running status
def set_agent_running(name: str):
    try:
        if hasattr(st, "session_state"):
            st.session_state.agent_running = name
    except Exception:
        pass

# ==========================================
# SCM LLM-DRIVEN AGENT NODES
# ==========================================

def user_interface_agent(state: dict) -> dict:
    state["current_phase"] = "Order Intake Phase"
    set_agent_running("User Interface Intake")
    if "agent_thoughts" not in state or not isinstance(state["agent_thoughts"], dict):
        state["agent_thoughts"] = {}

    model, model_name = get_llm_client()
    
    # 🔒 InputGuard validation
    order_id = state.get("order_id", "")
    customer_id = state.get("customer_id", "")
    disruptions = state.get("detected_disruptions", [])
    is_safe = SecurityGuards.InputGuard(order_id, customer_id, disruptions)
    
    default_resp = {
        "thoughts": "UI Intake Agent: Verifying order specifications and checking payload safety. Intake Successful: Customer tier rules active.",
        "location": "Shanghai Distribution Center (Intake)",
        "status": "Processing" if is_safe else "Security Exception"
    }
    
    if not is_safe:
        threat_msg = "⚠️ SECURITY THREAT INTERCEPTED: Malicious payload intercepted by InputGuard layer."
        state["status"] = "Security Exception"
        state["detected_disruptions"] = ["Malicious input injection intercepted by Guard Layer."]
        state["requires_correction"] = True
        state["live_location"] = "System Quarantine"
        state["cost_savings"] = "$0.00"
        state["agent_thoughts"]["ui_agent"] = threat_msg
        return state

    if model:
        try:
            prompt = f"""
            You are the SCM Intake Agent. Review the following order details:
            - Order ID: {state.get('order_id')}
            - Customer ID: {state.get('customer_id')}
            - Customer Tier: {state.get('customer_tier')}
            
            Confirm that the details are safe and compile the initial tracking logs.
            You MUST respond with a single JSON object in this format:
            {{
              "thoughts": "Describe your intake validation thought process and confirm safety in 1 sentence.",
              "location": "Shanghai Distribution Center (Intake)",
              "status": "Processing"
            }}
            """
            response = model.invoke(prompt)
            data = parse_json_response(str(response.content), default_resp)
            state["live_location"] = data.get("location", default_resp["location"])
            state["status"] = data.get("status", default_resp["status"])
            state["agent_thoughts"]["ui_agent"] = data.get("thoughts", default_resp["thoughts"])
        except Exception as e:
            state["live_location"] = default_resp["location"]
            state["status"] = default_resp["status"]
            state["agent_thoughts"]["ui_agent"] = f"{default_resp['thoughts']} (LLM Error fallback: {e})"
    else:
        state["live_location"] = default_resp["location"]
        state["status"] = default_resp["status"]
        state["agent_thoughts"]["ui_agent"] = default_resp["thoughts"]
        
    return state

def supply_chain_intelligence_agent(state: dict) -> dict:
    if state.get("status") == "Security Exception":
        return state
        
    state["current_phase"] = "Order Assessment Phase"
    set_agent_running("Supply Chain Intelligence")
    if "agent_thoughts" not in state or not isinstance(state["agent_thoughts"], dict):
        state["agent_thoughts"] = {}

    disruptions = state.get("detected_disruptions", [])
    
    # Check for historical memory
    historical_solution = "No historical incident matches."
    if disruptions:
        disrupt_text = " ".join(disruptions).lower()
        if "port strike" in disrupt_text or "congestion" in disrupt_text or "strike" in disrupt_text:
            historical_solution = "Prior incident: Port strike congestion resolved by shifting freight to Seattle Port Authority and scheduling secondary rail/truck routes."
        elif "typhoon" in disrupt_text or "weather" in disrupt_text or "storm" in disrupt_text:
            historical_solution = "Prior incident: Ocean route storm resolved by shifting priority logistics to air freight block or routing south of storm corridor."

    default_resp = {
        "thoughts": "Intelligence Agent: Continuous tracking indicates routes are completely clear. SLA breach risk: <1%. Demand is stable.",
        "requires_correction": True if disruptions else False
    }
    
    if disruptions:
        default_resp["thoughts"] = f"Intelligence Agent: Threat Detected! Alert: {', '.join(disruptions)}. Dynamic rerouting required."

    model, model_name = get_llm_client()
    
    if model:
        try:
            prompt = f"""
            You are the SCM Risk Intelligence Agent. Analyze potential threats for the current order.
            - Active Disruptions: {', '.join(disruptions) if disruptions else 'None'}
            - Historical SCM Memory: {historical_solution}
            
            Determine if active threats require dynamic rerouting and write your threat assessment.
            You MUST respond with a single JSON object in this format:
            {{
              "thoughts": "Your concise risk assessment thoughts in 1-2 sentences. Highlight the disruption and safety of cargo.",
              "requires_correction": {"true" if disruptions else "false"}
            }}
            """
            response = model.invoke(prompt)
            data = parse_json_response(str(response.content), default_resp)
            state["requires_correction"] = data.get("requires_correction", default_resp["requires_correction"])
            state["agent_thoughts"]["intelligence_agent"] = f"[{model_name}] {data.get('thoughts', default_resp['thoughts'])}"
        except Exception as e:
            state["requires_correction"] = default_resp["requires_correction"]
            state["agent_thoughts"]["intelligence_agent"] = f"{default_resp['thoughts']} (LLM Error fallback: {e})"
    else:
        state["requires_correction"] = default_resp["requires_correction"]
        state["agent_thoughts"]["intelligence_agent"] = default_resp["thoughts"]
        
    return state

def compliance_agent(state: dict) -> dict:
    if state.get("status") == "Security Exception":
        return state
        
    state["current_phase"] = "Regulatory Sandbox Verification"
    set_agent_running("Verification & Compliance")
    if "agent_thoughts" not in state or not isinstance(state["agent_thoughts"], dict):
        state["agent_thoughts"] = {}
    
    customer_tier = state.get("customer_tier", "Standard")
    live_loc = state.get("live_location", "Origin Point")
    
    default_resp = {
        "thoughts": f"Compliance Agent: Customer Tier: {customer_tier}. Checking export/import compliance for cargo. Verifying custom tariff filing codes. Immutable audit trail locked in. Decision verified as compliant under international trade rules."
    }
    
    model, model_name = get_llm_client()
    
    if model:
        try:
            prompt = f"""
            You are the SCM Compliance Officer. Verify trade compliance parameters for this order:
            - Customer Tier: {customer_tier}
            - Cargo Location: {live_loc}
            
            Check customs declarations and confirm regulatory sandbox lock.
            You MUST respond with a single JSON object in this format:
            {{
              "thoughts": "Your compliance check analysis in 1 sentence. Confirm regulatory sandbox lock."
            }}
            """
            response = model.invoke(prompt)
            data = parse_json_response(str(response.content), default_resp)
            state["agent_thoughts"]["compliance_agent"] = f"[{model_name}] {data.get('thoughts', default_resp['thoughts'])}"
        except Exception as e:
            state["agent_thoughts"]["compliance_agent"] = f"{default_resp['thoughts']} (LLM Error fallback: {e})"
    else:
        state["agent_thoughts"]["compliance_agent"] = default_resp["thoughts"]
        
    return state

def orchestration_agent(state: dict) -> dict:
    if state.get("status") == "Security Exception":
        return state
        
    state["current_phase"] = "Logistics Planning Phase"
    set_agent_running("Process Orchestration")
    if "agent_thoughts" not in state or not isinstance(state["agent_thoughts"], dict):
        state["agent_thoughts"] = {}
    
    cycles = state.get("optimization_cycles", 0)
    disruptions = state.get("detected_disruptions", [])
    
    # Fallback default dict
    default_resp = {
        "thoughts": "Orchestration Agent: Standard parameters validated. Ocean corridor capacity open. Booking standard container carrier.",
        "route_selected": "Standard Maritime Corridor",
        "inventory_status": "Stock Reserved at Main Shenzhen Warehouse",
        "live_location": "Origin: Shenzhen Plant",
        "cost_savings": "$150.00 (Standard Tier discount)"
    }
    
    if cycles > 0:
        default_resp = {
            "thoughts": f"Orchestration Agent (Cycle {cycles}): Auto-Correction loop triggered. Carrier booking failed on previous try. Rerouting to alternative supplier & port.",
            "route_selected": f"Alternative Freight Route Beta-V{cycles}",
            "inventory_status": "Alternative Supplier Pinged",
            "live_location": "Diverting: Seattle Port Authority",
            "cost_savings": "Calculating Recovery Optimizer..."
        }
    elif disruptions:
        default_resp = {
            "thoughts": "Orchestration Agent: Threat flag active. Logistics plan adjusted to alternative ocean lane. Reserving stock at regional hub to avoid line delays.",
            "route_selected": "Optimized Alternative Corridor B",
            "inventory_status": "Inventory Allocation Confirmed",
            "live_location": "Awaiting Alternative Carrier (Singapore Hub)",
            "cost_savings": "$4,250 (SLA Penalty Avoided)"
        }
        
    model, model_name = get_llm_client()
    
    if model:
        try:
            prompt = f"""
            You are the SCM Logistics Planner. Select the best route, carrier, and inventory allocation.
            - Optimization Cycle count: {cycles}
            - Detected Disruptions: {', '.join(disruptions) if disruptions else 'None'}
            - Current Location: {state.get('live_location', 'Origin')}
            
            Determine the shipping route and dynamic cost savings (if cycle > 0 or disruptions exist, allocate alternate suppliers or Seattle port to prevent SLA breach).
            You MUST respond with a single JSON object in this format:
            {{
              "thoughts": "Your logistics planning logic in 1 sentence.",
              "route_selected": "Name of the shipping route",
              "inventory_status": "Status of the inventory reservation",
              "live_location": "Name of the dispatch port or origin plant",
              "cost_savings": "Estimate dynamic savings (e.g. '$12,450.00 (SLA Penalty Avoided)')"
            }}
            """
            response = model.invoke(prompt)
            data = parse_json_response(str(response.content), default_resp)
            
            state["route_selected"] = data.get("route_selected", default_resp["route_selected"])
            state["inventory_status"] = data.get("inventory_status", default_resp["inventory_status"])
            state["live_location"] = data.get("live_location", default_resp["live_location"])
            state["cost_savings"] = data.get("cost_savings", default_resp["cost_savings"])
            state["agent_thoughts"]["orchestration_agent"] = f"[{model_name}] {data.get('thoughts', default_resp['thoughts'])}"
        except Exception as e:
            state["route_selected"] = default_resp["route_selected"]
            state["inventory_status"] = default_resp["inventory_status"]
            state["live_location"] = default_resp["live_location"]
            state["cost_savings"] = default_resp["cost_savings"]
            state["agent_thoughts"]["orchestration_agent"] = f"{default_resp['thoughts']} (LLM Error fallback: {e})"
    else:
        state["route_selected"] = default_resp["route_selected"]
        state["inventory_status"] = default_resp["inventory_status"]
        state["live_location"] = default_resp["live_location"]
        state["cost_savings"] = default_resp["cost_savings"]
        state["agent_thoughts"]["orchestration_agent"] = default_resp["thoughts"]
        
    return state

def external_entities_node(state: dict) -> dict:
    if state.get("status") == "Security Exception":
        return state
        
    state["current_phase"] = "Autonomous Execution Phase"
    set_agent_running("External Entities Simulation")
    if "agent_thoughts" not in state or not isinstance(state["agent_thoughts"], dict):
        state["agent_thoughts"] = {}
    
    cycles = state.get("optimization_cycles", 0)
    simulate_disruption = state.get("simulate_disruption", False)
    
    default_resp = {
        "thoughts": "External Entities Node: Ocean carrier confirmed boarding. Standard transit timelines met. Delivery completed.",
        "carrier_status": "Carrier Booking Confirmed",
        "status": "Execution Fulfilled",
        "live_location": "Pacific Ocean Transit -> San Jose, CA (Delivered)",
        "cost_savings": "$250.00 (Standard Volume Discount)"
    }
    
    if simulate_disruption and cycles < 1:
        default_resp = {
            "thoughts": "⚠️ EXTERNAL GATEWAY ALERT: Port Authority rejected booking at Port of Los Angeles. Port status: 100% capacity / Strike active. Returning error feedback loop...",
            "carrier_status": "Booking Rejected (Port Overcapacity/Strike)",
            "status": "Processing",
            "live_location": "Port of Los Angeles (Congested/Rejected)",
            "cost_savings": "$0.00 (SLA Penalty Risk)"
        }
    elif cycles > 0 or state.get("detected_disruptions"):
        default_resp = {
            "thoughts": "External Entities Node: Dynamic logistics carrier confirmed alternative arrival. Warehouse picking & customs clearance processed. Delivery completed successfully!",
            "carrier_status": "Carrier Booking Confirmed",
            "status": "Execution Fulfilled",
            "live_location": "Diverted: Oakland Port Terminal -> Seattle Terminal (Delivered)",
            "cost_savings": "$12,450.00 (SLA Penalty Prevented + Dyn. Route optimization)"
        }
        
    model, model_name = get_llm_client()
    
    if model:
        try:
            prompt = f"""
            You are the SCM Fulfillment Simulator. Simulate carrier booking confirmations and final delivery.
            - Selected Route: {state.get('route_selected')}
            - Simulate Disruption active: {simulate_disruption}
            - Current Optimization cycle: {cycles}
            
            Determine the booking status.
            *IMPORTANT*: If 'Simulate Disruption' is true and cycle is 0, set carrier_status to 'Booking Rejected (Port Overcapacity/Strike)' and live_location to 'Port of Los Angeles (Congested/Rejected)' to trigger self-correcting loops.
            Otherwise confirm delivery at Seattle Terminal or San Jose.
            You MUST respond with a single JSON object in this format:
            {{
              "thoughts": "Your fulfillment logging thoughts in 1 sentence.",
              "carrier_status": "Booking Rejected (Port Overcapacity/Strike)" or "Carrier Booking Confirmed",
              "status": "Processing" or "Execution Fulfilled",
              "live_location": "Current location (e.g. 'Diverted: Oakland Port Terminal -> Seattle Terminal (Delivered)' or 'Pacific Ocean Transit -> San Jose, CA (Delivered)')",
              "cost_savings": "Dynamic savings or SLA details"
            }}
            """
            response = model.invoke(prompt)
            data = parse_json_response(str(response.content), default_resp)
            
            # Update state with simulation results
            state["carrier_status"] = data.get("carrier_status", default_resp["carrier_status"])
            state["status"] = data.get("status", default_resp["status"])
            state["live_location"] = data.get("live_location", default_resp["live_location"])
            state["cost_savings"] = data.get("cost_savings", default_resp["cost_savings"])
            
            # Check if booking failed and we need to increment cycle
            if state["carrier_status"] == "Booking Rejected (Port Overcapacity/Strike)" and cycles < 1:
                state["optimization_cycles"] = cycles + 1
                
            state["agent_thoughts"]["external_entities"] = f"[{model_name}] {data.get('thoughts', default_resp['thoughts'])}"
        except Exception as e:
            state["carrier_status"] = default_resp["carrier_status"]
            state["status"] = default_resp["status"]
            state["live_location"] = default_resp["live_location"]
            state["cost_savings"] = default_resp["cost_savings"]
            if default_resp["carrier_status"] == "Booking Rejected (Port Overcapacity/Strike)" and cycles < 1:
                state["optimization_cycles"] = cycles + 1
            state["agent_thoughts"]["external_entities"] = f"{default_resp['thoughts']} (LLM Error fallback: {e})"
    else:
        state["carrier_status"] = default_resp["carrier_status"]
        state["status"] = default_resp["status"]
        state["live_location"] = default_resp["live_location"]
        state["cost_savings"] = default_resp["cost_savings"]
        if default_resp["carrier_status"] == "Booking Rejected (Port Overcapacity/Strike)" and cycles < 1:
            state["optimization_cycles"] = cycles + 1
        state["agent_thoughts"]["external_entities"] = default_resp["thoughts"]
        
    return state

