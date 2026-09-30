"""Unit tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_api_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "Control Tower" in data["app_name"]


def test_api_network_endpoint():
    res = client.get("/network")
    assert res.status_code == 200
    data = res.json()
    assert len(data["suppliers"]) == 3
    assert len(data["warehouses"]) == 2
    assert len(data["stores"]) == 6


def test_api_forecast_endpoint():
    res = client.post("/forecast", json={"horizon_length": 4})
    assert res.status_code == 200
    data = res.json()
    assert "forecasts" in data
    assert len(data["forecasts"]) > 0


def test_api_plan_endpoint():
    res = client.post("/plan", json={"max_negotiation_rounds": 1})
    assert res.status_code == 200
    data = res.json()
    assert "solution" in data
    assert data["solution"]["is_feasible"] is True
    assert "plain_english_briefing" in data


def test_api_disrupt_endpoint():
    res = client.post("/disrupt", json={
        "disruption_type": "SUPPLIER_DELAY",
        "affected_entity": "S1",
        "severity_factor": 2.0,
        "duration_periods": 2
    })
    assert res.status_code == 200
    data = res.json()
    assert "disruption" in data
    assert "solution" in data


def test_api_scenario_endpoint():
    res = client.get("/scenario/1")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == 1


def test_api_benchmark_summary_endpoint():
    res = client.get("/benchmark/summary")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
