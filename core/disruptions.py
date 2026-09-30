"""Disruption Event Models and Incident Catalog for Indian Logistics Network."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DisruptionType(str, Enum):
    CARRIER_FAILURE = "CARRIER_FAILURE"      # Transporter strike, fleet breakdown, FASTag blacklisting
    PORT_CONGESTION = "PORT_CONGESTION"      # Container dwell time spike, berth delays at JNPT / Mundra
    ROUTE_CLOSURE = "ROUTE_CLOSURE"          # Monsoon landslide in Western Ghats, NH-48 waterlogging
    CAPACITY_CHOKE = "CAPACITY_CHOKE"        # Surcharge / quota choke during festive surge


class SeverityLevel(str, Enum):
    LOW = "LOW"            # +1.0 day delay, +10% cost surcharge
    MEDIUM = "MEDIUM"      # +2.5 days delay, +25% cost surcharge, 40% capacity cut
    HIGH = "HIGH"          # +4.0 days delay, +50% cost surcharge, 75% capacity cut
    CRITICAL = "CRITICAL"  # Link / carrier 100% inoperable, complete route stoppage


class DisruptionEvent(BaseModel):
    event_id: str
    disruption_type: DisruptionType
    target_type: str = Field(..., description="'CARRIER', 'PORT', or 'LINK'")
    target_id: str = Field(..., description="e.g. 'SAFEXPRESS', 'PORT_JNPT', or 'L_JNPT_DEL'")
    severity: SeverityLevel
    delay_days_added: float = Field(default=2.0, ge=0.0)
    cost_surcharge_pct: float = Field(default=20.0, ge=0.0)
    capacity_reduction_pct: float = Field(default=50.0, ge=0.0, le=100.0)
    description: str = ""
    is_active: bool = True

    @property
    def carrier(self) -> Optional[str]:
        return self.target_id if self.target_type == "CARRIER" else None

    @property
    def port(self) -> Optional[str]:
        return self.target_id if self.target_type == "PORT" else None

    @property
    def delay_days(self) -> float:
        return self.delay_days_added

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["carrier"] = self.carrier
        d["port"] = self.port
        d["delay_days"] = self.delay_days_added
        return d


def get_predefined_disruptions() -> List[DisruptionEvent]:
    """Catalog of realistic Indian logistics disruptions."""
    return [
        DisruptionEvent(
            event_id="DIS-01",
            disruption_type=DisruptionType.PORT_CONGESTION,
            target_type="PORT",
            target_id="PORT_JNPT",
            severity=SeverityLevel.HIGH,
            delay_days_added=3.5,
            cost_surcharge_pct=40.0,
            capacity_reduction_pct=70.0,
            description="Severe container vessel congestion at Nhava Sheva (JNPT) terminal; gate-in delays +3.5 days."
        ),
        DisruptionEvent(
            event_id="DIS-02",
            disruption_type=DisruptionType.CARRIER_FAILURE,
            target_type="CARRIER",
            target_id="SAFEXPRESS",
            severity=SeverityLevel.CRITICAL,
            delay_days_added=5.0,
            cost_surcharge_pct=60.0,
            capacity_reduction_pct=100.0,
            description="All-India transporter driver strike at Safexpress depots; operations completely halted."
        ),
        DisruptionEvent(
            event_id="DIS-03",
            disruption_type=DisruptionType.PORT_CONGESTION,
            target_type="PORT",
            target_id="PORT_MUNDRA",
            severity=SeverityLevel.MEDIUM,
            delay_days_added=2.0,
            cost_surcharge_pct=25.0,
            capacity_reduction_pct=45.0,
            description="Customs electronic clearance server outage at Mundra Port; clearance backlog of 2 days."
        ),
        DisruptionEvent(
            event_id="DIS-04",
            disruption_type=DisruptionType.ROUTE_CLOSURE,
            target_type="LINK",
            target_id="L_JNPT_DEL",
            severity=SeverityLevel.HIGH,
            delay_days_added=3.0,
            cost_surcharge_pct=35.0,
            capacity_reduction_pct=80.0,
            description="Monsoon flooding and bridge repair on NH-48 Gujarat-Maharashtra corridor; heavy detour required."
        ),
        DisruptionEvent(
            event_id="DIS-05",
            disruption_type=DisruptionType.CARRIER_FAILURE,
            target_type="CARRIER",
            target_id="DELHIVERY",
            severity=SeverityLevel.MEDIUM,
            delay_days_added=2.0,
            cost_surcharge_pct=20.0,
            capacity_reduction_pct=50.0,
            description="Fleet maintenance and sorting hub technical failure at Delhivery Bilaspur sortation center."
        ),
    ]
