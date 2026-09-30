"""Agent 2: COD RTO Risk Scorer & Financial Margin Assessor.

Computes multi-factor RTO risk probability based on:
- Payment mode (COD vs Prepaid UPI)
- City Tier (Tier 1 vs Tier 4 Bharat)
- Address Quality Score & Landmark existence
- Product category return tendencies (Apparel/Footwear highest in India)
- Historical customer return track record
- Order cart value (High-value COD hesitation factor)
"""

from typing import Dict
from core.schema import OrderRecord, PaymentMode, CityTier, ProductCategory
from agents.state import IndianLogisticsState


def calculate_rto_risk(order: OrderRecord, address_score: float) -> float:
    """Predict RTO probability P(RTO) bounded in [0.02, 0.95]."""
    # 1. Base probability by payment mode
    if order.payment_mode in [PaymentMode.PREPAID_UPI, PaymentMode.PREPAID_CARD, PaymentMode.PREPAID_NETBANKING]:
        base_p = 0.05  # Prepaid buyers rarely reject at doorstep
    else:
        base_p = 0.28  # Industry average for Indian COD e-commerce

    # 2. Regional / City Tier Modifier
    tier_mods = {
        CityTier.TIER_1: -0.05,
        CityTier.TIER_2: 0.00,
        CityTier.TIER_3: 0.08,
        CityTier.TIER_4: 0.16
    }
    base_p += tier_mods.get(order.city_tier, 0.05)

    # 3. Address Completeness Modifier
    if address_score >= 0.85:
        base_p -= 0.08
    elif address_score >= 0.60:
        base_p -= 0.02
    elif address_score < 0.40:
        base_p += 0.18
    else:
        base_p += 0.06

    # 4. Product Category Tendency
    cat_mods = {
        ProductCategory.APPAREL: 0.08,
        ProductCategory.FOOTWEAR: 0.06,
        ProductCategory.ELECTRONICS: -0.04,
        ProductCategory.BEAUTY_WELLNESS: -0.02,
        ProductCategory.HOME_KITCHEN: 0.00,
        ProductCategory.GROCERY: -0.05
    }
    base_p += cat_mods.get(order.category, 0.0)

    # 5. Customer Historical Reputation
    if order.past_rto_count > 0:
        base_p += min(0.30, order.past_rto_count * 0.10)
    elif order.past_orders_count >= 3:
        base_p -= 0.07

    # 6. Order Value Impact on COD
    if order.payment_mode == PaymentMode.COD:
        if order.order_value_inr > 3500.0:
            base_p += 0.10  # Reluctance to pay large cash sums at door
        elif order.order_value_inr < 500.0:
            base_p += 0.05  # Frivolous impulse purchases

    return round(min(0.95, max(0.02, base_p)), 3)


def rto_scorer_node(state: IndianLogisticsState) -> Dict:
    """LangGraph node: Calculate RTO risk and expected margin for all orders."""
    risk_scores: Dict[str, float] = {}
    margins: Dict[str, float] = {}

    for order in state["raw_orders"]:
        addr_score = state["address_scores"].get(order.order_id, 0.5)
        p_rto = calculate_rto_risk(order, addr_score)
        risk_scores[order.order_id] = p_rto

        # Expected Margin (Assuming 35% gross profit margin on merchandise)
        gross_margin = 0.35 * order.order_value_inr
        estimated_rto_loss = 150.0  # ₹ Forward + Reverse + Damage
        exp_margin = ((1.0 - p_rto) * gross_margin) - (p_rto * estimated_rto_loss)
        margins[order.order_id] = round(exp_margin, 2)

    return {
        "rto_risk_scores": risk_scores,
        "expected_margins": margins
    }
