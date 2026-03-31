import sys
sys.path.append('.')
from main import workflow

initial_state = {
    "order_id": "test",
    "current_phase": "Initializing",
    "inventory_status": "Checking",
    "route_selected": "Pending Evaluation",
    "carrier_status": "Standby",
    "optimization_cycles": 0,
    "detected_disruptions": [],
    "audit_trail": [],
    "status": "Processing",
    "requires_correction": False,
    "simulate_disruption": False,
    "cost_savings": "$0.00 (Calculating...)",
    "live_location": "System Initiation"
}

try:
    final = workflow.invoke(initial_state)
    print("FINAL LOCATION:", final.get("live_location"))
    print("FINAL COST:", final.get("cost_savings"))
except Exception as e:
    print("ERROR:", e)
