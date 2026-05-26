import streamlit as st
import re
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from agents.guards import SecurityGuards

def get_llm_client(prefer: str = "gemini"):
    """Instantiate the requested LLM with fallback option"""
    gemini_key = st.session_state.get("gemini_api_key", "").strip()
    groq_key = st.session_state.get("groq_api_key", "").strip()
    
    if prefer == "gemini" and gemini_key:
        try:
            return ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", 
                google_api_key=gemini_key,
                temperature=0.1
            ), "Gemini 2.5 Flash"
        except Exception as e:
            st.warning(f"Failed to initialize Gemini, falling back to Groq. Error: {e}")
            
    if groq_key:
        try:
            return ChatGroq(
                model="mixtral-8x7b-32768", 
                groq_api_key=groq_key,
                temperature=0.1
            ), "Groq Mixtral"
        except Exception as e:
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

def user_interface_agent(state: dict) -> dict:
    state["current_phase"] = "Order Intake Phase"
    state["agent_thoughts"]["ui_agent"] = "UI Intake Agent: Verifying order specifications and checking payload safety."
    
    is_safe = SecurityGuards.InputGuard(state["order_id"], state["customer_id"], state["detected_disruptions"])
    if not is_safe:
        state["status"] = "Security Exception"
        state["detected_disruptions"] = ["Malicious input injection intercepted by Guard Layer."]
        state["requires_correction"] = True
        state["live_location"] = "System Quarantine"
        state["cost_savings"] = "$0.00"
        state["agent_thoughts"]["ui_agent"] = "⚠️ SECURITY THREAT INTERCEPTED: Input fails security inspection."
    else:
        state["live_location"] = "Shanghai Distribution Center (Intake)"
        state["agent_thoughts"]["ui_agent"] = f"Intake Successful: Customer tier rules for '{state['customer_tier']}' active. Initiating SCM workflow tracker."
        
    return state

def supply_chain_intelligence_agent(state: dict) -> dict:
    if state["status"] == "Security Exception":
        return state
        
    state["current_phase"] = "Order Assessment Phase"
    disruptions = state.get("detected_disruptions", [])
    
    st.session_state.agent_running = "Supply Chain Intelligence"
    
    if disruptions:
        model, model_name = get_llm_client(prefer=st.session_state.routing_preference)
        
        # Simulated Vector Database Retrieval
        historical_solution = ""
        if "port strike" in " ".join(disruptions).lower() or "congestion" in " ".join(disruptions).lower():
            historical_solution = "Prior incident: Port congestion resolved by shifting freight to Seattle Port Authority and scheduling secondary rail/truck routes."
        elif "typhoon" in " ".join(disruptions).lower() or "weather" in " ".join(disruptions).lower():
            historical_solution = "Prior incident: Ocean route storm resolved by shifting priority logistics to air freight block or routing south of storm corridor."
            
        thought_log = f"Intelligence Agent: Threat Detected! Alert: {', '.join(disruptions)}. "
        if historical_solution:
            thought_log += f"Found historical mitigation: {historical_solution}. "
            
        if model:
            try:
                prompt = (
                    f"Analyze the following supply chain threat: {', '.join(disruptions)}. "
                    f"Historical memory references: {historical_solution}. "
                    f"Formulate a concise 1-2 sentence mitigation decision. Highlight target carrier adjustment or port diversion."
                )
                response = model.invoke(prompt)
                decision = str(response.content)
                
                if not SecurityGuards.OutputGuard(decision):
                    decision = "Output blocked by Guard rails. Reverting to SOP standard rerouting."
                
                thought_log += f"\nLLM Analysis ({model_name}): {decision}"
            except Exception as e:
                decision = f"LLM assessment errored: {e}. Executing standard SOP."
                thought_log += f"\nWarning: {decision}"
        else:
            decision = "No LLM Keys operational. Applying default Standard Operating Procedure: Reroute via nearest functional port hub."
            thought_log += f"\nFallback: {decision}"
            
        state["agent_thoughts"]["intelligence_agent"] = thought_log
        state["requires_correction"] = True
    else:
        state["agent_thoughts"]["intelligence_agent"] = "Intelligence Agent: Continuous tracking indicates routes are completely clear. SLA breach risk: <1%. Demand is stable."
        state["requires_correction"] = False
        
    return state

