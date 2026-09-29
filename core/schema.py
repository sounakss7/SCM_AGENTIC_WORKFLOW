from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class DisruptionType(str, Enum):
    PORT_CONGESTION = "PORT_CONGESTION"
    CARRIER_FAILURE = "CARRIER_FAILURE"
    SUPPLIER_DELAY = "SUPPLIER_DELAY"
    DEMAND_SPIKE = "DEMAND_SPIKE"
    SEVERE_WEATHER = "SEVERE_WEATHER"

class CustomerTier(str, Enum):
    STANDARD = "Standard"
    PREMIUM = "Premium"
    VIP = "VIP"

class ShippingMode(str, Enum):
    STANDARD = "Standard Class"
    SECOND_DAY = "Second Class"
    FIRST_CLASS = "First Class"
    SAME_DAY = "Same Day"

class RecoveryActionType(str, Enum):
    DO_NOTHING = "DO_NOTHING"
    STANDARD_REROUTE = "STANDARD_REROUTE"
    EXPEDITE_AIR = "EXPEDITE_AIR"
    ALTERNATE_SUPPLIER = "ALTERNATE_SUPPLIER"
    SPLIT_EXPEDITE = "SPLIT_EXPEDITE"

class DisruptionEvent(BaseModel):
    event_id: str
    disruption_type: DisruptionType
    location: str
    severity: float = Field(default=0.7, ge=0.0, le=1.0, description="Severity multiplier 0.0 to 1.0")
    duration_days: int = Field(default=7, ge=1, le=60)
    affected_carrier: Optional[str] = None
    affected_warehouse: Optional[str] = None
    description: str

class OrderRecord(BaseModel):
    order_id: str
    customer_id: str
    customer_state: str
    customer_country: str = "United States"
    customer_tier: CustomerTier = CustomerTier.STANDARD
    product_id: int
    product_name: str
    category_name: str
    quantity: int = Field(default=1, ge=1)
    unit_price: float = Field(default=50.0, ge=0.0)
    total_value: float = Field(default=50.0, ge=0.0)
    shipping_mode: ShippingMode = ShippingMode.STANDARD
    scheduled_days: int = Field(default=4, ge=0)
    real_days: int = Field(default=4, ge=0)
    late_delivery_risk: int = Field(default=0, ge=0, le=1)
    origin_warehouse: str = "Pacific_Hub_LA"
    destination: str = "CA"
    status: str = "PENDING"
    
    # SLA penalty parameters
    daily_late_penalty_rate: float = Field(default=15.0, description="Penalty in USD per day late")
    cancellation_threshold_days: int = Field(default=10, description="Max delay before order is cancelled with full refund penalty")

class RiskAssessment(BaseModel):
    affected_orders_count: int
    total_value_at_risk: float
    base_delay_days: float
    base_penalty_exposure: float
    high_priority_orders_count: int
    summary: str

class OptimizationConstraints(BaseModel):
    max_budget: Optional[float] = None
    min_service_level_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Minimum on-time delivery percentage constraint")
    max_air_freight_units: int = Field(default=150, description="Global air cargo capacity limit (units)")
    warehouse_divert_capacities: Dict[str, int] = Field(
        default_factory=lambda: {
            "Midwest_Hub_Chicago": 250,
            "EastCoast_Hub_NJ": 200,
            "South_Hub_Dallas": 200,
            "Europe_Hub_Rotterdam": 100
        }
    )
    alternate_supplier_capacities: Dict[str, int] = Field(
        default_factory=lambda: {
            "Supplier_Alpha_Domestic": 120,
            "Supplier_Beta_Regional": 100,
            "Supplier_Gamma_AirBridge": 80
        }
    )

class OrderAllocation(BaseModel):
    order_id: str
    product_name: str
    quantity: int
    selected_action: RecoveryActionType
    recovery_cost: float
    expected_delay_days: int
    incurred_penalty: float
    total_cost: float
    on_time: bool
    fulfillment_node: str
    routing_notes: str

class OptimizedPlan(BaseModel):
    plan_id: str
    scenario_id: str
    status: str = "OPTIMAL"  # OPTIMAL, INFEASIBLE, FEASIBLE_RELAXED
    solver_time_sec: float
    total_recovery_cost: float
    total_penalty_cost: float
    total_combined_cost: float
    average_delay_days: float
    service_level_pct: float
    orders_on_time: int
    orders_delayed: int
    is_feasible: bool
    allocations: List[OrderAllocation] = Field(default_factory=list)
    capacity_utilization: Dict[str, float] = Field(default_factory=dict)

class CriticVerdict(BaseModel):
    is_feasible: bool
    violation_details: List[str] = Field(default_factory=list)
    retry_recommended: bool = False
    retry_count: int = 0
    suggested_constraint_adjustments: Dict[str, Any] = Field(default_factory=dict)

class AuditLogEntry(BaseModel):
    entry_id: str
    timestamp: str
    scenario_id: str
    phase: str
    agent_name: str
    action_taken: str
    model_used: str
    cost_impact: float
    requires_approval: bool
    approval_status: str  # AUTO_APPROVED, PENDING, APPROVED, REJECTED
    details: str
