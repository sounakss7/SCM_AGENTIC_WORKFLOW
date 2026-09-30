"""State Definition for the 5-Agent Supply Chain Resilience LangGraph Workflow.

Typed state ensuring complete auditability, clear contract across all agents,
and explicit telemetry on model calls (Gemini vs Groq).
"""

from typing import TypedDict, Optional, Dict, Any, List


class DisruptionWorkflowState(TypedDict, total=False):
    # Order Context
    order_id: str
    sku_id: str
    quantity: int
    source_supplier: str
    target_retailer: str

    # Network baseline
    nominal_plan: Optional[Dict[str, Any]]

    # Disruption Context
    disruption: Optional[Dict[str, Any]]
    disruption_detected: bool

    # Agent 2: Risk Assessor (Gemini 2.5 Flash)
    risk_assessment: Optional[Dict[str, Any]]

    # Agent 3: Routing & Decision Core (Deterministic Solver)
    proposed_plan: Optional[Dict[str, Any]]

    # Agent 4: Validator (Groq LPU low latency)
    validation_result: Optional[Dict[str, Any]]
    retry_count: int
    max_retries: int

    # Agent 5: Explainer (Gemini 2.5 Flash)
    explanation: Optional[str]

    # Final Outcome & Telemetry
    final_plan: Optional[Dict[str, Any]]
    status: str  # "NOMINAL", "DISRUPTED", "RE-ROUTING", "VALIDATED", "FAILED"
    agent_logs: List[Dict[str, Any]]
    model_records: List[Dict[str, Any]]