def compliance_agent(state: dict) -> dict:
    if state["status"] == "Security Exception":
        return state
        
    state["current_phase"] = "Regulatory Sandbox Verification"
    st.session_state.agent_running = "Verification & Compliance"
    
    tier_info = f"Customer Tier: {state['customer_tier']}. "
    compliance_rules = "Checking export/import compliance for cargo. Verifying custom tariff filing codes."
    
    state["agent_thoughts"]["compliance_agent"] = f"Compliance Agent: {tier_info}{compliance_rules}\nImmutable audit trail locked in. Decision verified as compliant under international trade rules."
    return state

def orchestration_agent(state: dict) -> dict:
    if state["status"] == "Security Exception":
        return state
        
    state["current_phase"] = "Logistics Planning Phase"
    st.session_state.agent_running = "Process Orchestration"
    
    cycles = state.get("optimization_cycles", 0)
    
    if cycles > 0:
        state["status"] = "Self-Correction Protocols Active"
        state["route_selected"] = f"Alternative Freight Route Beta-V{cycles}"
        state["inventory_status"] = "Alternative Supplier Pinged"
        state["live_location"] = "Diverting: Seattle Port Authority"
        state["cost_savings"] = "Calculating Recovery Optimizer..."
        
        state["agent_thoughts"]["orchestration_agent"] = (
            f"Orchestration Agent (Cycle {cycles}): Auto-Correction loop triggered. "
            f"Carrier booking failed on previous try. Rerouting to alternative supplier & port."
        )
    else:
        if state["detected_disruptions"]:
            state["status"] = "Logistics Rerouting"
            state["route_selected"] = "Optimized Alternative Corridor B"
            state["inventory_status"] = "Inventory Allocation Confirmed"
            state["live_location"] = "Awaiting Alternative Carrier (Singapore Hub)"
            state["cost_savings"] = "$4,250 (SLA Penalty Avoided)"
            
            state["agent_thoughts"]["orchestration_agent"] = (
                "Orchestration Agent: Threat flag active. Logistics plan adjusted to alternative ocean lane. "
                "Reserving stock at regional hub to avoid line delays."
            )
        else:
            state["status"] = "Order Processing"
            state["route_selected"] = "Standard Maritime Corridor"
            state["inventory_status"] = "Stock Reserved at Main Shenzhen Warehouse"
            state["live_location"] = "Origin: Shenzhen Plant"
            state["cost_savings"] = "$150.00 (Standard Tier discount)"
            
            state["agent_thoughts"]["orchestration_agent"] = (
                "Orchestration Agent: Standard parameters validated. Ocean corridor capacity open. "
                "Booking standard container carrier."
            )
            
    return state

def external_entities_node(state: dict) -> dict:
    if state["status"] == "Security Exception":
        return state
        
    state["current_phase"] = "Autonomous Execution Phase"
    st.session_state.agent_running = "External Entities Simulation"
    
    # Trigger port rejection if simulated disruption and first cycle
    if state["simulate_disruption"] and state["optimization_cycles"] < 1:
        state["carrier_status"] = "Booking Rejected (Port Overcapacity/Strike)"
        state["live_location"] = "Port of Los Angeles (Congested/Rejected)"
        state["cost_savings"] = "$0.00 (SLA Penalty Risk)"
        state["optimization_cycles"] += 1
        state["agent_thoughts"]["external_entities"] = (
            "⚠️ EXTERNAL GATEWAY ALERT: Port Authority rejected booking at Port of Los Angeles. "
            "Port status: 100% capacity / Strike active. Returning error feedback loop..."
        )
    else:
        state["carrier_status"] = "Carrier Booking Confirmed"
        state["status"] = "Execution Fulfilled"
        
        if state["optimization_cycles"] > 0 or state["detected_disruptions"]:
            state["live_location"] = "Diverted: Oakland Port Terminal -> Seattle Terminal (Delivered)"
            state["cost_savings"] = "$12,450.00 (SLA Penalty Prevented + Dyn. Route optimization)"
            state["agent_thoughts"]["external_entities"] = (
                "External Entities Node: Dynamic logistics carrier confirmed alternative arrival. "
                "Warehouse picking & customs clearance processed. Delivery completed successfully!"
            )
        else:
            state["live_location"] = "Pacific Ocean Transit -> San Jose, CA (Delivered)"
            state["cost_savings"] = "$250.00 (Standard Volume Discount)"
            state["agent_thoughts"]["external_entities"] = (
                "External Entities Node: Ocean carrier confirmed boarding. "
                "Standard transit timelines met. Delivery completed."
            )
            
    return state
