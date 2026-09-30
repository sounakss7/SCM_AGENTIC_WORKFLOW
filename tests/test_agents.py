"""Unit tests for individual agent nodes in the 5-agent resilience workflow."""

import pytest
from agents.state import DisruptionWorkflowState
from agents.monitor import monitor_agent_node
from agents.risk_agent import risk_agent_node
from agents.routing_agent import routing_agent_node
from agents.validator_agent import validator_agent_node
from agents.explainer_agent import explainer_agent_node
from core.disruptions import DisruptionEvent, DisruptionType, SeverityLevel


def test_monitor_agent_detection():
    nominal = {
        "supplier": "SUP_PUNE",
        "port": "PORT_JNPT",
        "warehouse": "WH_MUMBAI",
        "retailer": "RET_MUMBAI",
        "carrier": "SAFEXPRESS"
    }
    disruption = {
        "event_id": "D1",
        "disruption_type": "CARRIER_FAILURE",
        "carrier": "SAFEXPRESS",
        "description": "Safexpress strike"
    }

    state: DisruptionWorkflowState = {
        "nominal_plan": nominal,
        "disruption": disruption,
        "agent_logs": [],
        "model_records": []
    }

    res = monitor_agent_node(state)
    assert res["disruption_detected"] is True
    assert res["status"] == "DISRUPTED"


def test_risk_agent_scoring():
    nominal = {
        "supplier": "SUP_PUNE",
        "port": "PORT_JNPT",
        "warehouse": "WH_MUMBAI",
        "retailer": "RET_MUMBAI",
        "carrier": "SAFEXPRESS"
    }
    disruption = {
        "event_id": "D1",
        "disruption_type": "CARRIER_FAILURE",
        "carrier": "SAFEXPRESS",
        "delay_days": 4.0,
        "severity": "HIGH",
        "description": "Safexpress strike"
    }

    state: DisruptionWorkflowState = {
        "order_id": "ORD-RISK-1",
        "sku_id": "SKU_01",
        "quantity": 100,
        "nominal_plan": nominal,
        "disruption": disruption,
        "disruption_detected": True,
        "agent_logs": [],
        "model_records": []
    }

    res = risk_agent_node(state)
    assert res["status"] == "RISK_EVALUATED"
    risk = res["risk_assessment"]
    assert risk["risk_score"] > 0.0
    assert risk["unattended_penalty_inr"] > 0.0
    assert len(res["model_records"]) == 1
    assert "Gemini" in res["model_records"][0]["target_provider"]


def test_validator_agent_groq_validation():
    proposed = {
        "carrier": "DELHIVERY",
        "warehouse": "WH_MUMBAI",
        "total_transit_days": 2.5,
        "total_cost_inr": 1200.0
    }
    state: DisruptionWorkflowState = {
        "quantity": 100,
        "proposed_plan": proposed,
        "disruption_detected": True,
        "agent_logs": [],
        "model_records": []
    }

    res = validator_agent_node(state)
    assert res["status"] == "VALIDATED"
    assert res["validation_result"]["is_valid"] is True
    assert len(res["model_records"]) == 1
    assert "Groq" in res["model_records"][0]["target_provider"]
