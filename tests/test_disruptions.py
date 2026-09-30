"""Unit tests for disruption event modeling and incident catalog."""

import pytest
from core.disruptions import (
    DisruptionEvent, DisruptionType, SeverityLevel, get_predefined_disruptions
)


def test_disruption_catalog_completeness():
    catalog = get_predefined_disruptions()
    assert len(catalog) >= 3

    types = {d.disruption_type for d in catalog}
    assert DisruptionType.CARRIER_FAILURE in types
    assert DisruptionType.PORT_CONGESTION in types


def test_disruption_event_convenience_properties():
    event = DisruptionEvent(
        event_id="TEST-01",
        disruption_type=DisruptionType.CARRIER_FAILURE,
        target_type="CARRIER",
        target_id="SAFEXPRESS",
        severity=SeverityLevel.CRITICAL,
        delay_days_added=5.0,
        cost_surcharge_pct=50.0,
        capacity_reduction_pct=100.0,
        description="Safexpress nationwide strike."
    )

    assert event.carrier == "SAFEXPRESS"
    assert event.port is None
    assert event.delay_days == 5.0

    d_dict = event.to_dict()
    assert d_dict["carrier"] == "SAFEXPRESS"
    assert d_dict["delay_days"] == 5.0
