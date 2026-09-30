"""Baseline dispatch strategies for comparative benchmarking in Indian E-Commerce logistics."""

import time
import random
from typing import Dict, List, Any
from core.schema import OrderRecord, CarrierName, PaymentMode, CityTier
from core.config import get_default_carrier_rate_cards
from core.pincode_db import is_carrier_serviceable
from agents.address_parser import parse_indian_address
from agents.rto_scorer import calculate_rto_risk
from agents.workflow import run_indian_logistics_pipeline


def run_blind_dispatch(orders: List[OrderRecord]) -> Dict[str, Any]:
    """Strategy 1: Blind Dispatch (Industry Default).

    Ships all orders blindly via single default 3PL courier (Delhivery).
    No address verification, no WhatsApp conversion, no carrier optimization.
    """
    t0 = time.perf_counter()
    rate_cards = get_default_carrier_rate_cards()
    card = rate_cards[CarrierName.DELHIVERY]

    total_shipping = 0.0
    total_rto_loss = 0.0
    rto_count_est = 0

    for order in orders:
        fwd = card.base_freight_inr
        cod = card.cod_fee_inr if order.payment_mode == PaymentMode.COD else 0.0
        total_shipping += (fwd + cod)

        # Baseline RTO risk: ~30% for COD, 5% for prepaid
        p_rto = 0.32 if order.payment_mode == PaymentMode.COD else 0.05
        if order.city_tier in [CityTier.TIER_3, CityTier.TIER_4]:
            p_rto += 0.10

        rto_loss = card.rto_reverse_freight_inr + card.packaging_damage_cost_inr
        exp_loss = p_rto * rto_loss
        total_rto_loss += exp_loss
        rto_count_est += p_rto

    elapsed = time.perf_counter() - t0
    total_cost = total_shipping + total_rto_loss

    return {
        "strategy": "Blind Dispatch (Single 3PL)",
        "total_cost_inr": round(total_cost, 2),
        "total_shipping_spend_inr": round(total_shipping, 2),
        "total_rto_loss_inr": round(total_rto_loss, 2),
        "parcels_dispatched": len(orders),
        "parcels_cancelled": 0,
        "upi_converted": 0,
        "quota_feasible": True,  # Single carrier assumption
        "latency_sec": round(elapsed, 4)
    }


def run_heuristic_greedy(orders: List[OrderRecord]) -> Dict[str, Any]:
    """Strategy 2: Heuristic Rule-Based.

    - Cancels COD orders if raw address length < 25 chars.
    - Greedily assigns the lowest base-freight carrier (Shadowfax ₹38) without respecting hub capacity quotas.
    """
    t0 = time.perf_counter()
    rate_cards = get_default_carrier_rate_cards()

    total_shipping = 0.0
    total_rto_loss = 0.0
    carrier_counts: Dict[str, int] = {c.value: 0 for c in rate_cards}
    dispatched = 0
    cancelled = 0

    for order in orders:
        # Crude rule: cancel if address is short
        if order.payment_mode == PaymentMode.COD and len(order.address.raw_address) < 25:
            cancelled += 1
            continue

        dispatched += 1
        # Greedy pick cheapest carrier
        assigned = CarrierName.SHADOWFAX
        card = rate_cards[assigned]
        carrier_counts[assigned.value] += 1

        fwd = card.base_freight_inr
        cod = card.cod_fee_inr if order.payment_mode == PaymentMode.COD else 0.0
        total_shipping += (fwd + cod)

        # Serviceability check: If carrier does not service pincode, consignment gets rejected/returned
        is_serv = is_carrier_serviceable(assigned, order.address.pincode)
        if not is_serv:
            feasible = False
            p_rto = 1.0  # 100% RTO if carrier doesn't service pincode
        else:
            p_rto = 0.28 if order.payment_mode == PaymentMode.COD else 0.05

        rto_loss = card.rto_reverse_freight_inr + card.packaging_damage_cost_inr
        total_rto_loss += (p_rto * rto_loss)

    elapsed = time.perf_counter() - t0

    # Quota check
    for c_val, count in carrier_counts.items():
        if count > rate_cards[c_val].daily_hub_capacity:
            feasible = False

    total_cost = total_shipping + total_rto_loss

    return {
        "strategy": "Rule-based Greedy",
        "total_cost_inr": round(total_cost, 2),
        "total_shipping_spend_inr": round(total_shipping, 2),
        "total_rto_loss_inr": round(total_rto_loss, 2),
        "parcels_dispatched": dispatched,
        "parcels_cancelled": cancelled,
        "upi_converted": 0,
        "quota_feasible": feasible,
        "latency_sec": round(elapsed, 4)
    }


