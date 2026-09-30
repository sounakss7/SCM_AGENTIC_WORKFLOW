"""Unit tests for COD RTO Risk Scorer."""

from core.schema import OrderRecord, PaymentMode, CityTier, ProductCategory, IndianAddress, AddressQualityTier
from agents.rto_scorer import calculate_rto_risk


def create_dummy_order(payment_mode: PaymentMode, city_tier: CityTier, order_val: float = 1200.0) -> OrderRecord:
    addr = IndianAddress(
        raw_address="Sample Address",
        city="Test City",
        state="Test State",
        pincode="110001",
        has_landmark=True,
        address_completeness_score=0.85,
        quality_tier=AddressQualityTier.HIGH
    )
    return OrderRecord(
        order_id="ORD-TEST-001",
        customer_id="CUST-1",
        customer_name="Test User",
        phone="+91 9999999999",
        payment_mode=payment_mode,
        city_tier=city_tier,
        address=addr,
        category=ProductCategory.APPAREL,
        order_value_inr=order_val,
        past_orders_count=2,
        past_rto_count=0
    )


def test_cod_has_higher_risk_than_upi():
    order_cod = create_dummy_order(PaymentMode.COD, CityTier.TIER_1)
    order_upi = create_dummy_order(PaymentMode.PREPAID_UPI, CityTier.TIER_1)

    risk_cod = calculate_rto_risk(order_cod, 0.85)
    risk_upi = calculate_rto_risk(order_upi, 0.85)

    assert risk_cod > risk_upi
    assert risk_upi <= 0.15


def test_tier4_has_higher_risk_than_tier1():
    order_t1 = create_dummy_order(PaymentMode.COD, CityTier.TIER_1)
    order_t4 = create_dummy_order(PaymentMode.COD, CityTier.TIER_4)

    risk_t1 = calculate_rto_risk(order_t1, 0.70)
    risk_t4 = calculate_rto_risk(order_t4, 0.70)

    assert risk_t4 > risk_t1
