import pytest
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)

def test_api_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "solver" in data

def test_api_disrupt_endpoint():
    payload = {
        "disruption_type": "PORT_CONGESTION",
        "location": "Port of Los Angeles",
        "severity": 0.8,
        "duration_days": 7,
        "affected_warehouse": "Pacific_Hub_LA",
        "order_count": 5
    }
    res = client.post("/disrupt", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "scenario_id" in data
    assert data["affected_orders_count"] == 5
    assert data["total_value_at_risk_usd"] > 0.0

def test_api_plan_endpoint():
    payload = {
        "disruption": {
            "disruption_type": "CARRIER_FAILURE",
            "location": "Chicago Rail Intermodal",
            "severity": 0.7,
            "duration_days": 5,
            "order_count": 4
        }
    }
    res = client.post("/plan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["plan_status"] == "OPTIMAL"
    assert data["is_feasible"] is True
    assert len(data["allocations"]) == 4
    assert "explanation" in data

def test_api_approve_endpoint():
    payload = {
        "scenario_id": "SCEN-API-TEST-APPROVAL",
        "decision": "APPROVED",
        "dispatcher_name": "Senior_Dispatcher",
        "notes": "Verified container availability"
    }
    res = client.post("/approve", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] == "APPROVED"
    assert data["scenario_id"] == "SCEN-API-TEST-APPROVAL"

def test_api_audit_endpoint():
    res = client.get("/audit?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "logs" in data
    assert isinstance(data["logs"], list)
