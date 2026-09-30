"""Agent 1: Address Intelligence & Indian Entity Parser.

Parses chaotic unstructured Indian addresses containing colloquial landmarks
(e.g., 'behind Sharma sweets, near Shiv Mandir, pipal ped ke pass') and assesses
address completeness and deliverability.
"""

import re
from typing import Dict, Tuple
from core.schema import AddressQualityTier, IndianAddress
from core.pincode_db import get_pincode_info
from agents.state import IndianLogisticsState

LANDMARK_KEYWORDS = [
    r"near\b", r"opp\b", r"opposite\b", r"behind\b", r"ke peeche\b", r"ke pass\b",
    r"mandir\b", r"temple\b", r"masjid\b", r"gurudwara\b", r"church\b",
    r"school\b", r"college\b", r"hospital\b", r"phatak\b", r"tanki\b",
    r"sweets\b", r"sweet shop\b", r"kirana\b", r"general store\b", r"chowk\b",
    r"police station\b", r"thana\b", r"petrol pump\b", r"atm\b", r"bank\b",
    r"railway station\b", r"bus stand\b", r"post office\b"
]

HOUSE_PATTERNS = [
    r"(?:flat|house|h\.no|qtr|room|plot|ward)\s*(?:no\.?)?\s*([0-9a-zA-Z\-/]+)",
    r"\b([0-9]{1,4}[a-zA-Z]?/[0-9a-zA-Z]+)\b",
    r"\b([0-9]{1,4})\s*,\s*"
]


def parse_indian_address(raw_text: str, default_pin: str = "110001") -> Tuple[IndianAddress, float]:
    """Parse chaotic Indian address string and compute deliverability score."""
    text = raw_text.strip()
    entities = {}

    # Extract 6-digit PIN code
    pin_match = re.search(r"\b([1-9][0-9]{5})\b", text)
    pincode = pin_match.group(1) if pin_match else default_pin
    entities["pincode"] = pincode
    pin_meta = get_pincode_info(pincode)

    # Detect Landmark
    has_landmark = False
    detected_landmark = None

    # Check Hindi postpositional landmarks (e.g. "Shiv Mandir ke pass", "Sharma sweets ke peeche")
    post_match = re.search(r"([^,]+(?:\s+ke pass|\s+ke peeche))", text, re.IGNORECASE)
    if post_match:
        has_landmark = True
        detected_landmark = post_match.group(1).strip()
    else:
        for kw in LANDMARK_KEYWORDS:
            match = re.search(rf"((?:[a-zA-Z0-9\.]+\s+)?{kw}[^,]*)", text, re.IGNORECASE)
            if match:
                has_landmark = True
                detected_landmark = match.group(1).strip()
                break
    entities["landmark"] = detected_landmark or "NONE"

    # Detect House / Flat
    detected_house = None
    for pattern in HOUSE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            detected_house = match.group(1).strip()
            break
    entities["house_no"] = detected_house or "NOT_FOUND"

    # Scoring Algorithm (0.0 to 1.0)
    score = 0.0

    # 1. PIN code validity (+0.30)
    if pin_meta.get("city"):
        score += 0.30

    # 2. Recognizable landmark (+0.30)
    if has_landmark:
        score += 0.30

    # 3. House/Flat identification (+0.20)
    if detected_house:
        score += 0.20

    # 4. Length and detail (+0.20)
    words = text.split()
    if len(words) >= 8:
        score += 0.15
    elif len(words) >= 5:
        score += 0.10

    if len(text) > 30:
        score += 0.05

    score = round(min(1.0, max(0.10, score)), 3)

    # Determine Quality Tier
    if score >= 0.80:
        quality_tier = AddressQualityTier.HIGH
    elif score >= 0.55:
        quality_tier = AddressQualityTier.MEDIUM
    elif score >= 0.35:
        quality_tier = AddressQualityTier.LOW
    else:
        quality_tier = AddressQualityTier.CRITICAL

    address_obj = IndianAddress(
        raw_address=raw_text,
        house_no=detected_house,
        landmark=detected_landmark,
        locality=pin_meta["district"],
        city=pin_meta["city"],
        state=pin_meta["state"],
        pincode=pincode,
        has_landmark=has_landmark,
        address_completeness_score=score,
        quality_tier=quality_tier,
        extracted_entities=entities
    )

    return address_obj, score


def address_parser_node(state: IndianLogisticsState) -> Dict:
    """LangGraph node: Parse addresses for all raw orders."""
    scores: Dict[str, float] = {}
    parsed: Dict[str, Dict[str, str]] = {}

    for order in state["raw_orders"]:
        addr_obj, score = parse_indian_address(order.address.raw_address, order.address.pincode)
        order.address = addr_obj
        scores[order.order_id] = score
        parsed[order.order_id] = addr_obj.extracted_entities

    return {
        "address_scores": scores,
        "parsed_addresses": parsed,
        "raw_orders": state["raw_orders"]
    }
