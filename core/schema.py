"""Pydantic v2 domain schemas for Indian E-Commerce COD RTO & Last-Mile Allocation Engine.

Models the complete Indian e-commerce fulfillment lifecycle:
- Indian address parsing (chaotic landmarks, 6-digit PIN codes)
- Payment modes (COD, UPI Prepaid)
- WhatsApp pre-shipment buyer verification (Hindi, Hinglish, English)
- Carrier rate cards (Delhivery, Blue Dart, Shadowfax, Xpressbees, Ecom Express)
- PuLP deterministic carrier allocation results
- Immutable audit ledger entries
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class CityTier(str, Enum):
    TIER_1 = "TIER_1"  # Delhi, Mumbai, Bengaluru, Chennai, Kolkata, Hyderabad, Pune, Ahmedabad
    TIER_2 = "TIER_2"  # Jaipur, Lucknow, Patna, Surat, Indore, Chandigarh, Kochi, etc.
    TIER_3 = "TIER_3"  # Muzaffarpur, Gorakhpur, Alwar, Salem, etc.
    TIER_4 = "TIER_4"  # Rural & semi-urban talukas


class PaymentMode(str, Enum):
    COD = "COD"
    PREPAID_UPI = "PREPAID_UPI"
    PREPAID_CARD = "PREPAID_CARD"
    PREPAID_NETBANKING = "PREPAID_NETBANKING"


class AddressQualityTier(str, Enum):
    HIGH = "HIGH"          # House number + Landmark + Complete Locality + Valid PIN (Score >= 0.8)
    MEDIUM = "MEDIUM"      # Landmark present, vague house number (Score 0.5 - 0.8)
    LOW = "LOW"            # No landmark, vague street/area (Score 0.3 - 0.5)
    CRITICAL = "CRITICAL"  # Missing locality/landmark, suspicious text (Score < 0.3)


class ProductCategory(str, Enum):
    APPAREL = "APPAREL"
    ELECTRONICS = "ELECTRONICS"
    BEAUTY_WELLNESS = "BEAUTY_WELLNESS"
    FOOTWEAR = "FOOTWEAR"
    HOME_KITCHEN = "HOME_KITCHEN"
    GROCERY = "GROCERY"


class IndianAddress(BaseModel):
    raw_address: str = Field(..., description="Raw unstructured Indian address text as entered by customer")
    house_no: Optional[str] = Field(default=None, description="Extracted House / Flat / Plot number")
    landmark: Optional[str] = Field(default=None, description="Extracted Landmark (e.g. Near Shiv Mandir, Behind Sweet Shop)")
    locality: Optional[str] = Field(default=None, description="Extracted Locality / Sector / Mohalla / Gali")
    city: str = Field(..., description="City or District")
    state: str = Field(..., description="Indian State or Union Territory")
    pincode: str = Field(..., description="6-digit Indian Postal Code")
    has_landmark: bool = Field(default=False, description="Flag indicating if a recognizable landmark is present")
    address_completeness_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Quality score 0.0 to 1.0")
    quality_tier: AddressQualityTier = Field(default=AddressQualityTier.LOW)
    extracted_entities: Dict[str, str] = Field(default_factory=dict)


class OrderRecord(BaseModel):
    order_id: str = Field(..., description="Unique Order Identifier (e.g. ORD-IND-8021)")
    customer_id: str = Field(..., description="Customer UUID or Phone Number")
    customer_name: str = Field(..., description="Customer full name")
    phone: str = Field(..., description="10-digit Indian Mobile Number (e.g. +91 9876543210)")
    payment_mode: PaymentMode = Field(..., description="Payment method (COD vs Prepaid)")
    city_tier: CityTier = Field(..., description="City tier of shipping destination")
    address: IndianAddress = Field(..., description="Structured Indian address")
    category: ProductCategory = Field(..., description="Merchandise product category")
    order_value_inr: float = Field(..., ge=0.0, description="Gross merchandise value in Indian Rupees (₹)")
    item_weight_grams: int = Field(default=500, ge=100, description="Package weight in grams")
    past_orders_count: int = Field(default=0, ge=0, description="Lifetime orders placed by customer")
    past_rto_count: int = Field(default=0, ge=0, description="Lifetime RTO orders by customer")
    max_delivery_days: int = Field(default=5, ge=1, le=14, description="Contractual or promised SLA days")
    created_at: str = Field(default="", description="ISO timestamp")


class WhatsAppLanguage(str, Enum):
    ENGLISH = "ENGLISH"
    HINDI = "HINDI"
    HINGLISH = "HINGLISH"


class WhatsAppAction(str, Enum):
    CONFIRMED_ADDRESS = "CONFIRMED_ADDRESS"
    CONVERTED_PREPAID_UPI = "CONVERTED_PREPAID_UPI"
    CANCELLED_ORDER = "CANCELLED_ORDER"
    NO_RESPONSE = "NO_RESPONSE"


class WhatsAppVerificationResult(BaseModel):
    order_id: str
    attempt_count: int = 1
    language: WhatsAppLanguage = WhatsAppLanguage.HINGLISH
    chat_transcript: List[Dict[str, str]] = Field(default_factory=list, description="Role & content messages")
    action_taken: WhatsAppAction = WhatsAppAction.NO_RESPONSE
    revised_payment_mode: PaymentMode = PaymentMode.COD
    discount_applied_inr: float = Field(default=0.0, ge=0.0, description="Instant UPI discount in ₹ if converted")
    gps_lat_lng_shared: bool = Field(default=False, description="Whether customer provided exact map location")
    address_refined: Optional[str] = None
    rto_risk_reduction_pct: float = Field(default=0.0, ge=0.0, le=100.0)


class CarrierName(str, Enum):
    DELHIVERY = "DELHIVERY"
    BLUEDART = "BLUEDART"
    SHADOWFAX = "SHADOWFAX"
    XPRESSBEES = "XPRESSBEES"
    ECOM_EXPRESS = "ECOM_EXPRESS"


class CarrierRateCard(BaseModel):
    carrier: CarrierName
    carrier_display_name: str
    base_freight_inr: float = Field(..., ge=0.0, description="Forward shipping freight per 500g in ₹")
    cod_fee_inr: float = Field(..., ge=0.0, description="COD collection fee (flat or min threshold) in ₹")
    rto_reverse_freight_inr: float = Field(..., ge=0.0, description="Reverse logistics freight charged on RTO in ₹")
    packaging_damage_cost_inr: float = Field(default=30.0, ge=0.0, description="Average packaging loss upon return")
    avg_transit_days: int = Field(..., ge=1, description="Average delivery timeline in days")
    daily_hub_capacity: int = Field(..., ge=1, description="Maximum parcels allocated per day at origin hub")
    serviceable_tiers: List[CityTier] = Field(default_factory=list, description="Tiers actively serviced")


class CarrierAllocation(BaseModel):
    order_id: str
    carrier: CarrierName
    shipping_cost_inr: float = Field(..., ge=0.0, description="Forward shipping fee in ₹")
    cod_fee_inr: float = Field(default=0.0, ge=0.0, description="COD handling fee in ₹")
    predicted_rto_risk: float = Field(..., ge=0.0, le=1.0, description="Probability of RTO (0.0 to 1.0)")
    expected_rto_cost_inr: float = Field(..., ge=0.0, description="P(RTO) * (Reverse Freight + Damage)")
    total_expected_cost_inr: float = Field(..., ge=0.0, description="Shipping + COD + Expected RTO Loss")
    estimated_delivery_days: int = Field(..., ge=1)
    status: str = Field(default="DISPATCHED", description="DISPATCHED, CANCELLED_PREVENTED_RTO, or HELD_FOR_VERIFICATION")
    rationale: str = Field(default="")


class DispatchPlan(BaseModel):
    plan_id: str
    allocations: List[CarrierAllocation] = Field(default_factory=list)
    total_shipping_spend_inr: float = Field(default=0.0, ge=0.0)
    total_expected_rto_cost_inr: float = Field(default=0.0, ge=0.0)
    total_cost_inr: float = Field(default=0.0, ge=0.0)
    parcels_dispatched: int = 0
    parcels_cancelled_prevented_rto: int = 0
    upi_converted_count: int = 0
    rto_cost_savings_inr: float = Field(default=0.0, ge=0.0, description="Estimated ₹ saved vs blind dispatch")
    carrier_utilization: Dict[str, int] = Field(default_factory=dict)
    solver_status: str = "OPTIMAL"
    hitl_approval_required: bool = False
    hitl_approval_reason: Optional[str] = None
    bilingual_briefing_en: str = ""
    bilingual_briefing_hi: str = ""


class AuditLogEntry(BaseModel):
    log_id: str
    timestamp: str
    event_type: str
    order_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    financial_impact_inr: float = 0.0
    operator_approved: bool = True
    operator_notes: Optional[str] = None
