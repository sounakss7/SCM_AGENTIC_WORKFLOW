"""Indian E-Commerce Order Dataset Loader and Realistic Order Generator.

Generates realistic, nuanced Indian e-commerce consignments exhibiting:
- Real chaotic Indian address variations (landmarks, colloquial phrasing, missing street numbers)
- Distribution of 6-digit Indian PIN codes across Tiers 1, 2, 3, and 4
- Indian payment modes (65% COD vs 35% UPI/Prepaid)
- Historical customer return behavior & category-specific return patterns (Apparel/Footwear highest)
"""

import random
from typing import List
from core.schema import (
    OrderRecord, IndianAddress, PaymentMode, CityTier, ProductCategory, AddressQualityTier
)
from core.pincode_db import PINCODE_REGISTRY, get_pincode_info

INDIAN_NAMES = [
    "Rahul Sharma", "Priya Verma", "Mohammad Rizwan", "Ananya Sundaram", "Vikram Rathore",
    "Pooja Patel", "Amitabh Banerjee", "Deepak Yadav", "Sunita Devi", "Rohan Kulkarni",
    "Kavita Nair", "Arjun Reddy", "Harpreet Singh", "Neha Gupta", "Suresh Choudhary",
    "Manish Tiwari", "Ritu Mishra", "Sanjay Joshi", "Sneha Iyer", "Rajesh Das"
]

CHAOTIC_ADDRESS_TEMPLATES = [
    # High Quality (Landmark + House No + Area)
    ("{house}, {society}, Near {landmark}, {locality}, {city}, {state}", AddressQualityTier.HIGH, 0.92, True),
    ("Flat No. {house}, Tower B, Opp. {landmark}, {locality}, {city}, {state}", AddressQualityTier.HIGH, 0.88, True),

    # Medium Quality (Vague house number, prominent landmark)
    ("Behind {landmark}, Gali No. {gali}, {locality}, {city}, {state}", AddressQualityTier.MEDIUM, 0.68, True),
    ("Near {landmark}, {locality}, Main Road, {city}, {state}", AddressQualityTier.MEDIUM, 0.62, True),
    ("C/O Sharma Niwas, Near {landmark}, {locality}, {city}, {state}", AddressQualityTier.MEDIUM, 0.70, True),

    # Low Quality (Colloquial landmark, no house number)
    ("{landmark} ke peeche, Lal building, {locality}, {city}, {state}", AddressQualityTier.LOW, 0.42, True),
    ("Near purani paani ki tanki, {locality}, {city}, {state}", AddressQualityTier.LOW, 0.38, True),
    ("Station Road, Near {landmark}, {city}, {state}", AddressQualityTier.LOW, 0.45, True),

    # Critical Quality (Missing landmark, minimal information)
    ("Ward No. {gali}, {locality}, {city}, {state}", AddressQualityTier.CRITICAL, 0.25, False),
    ("Near bus stand, {city}, {state}", AddressQualityTier.CRITICAL, 0.18, False),
    ("{locality}, {city}, {state}", AddressQualityTier.CRITICAL, 0.15, False)
]

LANDMARKS = [
    "Shiv Mandir", "Hanuman Mandir", "Gulab Sweets", "HDFC Bank ATM", "Railway Phatak",
    "Government Primary School", "Pipal ka ped", "Water Tanki", "Sharma General Store",
    "District Hospital", "Police Chowki", "Bata Shoe Store", "Post Office"
]

LOCALITIES = [
    "Civil Lines", "Gandhi Nagar", "Koramangala", "Shastri Nagar", "Sector 15",
    "Raja Bazar", "Indira Nagar", "Model Town", "Station Para", "Subhash Nagar",
    "Ashok Vihar", "Patel Nagar", "Boring Road", "Salt Lake Sector 2"
]


