"""Agent 3: Autonomous WhatsApp Pre-Shipment Verification Agent.

Engages high-risk COD buyers in conversational English, Hindi, or Hinglish via WhatsApp:
1. Confirms chaotic Indian addresses and prompts for recognizable landmarks or GPS pins
2. Incentivizes COD-to-UPI conversion with an instant discount (5% up to ₹50)
3. Detects buyer cancellations BEFORE parcels leave the warehouse (saving ₹180 in forward + reverse freight)
"""

import random
from typing import Dict, List, Tuple
from core.schema import (
    OrderRecord, PaymentMode, WhatsAppAction, WhatsAppLanguage, WhatsAppVerificationResult
)
from core.config import settings
from agents.state import IndianLogisticsState


def simulate_whatsapp_dialogue(
    order: OrderRecord,
    base_rto_risk: float,
    language: WhatsAppLanguage = WhatsAppLanguage.HINGLISH,
    seed: int = 42
) -> WhatsAppVerificationResult:
    """Simulate realistic Indian buyer WhatsApp interaction with Hinglish templates."""
    rng = random.Random(seed + sum(ord(c) for c in order.order_id) % 10000)

    discount_amount = min(
        settings.UPI_CONVERSION_MAX_DISCOUNT_INR,
        round(order.order_value_inr * (settings.UPI_CONVERSION_DISCOUNT_PCT / 100.0), 2)
    )

    # Outgoing WhatsApp Message Template
    if language == WhatsAppLanguage.HINDI:
        bot_msg = (
            f"नमस्ते {order.customer_name} जी! 🙏 आपका ऑर्डर #{order.order_id} (मूल्य: ₹{order.order_value_inr:.0f}) तैयार है। "
            f"डिलीवरी पता: '{order.address.raw_address}'। "
            f"कृपया पता कन्फर्म करें। तुरंत UPI से भुगतान करने पर ₹{discount_amount:.0f} की विशेष छूट पाएं!"
        )
    elif language == WhatsAppLanguage.ENGLISH:
        bot_msg = (
            f"Hello {order.customer_name}! Your order #{order.order_id} of ₹{order.order_value_inr:.0f} is ready for dispatch to: "
            f"'{order.address.raw_address}'. "
            f"Reply 1 to Confirm COD, 2 to Pay via UPI & get ₹{discount_amount:.0f} OFF, or 3 to Cancel."
        )
    else:  # HINGLISH (Default for Indian E-Commerce)
        bot_msg = (
            f"Namaste {order.customer_name} ji! 🙏 Aapka order #{order.order_id} (Amount: ₹{order.order_value_inr:.0f}) dispatch ke liye ready hai. "
            f"Shipping Address: '{order.address.raw_address}'.\n\n"
            f"👉 1. Address confirm karein aur UPI se pay karke ₹{discount_amount:.0f} instant discount payein\n"
            f"👉 2. Cash on Delivery (COD) confirm karein\n"
            f"👉 3. Order cancel karein"
        )

    # Probabilistic buyer response model based on Indian e-commerce benchmarks:
    # 25% Convert to UPI, 40% Confirm COD with landmark, 15% Cancel, 20% No response
    roll = rng.random()
    chat_transcript = [{"role": "assistant", "message": bot_msg}]

    if roll < 0.25:
        # Scenario 1: Convert to UPI
        user_msg = f"Haan main UPI se pay kar deta hoon. Send payment link."
        chat_transcript.append({"role": "user", "message": user_msg})
        chat_transcript.append({"role": "assistant", "message": f"Payment of ₹{order.order_value_inr - discount_amount:.0f} received via UPI! Your order is prioritized. 🚀"})
        return WhatsAppVerificationResult(
            order_id=order.order_id,
            language=language,
            chat_transcript=chat_transcript,
            action_taken=WhatsAppAction.CONVERTED_PREPAID_UPI,
            revised_payment_mode=PaymentMode.PREPAID_UPI,
            discount_applied_inr=discount_amount,
            gps_lat_lng_shared=True,
            rto_risk_reduction_pct=80.0
        )
    elif roll < 0.65:
        # Scenario 2: Confirm Address & provide landmark
        landmark = order.address.landmark or "Near Shiv Mandir"
        user_msg = f"Address sahi hai, {landmark} ke pass aake call karna."
        chat_transcript.append({"role": "user", "message": user_msg})
        chat_transcript.append({"role": "assistant", "message": f"Thank you {order.customer_name} ji! Delivery partner ko note de diya hai. 👍"})
        return WhatsAppVerificationResult(
            order_id=order.order_id,
            language=language,
            chat_transcript=chat_transcript,
            action_taken=WhatsAppAction.CONFIRMED_ADDRESS,
            revised_payment_mode=PaymentMode.COD,
            discount_applied_inr=0.0,
            gps_lat_lng_shared=True,
            address_refined=f"{order.address.raw_address} (Landmark Confirmed: {landmark})",
            rto_risk_reduction_pct=30.0
        )
    elif roll < 0.80:
        # Scenario 3: Cancel Order (Major RTO cost saver!)
        user_msg = f"Nahi chahiye abhi, cancel kar do."
        chat_transcript.append({"role": "user", "message": user_msg})
        chat_transcript.append({"role": "assistant", "message": "Aapka order cancel kar diya gaya hai. Koi charges nahi lageinge. Dhanyawad!"})
        return WhatsAppVerificationResult(
            order_id=order.order_id,
            language=language,
            chat_transcript=chat_transcript,
            action_taken=WhatsAppAction.CANCELLED_ORDER,
            revised_payment_mode=PaymentMode.COD,
            discount_applied_inr=0.0,
            rto_risk_reduction_pct=100.0
        )
    else:
        # Scenario 4: No Response
        return WhatsAppVerificationResult(
            order_id=order.order_id,
            language=language,
            chat_transcript=chat_transcript,
            action_taken=WhatsAppAction.NO_RESPONSE,
            revised_payment_mode=PaymentMode.COD,
            discount_applied_inr=0.0,
            rto_risk_reduction_pct=0.0
        )


