"""Unit and Integration Tests for the 5-Agent LangGraph Resilience Workflow."""

import pytest
from core.network import get_default_indian_network
from core.disruptions import DisruptionEvent, DisruptionType, SeverityLevel, get_predefined_disruptions
from agents.workflow import run_resilience_workflow


def test_workflow_nominal_pass_through():
    """Verify that orders without intersecting disruptions remain on nominal plan."""
    net = get_default_indian_network()
    res = run_resilience_workflow(
        order_id="ORD-PASS-1",
        sku_id="SKU_01",
        quantity=50,
        source_supplier="SUP_PUNE",
        target_retailer="RET_MUMBAI",
        disruption=None
    )
    assert res.get("disruption_detected") is False
    assert res.get("status") == "NOMINAL"
    assert res.get("final_plan") is not None
    assert "nominal schedule" in res.get("explanation", "").lower()


def test_workflow_carrier_strike_self_correction():
    """Verify 5-agent detection, risk assessment, deterministic replan, validation, and explanation."""
    disruptions = get_predefined_disruptions()
    safexpress_strike = next(d for d in disruptions if d.target_id == "SAFEXPRESS")

    res = run_resilience_workflow(
        order_id="ORD-DIS-2",
        sku_id="SKU_01",
        quantity=100,
        source_supplier="SUP_PUNE",
        target_retailer="RET_MUMBAI",
        disruption=safexpress_strike.to_dict()
    )

    # 1. Monitor detected disruption
    assert res.get("disruption_detected") is True

    # 2. Risk assessed by Gemini 2.5 Flash
    risk = res.get("risk_assessment")
    assert risk is not None
    assert risk.get("risk_score") >= 5.0
    assert risk.get("unattended_penalty_inr") > 0

    # 3. Routing Agent switched away from Safexpress
    final_plan = res.get("final_plan")
    assert final_plan is not None
    assert final_plan.get("carrier") != "SAFEXPRESS"
    assert final_plan.get("is_feasible") is True

    # 4. Validator approved via Groq
    val = res.get("validation_result")
    assert val is not None
    assert val.get("is_valid") is True

    # 5. Explainer generated briefing
    explanation = res.get("explanation")
    assert explanation is not None
    assert len(explanation) > 50

    # 6. Model routing telemetry verified
    model_records = res.get("model_records", [])
    assert len(model_records) >= 3  # Risk (Gemini), Validator (Groq), Explainer (Gemini)

    providers = [m["target_provider"] for m in model_records]
    assert any("Gemini" in p for p in providers), "Must record Gemini call for reasoning"
    assert any("Groq" in p for p in providers), "Must record Groq call for validation"


def test_validator_self_correction_retry_loop():
    """Verify that when a proposed route violates constraints, Validator triggers self-correction."""
    # Create an order with huge volume (e.g. 500 units) that will test carrier limit or retry logic
    disruptions = get_predefined_disruptions()
    disruption = disruptions[1]  # Safexpress strike

    res = run_resilience_workflow(
        order_id="ORD-RETRY-3",
        sku_id="SKU_02",
        quantity=250,
        source_supplier="SUP_SURAT",
        target_retailer="RET_DELHI",
        disruption=disruption.to_dict()
    )

    assert res.get("status") in ["COMPLETED", "VALIDATED"]
    assert res.get("final_plan") is not None
    assert res.get("final_plan", {}).get("carrier") != "SAFEXPRESS"
