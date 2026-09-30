"""Unit and Integration Tests for FastAPI Application Endpoints."""

import pytest
from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_api_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "Resilience" in data["service"]
    assert "INR" in data["currency"]


def test_api_network_endpoint():
    res = client.get("/network")
    assert res.status_code == 200
    data = res.json()
    assert len(data["suppliers"]) == 3
    assert len(data["ports"]) == 3
    assert len(data["warehouses"]) == 3
    assert len(data["retailers"]) == 4
    assert len(data["carriers"]) == 4
    assert len(data["skus"]) == 25


def test_api_catalog_disruptions():
    res = client.get("/catalog/disruptions")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    assert any(d["target_id"] == "SAFEXPRESS" for d in data)


def test_api_simulate_steady_state():
    res = client.post("/simulate", json={
        "order_id": "ORD-TEST-001",
        "sku_id": "SKU_01",
        "quantity": 50,
        "source_supplier": "SUP_PUNE",
        "target_retailer": "RET_MUMBAI"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["disruption_detected"] is False
    assert data["status"] == "NOMINAL"
    assert data["final_plan"] is not None


def test_api_disrupt_injection():
    res = client.post("/disrupt", json={
        "disruption_type": "CARRIER_FAILURE",
        "target_type": "CARRIER",
        "target_id": "SAFEXPRESS",
        "severity": "CRITICAL",
        "delay_days_added": 5.0,
        "cost_surcharge_pct": 50.0,
        "capacity_reduction_pct": 100.0,
        "description": "Safexpress strike via API test."
    })
    assert res.status_code == 200
    data = res.json()
    assert "injected_disruption" in data
    assert "workflow_resolution" in data
    resolution = data["workflow_resolution"]
    assert resolution["disruption_detected"] is True
    assert resolution["final_plan"]["carrier"] != "SAFEXPRESS"


def test_api_plan_scenario():
    res = client.get("/plan/1")
    assert res.status_code == 200
    data = res.json()
    assert "scenario_metadata" in data
    assert data["scenario_metadata"]["scenario_id"] == 1
