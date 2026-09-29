from typing import TypedDict, List, Dict, Any, Optional
from core.schema import (
    DisruptionEvent,
    OrderRecord,
    RiskAssessment,
    OptimizationConstraints,
    OptimizedPlan,
    CriticVerdict
)

class DisruptionState(TypedDict):
    """LangGraph state schema for Supply Chain Disruption Response Engine."""
    scenario_id: str
    disruption_event: DisruptionEvent
    affected_orders: List[OrderRecord]
    risk_assessment: Optional[RiskAssessment]
    constraints: OptimizationConstraints
    optimized_plan: Optional[OptimizedPlan]
    critic_verdict: Optional[CriticVerdict]
    explanation: str
    requires_human_approval: bool
    approval_status: str  # AUTO_APPROVED, PENDING, APPROVED, REJECTED
    retry_count: int
    llm_call_count: int
    audit_trail: List[Dict[str, Any]]
