"""Typed Pydantic and TypedDict state models for Multi-Agent Supply Chain Negotiation."""

from typing import Dict, List, Optional, Any, Tuple, TypedDict
from pydantic import BaseModel, Field
from core.network import MultiEchelonNetwork
from optimizer.multi_echelon_solver import MultiEchelonSolution


class DisruptionEvent(BaseModel):
    disruption_type: str = Field(..., description="SUPPLIER_DELAY, PORT_CONGESTION, DEMAND_SPIKE, or WAREHOUSE_CAPACITY_LOSS")
    affected_entity: str = Field(..., description="e.g. 'S1', 'W1', or 'R1'")
    severity_factor: float = Field(default=1.5, description="Multiplier or magnitude of disruption")
    duration_periods: int = Field(default=2, ge=1)
    description: str = Field(default="")


class NegotiationRound(BaseModel):
    round_index: int
    procurement_focus: str
    logistics_focus: str
    conflict_identified: str
    resolution_action: str
    joint_cost_estimate: float
    service_level_estimate: float


class MultiEchelonAgentState(TypedDict):
    network: MultiEchelonNetwork
    forecast_demand: Dict[Tuple[str, str, int], Dict[str, float]]
    active_disruption: Optional[DisruptionEvent]
    procurement_proposal: Dict[str, Any]
    logistics_proposal: Dict[str, Any]
    conflict_detected: bool
    conflict_reason: str
    negotiation_round: int
    max_negotiation_rounds: int
    negotiation_log: List[Dict[str, Any]]
    joint_solution: Optional[MultiEchelonSolution]
    before_disruption_solution: Optional[MultiEchelonSolution]
    cost_delta: float
    service_delta: float
    plain_english_briefing: str