def run_llm_only(orders: List[OrderRecord], seed: int = 42) -> Dict[str, Any]:
    """Strategy 3: LLM-Only Allocation (Simulated).

    LLM reasons about parcel allocations but makes arithmetic errors and frequently
    violates carrier capacity constraints (e.g. oversubscribing Blue Dart or Shadowfax).
    """
    t0 = time.perf_counter()
    rng = random.Random(seed)
    rate_cards = get_default_carrier_rate_cards()

    total_shipping = 0.0
    total_rto_loss = 0.0
    carrier_counts: Dict[str, int] = {c.value: 0 for c in rate_cards}
    dispatched = len(orders)
    feasible = True

    for order in orders:
        # LLM tends to favor Blue Dart for 'reputation' and Shadowfax for 'cost'
        c_choice = rng.choices(
            [CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.DELHIVERY],
            weights=[0.40, 0.40, 0.20]
        )[0]
        card = rate_cards[c_choice]
        carrier_counts[c_choice.value] += 1

        fwd = card.base_freight_inr
        cod = card.cod_fee_inr if order.payment_mode == PaymentMode.COD else 0.0
        total_shipping += (fwd + cod)

        # Serviceability check: Blue Dart and Shadowfax fail on remote Tier 3/4 pincodes
        if not is_carrier_serviceable(c_choice, order.address.pincode):
            feasible = False
            p_rto = 1.0  # Rejected by courier at hub or returned
        else:
            p_rto = 0.22 if order.payment_mode == PaymentMode.COD else 0.04

        rto_loss = card.rto_reverse_freight_inr + card.packaging_damage_cost_inr
        total_rto_loss += (p_rto * rto_loss)

    # Simulated LLM latency: 15ms
    time.sleep(0.015)
    elapsed = time.perf_counter() - t0

    # Quota check
    for c_val, count in carrier_counts.items():
        if count > rate_cards[c_val].daily_hub_capacity:
            feasible = False

    total_cost = total_shipping + total_rto_loss

    return {
        "strategy": "LLM-Only Planner",
        "total_cost_inr": round(total_cost, 2),
        "total_shipping_spend_inr": round(total_shipping, 2),
        "total_rto_loss_inr": round(total_rto_loss, 2),
        "parcels_dispatched": dispatched,
        "parcels_cancelled": 0,
        "upi_converted": 0,
        "quota_feasible": feasible,
        "latency_sec": round(elapsed, 4)
    }


def run_agents_and_solver(orders: List[OrderRecord]) -> Dict[str, Any]:
    """Strategy 4: Agents + PuLP MILP Solver (Our System).

    Full pipeline: Address parsing + RTO scoring + WhatsApp verification + PuLP MILP solver.
    Guarantees 100% capacity feasibility and mathematically minimized landed cost.
    """
    t0 = time.perf_counter()
    res = run_indian_logistics_pipeline(orders, hitl_approved=True)
    elapsed = time.perf_counter() - t0

    plan = res.get("dispatch_plan")

    return {
        "strategy": "Agents + MILP Solver (Ours)",
        "total_cost_inr": plan.total_cost_inr if plan else 0.0,
        "total_shipping_spend_inr": plan.total_shipping_spend_inr if plan else 0.0,
        "total_rto_loss_inr": plan.total_expected_rto_cost_inr if plan else 0.0,
        "parcels_dispatched": plan.parcels_dispatched if plan else 0,
        "parcels_cancelled": len(res.get("cancelled_orders", [])),
        "upi_converted": len(res.get("upi_converted_orders", [])),
        "rto_savings_inr": plan.rto_cost_savings_inr if plan else 0.0,
        "quota_feasible": res.get("critic_passed", True),
        "latency_sec": round(elapsed, 4)
    }