def whatsapp_verification_node(state: IndianLogisticsState) -> Dict:
    """LangGraph node: Engage high-risk COD orders via WhatsApp verification."""
    results: Dict[str, WhatsAppVerificationResult] = {}
    cancelled_ids: List[str] = []
    upi_converted_ids: List[str] = []
    dispatched_candidates: List[OrderRecord] = []

    for order in state["raw_orders"]:
        p_rto = state["rto_risk_scores"].get(order.order_id, 0.3)
        addr_score = state["address_scores"].get(order.order_id, 0.5)

        # Trigger WhatsApp if COD and (High Risk or Low Address Quality)
        if order.payment_mode == PaymentMode.COD and (p_rto >= 0.40 or addr_score < 0.60):
            res = simulate_whatsapp_dialogue(order, p_rto)
            results[order.order_id] = res

            if res.action_taken == WhatsAppAction.CANCELLED_ORDER:
                cancelled_ids.append(order.order_id)
            elif res.action_taken == WhatsAppAction.CONVERTED_PREPAID_UPI:
                order.payment_mode = PaymentMode.PREPAID_UPI
                # Recalculate reduced risk
                state["rto_risk_scores"][order.order_id] = round(p_rto * 0.20, 3)
                upi_converted_ids.append(order.order_id)
                dispatched_candidates.append(order)
            elif res.action_taken == WhatsAppAction.CONFIRMED_ADDRESS:
                state["rto_risk_scores"][order.order_id] = round(p_rto * 0.70, 3)
                dispatched_candidates.append(order)
            else:
                dispatched_candidates.append(order)
        else:
            dispatched_candidates.append(order)

    return {
        "whatsapp_results": results,
        "cancelled_orders": cancelled_ids,
        "upi_converted_orders": upi_converted_ids,
        "dispatched_candidates": dispatched_candidates,
        "rto_risk_scores": state["rto_risk_scores"]
    }
