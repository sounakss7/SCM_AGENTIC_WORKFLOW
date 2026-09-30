"""Configuration settings and Indian 3PL Rate Cards for the RTO & Last-Mile Allocation Engine."""

from typing import Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from core.schema import CarrierName, CarrierRateCard, CityTier


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Bharat E-Commerce COD RTO & Last-Mile Allocation Engine"
    ENV: str = "production"
    DATABASE_URL: str = "sqlite:///./indian_ecom_rto.db"

    # Human-in-the-Loop (HITL) Thresholds (Indian Rupees ₹)
    HITL_ORDER_VALUE_THRESHOLD_INR: float = 5000.0
    HITL_HIGH_RISK_PROB_THRESHOLD: float = 0.60

    # WhatsApp Pre-shipment UPI Conversion Incentives
    UPI_CONVERSION_DISCOUNT_PCT: float = 5.0
    UPI_CONVERSION_MAX_DISCOUNT_INR: float = 50.0

    # LLM API Keys (Optional; deterministic heuristics trigger when absent)
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None

    # LangSmith Observability
    LANGSMITH_TRACING: bool = False
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "indian-ecom-rto-engine"


settings = Settings()


def get_default_carrier_rate_cards() -> Dict[CarrierName, CarrierRateCard]:
    """Real-world benchmark Indian 3PL courier rate cards (per 500g slab in ₹)."""
    return {
        CarrierName.DELHIVERY: CarrierRateCard(
            carrier=CarrierName.DELHIVERY,
            carrier_display_name="Delhivery Express",
            base_freight_inr=45.0,
            cod_fee_inr=35.0,
            rto_reverse_freight_inr=55.0,
            packaging_damage_cost_inr=30.0,
            avg_transit_days=3,
            daily_hub_capacity=180,
            serviceable_tiers=[CityTier.TIER_1, CityTier.TIER_2, CityTier.TIER_3, CityTier.TIER_4]
        ),
        CarrierName.BLUEDART: CarrierRateCard(
            carrier=CarrierName.BLUEDART,
            carrier_display_name="Blue Dart Air Express",
            base_freight_inr=85.0,
            cod_fee_inr=50.0,
            rto_reverse_freight_inr=90.0,
            packaging_damage_cost_inr=30.0,
            avg_transit_days=2,
            daily_hub_capacity=60,
            serviceable_tiers=[CityTier.TIER_1, CityTier.TIER_2]
        ),
        CarrierName.SHADOWFAX: CarrierRateCard(
            carrier=CarrierName.SHADOWFAX,
            carrier_display_name="Shadowfax E-Com",
            base_freight_inr=38.0,
            cod_fee_inr=30.0,
            rto_reverse_freight_inr=45.0,
            packaging_damage_cost_inr=30.0,
            avg_transit_days=4,
            daily_hub_capacity=120,
            serviceable_tiers=[CityTier.TIER_1, CityTier.TIER_2, CityTier.TIER_3]
        ),
        CarrierName.XPRESSBEES: CarrierRateCard(
            carrier=CarrierName.XPRESSBEES,
            carrier_display_name="Xpressbees Logistics",
            base_freight_inr=42.0,
            cod_fee_inr=32.0,
            rto_reverse_freight_inr=50.0,
            packaging_damage_cost_inr=30.0,
            avg_transit_days=4,
            daily_hub_capacity=140,
            serviceable_tiers=[CityTier.TIER_1, CityTier.TIER_2, CityTier.TIER_3, CityTier.TIER_4]
        ),
        CarrierName.ECOM_EXPRESS: CarrierRateCard(
            carrier=CarrierName.ECOM_EXPRESS,
            carrier_display_name="Ecom Express Bharat",
            base_freight_inr=44.0,
            cod_fee_inr=32.0,
            rto_reverse_freight_inr=52.0,
            packaging_damage_cost_inr=30.0,
            avg_transit_days=4,
            daily_hub_capacity=150,
            serviceable_tiers=[CityTier.TIER_1, CityTier.TIER_2, CityTier.TIER_3, CityTier.TIER_4]
        ),
    }
