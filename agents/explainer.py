"""Agent 6: Bilingual Dispatch Explainer & Courier Manifest Generator.

Translates verified mathematical solver outputs into executive briefings and
warehouse handover slips in both English and Hindi.
Strict Rule: No mathematical hallucination. Grounded strictly in solver data.
"""

from typing import Dict
from agents.state import IndianLogisticsState


def generate_bilingual_briefings(state: IndianLogisticsState) -> Dict[str, str]:
    """Generate English and Hindi operational dispatch manifests."""
    plan = state.get("dispatch_plan")
    if not plan:
        return {"briefing_en": "No dispatch plan available.", "briefing_hi": "कोई डिस्पैच योजना उपलब्ध नहीं है।"}

    carrier_lines_en = [f"- **{carrier}**: {count} parcels" for carrier, count in plan.carrier_utilization.items() if count > 0]
    carrier_summary_en = "\n".join(carrier_lines_en) if carrier_lines_en else "- No carrier assigned"

    # English Briefing
    briefing_en = (
        f"### 📦 Dispatch Manifest & RTO Mitigation Summary\n\n"
        f"- **Total Consignments Evaluated**: {len(state.get('raw_orders', []))}\n"
        f"- **Parcels Dispatched**: {plan.parcels_dispatched}\n"
        f"- **Pre-Shipment Buyer Cancellations**: {plan.parcels_cancelled_prevented_rto} (saved forward + reverse freight)\n"
        f"- **COD to UPI Prepaid Conversions**: {plan.upi_converted_count}\n"
        f"- **Total Outbound Logistics Spend**: ₹{plan.total_shipping_spend_inr:,.2f}\n"
        f"- **Expected RTO Financial Loss**: ₹{plan.total_expected_rto_cost_inr:,.2f}\n"
        f"- **Estimated RTO Cost Savings vs Blind Dispatch**: **₹{plan.rto_cost_savings_inr:,.2f}**\n\n"
        f"#### Carrier Hub Allocation Breakdown:\n{carrier_summary_en}\n"
    )

    carrier_names_hi = {
        "DELHIVERY": "डेल्हीवरी (Delhivery)",
        "BLUEDART": "ब्लू डार्ट एयर (Blue Dart)",
        "SHADOWFAX": "शैडोफैक्स (Shadowfax)",
        "XPRESSBEES": "एक्सप्रेसबीज (Xpressbees)",
        "ECOM_EXPRESS": "ईकॉम एक्सप्रेस (Ecom Express)"
    }
    carrier_lines_hi = [
        f"- **{carrier_names_hi.get(c, c)}**: {count} पार्सल"
        for c, count in plan.carrier_utilization.items() if count > 0
    ]
    carrier_summary_hi = "\n".join(carrier_lines_hi) if carrier_lines_hi else "- कोई कोरियर आवंटित नहीं"

    # Hindi Briefing (डिस्पैच सारांश)
    briefing_hi = (
        f"### 🇮🇳 डिस्पैच मैनिफेस्ट एवं कोरियर आवंटन विवरण\n\n"
        f"- **कुल प्राप्त ऑर्डर्स**: {len(state.get('raw_orders', []))}\n"
        f"- **स्वीकृत एवं डिस्पैच पार्सल**: {plan.parcels_dispatched}\n"
        f"- **प्री-डिस्पैच ग्राहक द्वारा रद्द**: {plan.parcels_cancelled_prevented_rto} (आने-जाने का मालभाड़ा बचाया गया)\n"
        f"- **COD से UPI प्रीपेड में परिवर्तित**: {plan.upi_converted_count} ऑर्डर्स\n"
        f"- **कुल अनुमानित फ्रेट खर्च**: ₹{plan.total_shipping_spend_inr:,.2f}\n"
        f"- **अनुमानित RTO वापसी नुकसान**: ₹{plan.total_expected_rto_cost_inr:,.2f}\n"
        f"- **कुल बचत (सामान्य डिस्पैच की तुलना में)**: **₹{plan.rto_cost_savings_inr:,.2f}**\n\n"
        f"#### कोरियर पार्टनर वार पार्सल आवंटन:\n{carrier_summary_hi}\n"
    )

    return {
        "briefing_en": briefing_en,
        "briefing_hi": briefing_hi
    }


def explainer_node(state: IndianLogisticsState) -> Dict:
    """LangGraph node: Produce bilingual briefing manifests."""
    briefings = generate_bilingual_briefings(state)
    plan = state.get("dispatch_plan")
    if plan:
        plan.bilingual_briefing_en = briefings["briefing_en"]
        plan.bilingual_briefing_hi = briefings["briefing_hi"]

    return {
        "briefing_en": briefings["briefing_en"],
        "briefing_hi": briefings["briefing_hi"],
        "dispatch_plan": plan
    }