def generate_indian_orders(count: int = 50, seed: int = 42) -> List[OrderRecord]:
    """Deterministically synthesize representative Indian e-commerce orders."""
    rng = random.Random(seed)
    pincode_list = list(PINCODE_REGISTRY.keys())
    categories = [
        (ProductCategory.APPAREL, 0.35),
        (ProductCategory.FOOTWEAR, 0.20),
        (ProductCategory.ELECTRONICS, 0.15),
        (ProductCategory.BEAUTY_WELLNESS, 0.15),
        (ProductCategory.HOME_KITCHEN, 0.15)
    ]

    orders: List[OrderRecord] = []

    for i in range(1, count + 1):
        order_id = f"ORD-IND-{1000 + i}"
        customer_name = rng.choice(INDIAN_NAMES)
        customer_id = f"CUST-{rng.randint(10000, 99999)}"
        phone = f"+91 {rng.randint(70000, 99999)}{rng.randint(10000, 99999)}"

        # Realistic Indian payment split: 65% COD, 35% Prepaid UPI/Card
        is_cod = rng.random() < 0.65
        payment_mode = PaymentMode.COD if is_cod else rng.choice([PaymentMode.PREPAID_UPI, PaymentMode.PREPAID_CARD])

        # Pick random PIN code from registry
        pincode = rng.choice(pincode_list)
        pin_meta = get_pincode_info(pincode)
        city = pin_meta["city"]
        state = pin_meta["state"]
        city_tier = pin_meta["tier"]

        # Generate address text
        template, quality_tier, base_score, has_landmark_flag = rng.choice(CHAOTIC_ADDRESS_TEMPLATES)
        landmark = rng.choice(LANDMARKS) if has_landmark_flag else None
        locality = rng.choice(LOCALITIES)
        house_no = f"{rng.randint(1, 150)}" if "house" in template else None

        raw_addr = template.format(
            house=house_no or "12",
            society="Green Enclave",
            landmark=landmark or "Chowk",
            locality=locality,
            city=city,
            state=state,
            gali=rng.randint(1, 12)
        )

        # Micro-variation in score based on tier
        score = min(1.0, max(0.1, base_score + rng.uniform(-0.05, 0.05)))

        address = IndianAddress(
            raw_address=raw_addr,
            house_no=house_no,
            landmark=landmark,
            locality=locality,
            city=city,
            state=state,
            pincode=pincode,
            has_landmark=has_landmark_flag,
            address_completeness_score=round(score, 3),
            quality_tier=quality_tier,
            extracted_entities={
                "city": city,
                "state": state,
                "pincode": pincode,
                "landmark": landmark or "NONE",
                "locality": locality
            }
        )

        # Weighted Category
        cat_roll = rng.random()
        cumulative = 0.0
        selected_category = ProductCategory.APPAREL
        for cat, prob in categories:
            cumulative += prob
            if cat_roll <= cumulative:
                selected_category = cat
                break

        # Order Value in INR (₹)
        if selected_category == ProductCategory.ELECTRONICS:
            order_value = float(rng.randint(1500, 9500))
        elif selected_category == ProductCategory.APPAREL:
            order_value = float(rng.randint(499, 2999))
        else:
            order_value = float(rng.randint(349, 1999))

        # Customer History
        past_orders = rng.randint(0, 15)
        # COD customers in Tier 3/4 have higher baseline return rate
        if past_orders > 0:
            if is_cod and city_tier in [CityTier.TIER_3, CityTier.TIER_4]:
                past_rto = rng.randint(0, min(past_orders, 4))
            else:
                past_rto = 0 if rng.random() > 0.3 else 1
        else:
            past_rto = 0

        # SLA requirement (Tier 1 gets tighter 3-4 days SLA; Tier 4 gets 5-7 days)
        sla_days = 3 if city_tier == CityTier.TIER_1 else (5 if city_tier == CityTier.TIER_2 else 7)

        orders.append(OrderRecord(
            order_id=order_id,
            customer_id=customer_id,
            customer_name=customer_name,
            phone=phone,
            payment_mode=payment_mode,
            city_tier=city_tier,
            address=address,
            category=selected_category,
            order_value_inr=order_value,
            item_weight_grams=rng.choice([350, 500, 750, 1000]),
            past_orders_count=past_orders,
            past_rto_count=past_rto,
            max_delivery_days=sla_days,
            created_at="2026-09-30T10:00:00Z"
        ))

    return orders
