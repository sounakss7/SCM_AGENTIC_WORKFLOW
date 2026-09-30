"""Unit tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
from api.server import app

client = TestClient(app)


def test_api_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "Bharat" in data["app_name"]


def test_api_parse_address_endpoint():
    res = client.post("/address/parse", json={
        "raw_address": "Near Hanuman Mandir, Sector 15, Noida, UP, 201301",
        "pincode": "201301"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["has_landmark"] is True
    assert data["completeness_score"] >= 0.60


def test_api_rate_cards_endpoint():
    res = client.get("/carriers/rate-cards")
    assert res.status_code == 200
    data = res.json()
    assert "DELHIVERY" in data
    assert "BLUEDART" in data
    assert "SHADOWFAX" in data


def test_api_audit_logs_endpoint():
    res = client.get("/audit/logs")
    assert res.status_code == 200
    data = res.json()
    assert "logs" in data
