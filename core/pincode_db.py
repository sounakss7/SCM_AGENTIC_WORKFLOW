"""Indian Postal PIN Code Database and 3PL Courier Serviceability Directory.

Provides 6-digit PIN code metadata covering:
- Postal Circle & Zone
- City, District, and State
- City Tier Classification (Tier 1, Tier 2, Tier 3, Tier 4)
- 3PL Carrier Serviceability (Delhivery, Blue Dart, Shadowfax, Xpressbees, Ecom Express)
"""

from typing import Dict, Optional, Any
from core.schema import CityTier, CarrierName

# Curated reference directory of representative Indian PIN codes across all zones & tiers
PINCODE_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Zone 1: North (Delhi, Haryana, Punjab, HP, J&K)
    "110001": {"city": "New Delhi", "district": "Central Delhi", "state": "Delhi", "tier": CityTier.TIER_1, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "110092": {"city": "Delhi", "district": "East Delhi", "state": "Delhi", "tier": CityTier.TIER_1, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "122001": {"city": "Gurgaon", "district": "Gurugram", "state": "Haryana", "tier": CityTier.TIER_1, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "121001": {"city": "Faridabad", "district": "Faridabad", "state": "Haryana", "tier": CityTier.TIER_2, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "141001": {"city": "Ludhiana", "district": "Ludhiana", "state": "Punjab", "tier": CityTier.TIER_2, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "143001": {"city": "Amritsar", "district": "Amritsar", "state": "Punjab", "tier": CityTier.TIER_2, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "160017": {"city": "Chandigarh", "district": "Chandigarh", "state": "Chandigarh", "tier": CityTier.TIER_2, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},

    # Zone 2: UP & Uttarakhand
    "201301": {"city": "Noida", "district": "Gautam Buddha Nagar", "state": "Uttar Pradesh", "tier": CityTier.TIER_1, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "226001": {"city": "Lucknow", "district": "Lucknow", "state": "Uttar Pradesh", "tier": CityTier.TIER_2, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "208001": {"city": "Kanpur", "district": "Kanpur Nagar", "state": "Uttar Pradesh", "tier": CityTier.TIER_2, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "221001": {"city": "Varanasi", "district": "Varanasi", "state": "Uttar Pradesh", "tier": CityTier.TIER_2, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "273001": {"city": "Gorakhpur", "district": "Gorakhpur", "state": "Uttar Pradesh", "tier": CityTier.TIER_3, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS, CarrierName.SHADOWFAX]},
    "248001": {"city": "Dehradun", "district": "Dehradun", "state": "Uttarakhand", "tier": CityTier.TIER_2, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "243001": {"city": "Bareilly", "district": "Bareilly", "state": "Uttar Pradesh", "tier": CityTier.TIER_3, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "284001": {"city": "Jhansi", "district": "Jhansi", "state": "Uttar Pradesh", "tier": CityTier.TIER_3, "zone": "North",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.ECOM_EXPRESS, CarrierName.XPRESSBEES]},

    # Zone 3: West (Rajasthan, Gujarat)
    "302001": {"city": "Jaipur", "district": "Jaipur", "state": "Rajasthan", "tier": CityTier.TIER_2, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "342001": {"city": "Jodhpur", "district": "Jodhpur", "state": "Rajasthan", "tier": CityTier.TIER_2, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "301001": {"city": "Alwar", "district": "Alwar", "state": "Rajasthan", "tier": CityTier.TIER_3, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "380001": {"city": "Ahmedabad", "district": "Ahmedabad", "state": "Gujarat", "tier": CityTier.TIER_1, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "395001": {"city": "Surat", "district": "Surat", "state": "Gujarat", "tier": CityTier.TIER_2, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "390001": {"city": "Vadodara", "district": "Vadodara", "state": "Gujarat", "tier": CityTier.TIER_2, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "360001": {"city": "Rajkot", "district": "Rajkot", "state": "Gujarat", "tier": CityTier.TIER_2, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},

    # Zone 4: Central & West (Maharashtra, MP, Goa, Chhattisgarh)
    "400001": {"city": "Mumbai", "district": "Mumbai", "state": "Maharashtra", "tier": CityTier.TIER_1, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "400053": {"city": "Mumbai (Andheri)", "district": "Mumbai Suburban", "state": "Maharashtra", "tier": CityTier.TIER_1, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "411001": {"city": "Pune", "district": "Pune", "state": "Maharashtra", "tier": CityTier.TIER_1, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "440001": {"city": "Nagpur", "district": "Nagpur", "state": "Maharashtra", "tier": CityTier.TIER_2, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "422001": {"city": "Nashik", "district": "Nashik", "state": "Maharashtra", "tier": CityTier.TIER_2, "zone": "West",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "452001": {"city": "Indore", "district": "Indore", "state": "Madhya Pradesh", "tier": CityTier.TIER_2, "zone": "Central",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "462001": {"city": "Bhopal", "district": "Bhopal", "state": "Madhya Pradesh", "tier": CityTier.TIER_2, "zone": "Central",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "492001": {"city": "Raipur", "district": "Raipur", "state": "Chhattisgarh", "tier": CityTier.TIER_2, "zone": "Central",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},

    # Zone 5: South (AP, Telangana, Karnataka)
    "560001": {"city": "Bengaluru", "district": "Bengaluru Urban", "state": "Karnataka", "tier": CityTier.TIER_1, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "560034": {"city": "Bengaluru (Koramangala)", "district": "Bengaluru Urban", "state": "Karnataka", "tier": CityTier.TIER_1, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "500001": {"city": "Hyderabad", "district": "Hyderabad", "state": "Telangana", "tier": CityTier.TIER_1, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "530001": {"city": "Visakhapatnam", "district": "Visakhapatnam", "state": "Andhra Pradesh", "tier": CityTier.TIER_2, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "520001": {"city": "Vijayawada", "district": "NTR", "state": "Andhra Pradesh", "tier": CityTier.TIER_2, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "570001": {"city": "Mysuru", "district": "Mysuru", "state": "Karnataka", "tier": CityTier.TIER_2, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "580020": {"city": "Hubli", "district": "Dharwad", "state": "Karnataka", "tier": CityTier.TIER_3, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},

    # Zone 6: South (Tamil Nadu, Kerala)
    "600001": {"city": "Chennai", "district": "Chennai", "state": "Tamil Nadu", "tier": CityTier.TIER_1, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "641001": {"city": "Coimbatore", "district": "Coimbatore", "state": "Tamil Nadu", "tier": CityTier.TIER_2, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "625001": {"city": "Madurai", "district": "Madurai", "state": "Tamil Nadu", "tier": CityTier.TIER_2, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "636001": {"city": "Salem", "district": "Salem", "state": "Tamil Nadu", "tier": CityTier.TIER_3, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "682001": {"city": "Kochi", "district": "Ernakulam", "state": "Kerala", "tier": CityTier.TIER_2, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "695001": {"city": "Thiruvananthapuram", "district": "Thiruvananthapuram", "state": "Kerala", "tier": CityTier.TIER_2, "zone": "South",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},

    # Zone 7: East & North East (West Bengal, Odisha, Assam)
    "700001": {"city": "Kolkata", "district": "Kolkata", "state": "West Bengal", "tier": CityTier.TIER_1, "zone": "East",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "711101": {"city": "Howrah", "district": "Howrah", "state": "West Bengal", "tier": CityTier.TIER_2, "zone": "East",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.SHADOWFAX, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "751001": {"city": "Bhubaneswar", "district": "Khurda", "state": "Odisha", "tier": CityTier.TIER_2, "zone": "East",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "781001": {"city": "Guwahati", "district": "Kamrup Metropolitan", "state": "Assam", "tier": CityTier.TIER_2, "zone": "North East",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "734001": {"city": "Siliguri", "district": "Darjeeling", "state": "West Bengal", "tier": CityTier.TIER_3, "zone": "East",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},

    # Zone 8: Bihar & Jharkhand
    "800001": {"city": "Patna", "district": "Patna", "state": "Bihar", "tier": CityTier.TIER_2, "zone": "East",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS, CarrierName.SHADOWFAX]},
    "834001": {"city": "Ranchi", "district": "Ranchi", "state": "Jharkhand", "tier": CityTier.TIER_2, "zone": "East",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "831001": {"city": "Jamshedpur", "district": "East Singhbhum", "state": "Jharkhand", "tier": CityTier.TIER_2, "zone": "East",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.BLUEDART, CarrierName.XPRESSBEES, CarrierName.ECOM_EXPRESS]},
    "842001": {"city": "Muzaffarpur", "district": "Muzaffarpur", "state": "Bihar", "tier": CityTier.TIER_3, "zone": "East",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.ECOM_EXPRESS, CarrierName.XPRESSBEES]},
    "823001": {"city": "Gaya", "district": "Gaya", "state": "Bihar", "tier": CityTier.TIER_3, "zone": "East",
               "serviceable": [CarrierName.DELHIVERY, CarrierName.ECOM_EXPRESS, CarrierName.XPRESSBEES]},
    "841301": {"city": "Chapra", "district": "Saran", "state": "Bihar", "tier": CityTier.TIER_4, "zone": "East",
               "serviceable": [CarrierName.ECOM_EXPRESS, CarrierName.DELHIVERY]},
}


def get_pincode_info(pincode: str) -> Dict[str, Any]:
    """Retrieve metadata for a 6-digit Indian PIN code with regional fallback."""
    clean_pin = str(pincode).strip()
    if clean_pin in PINCODE_REGISTRY:
        return PINCODE_REGISTRY[clean_pin]

    # Deterministic fallback based on Postal Circle first-digit logic
    zone_digit = clean_pin[0] if clean_pin else "1"
    zone_map = {
        "1": ("Delhi/Punjab/Haryana", "North", CityTier.TIER_3),
        "2": ("Uttar Pradesh", "North", CityTier.TIER_3),
        "3": ("Rajasthan/Gujarat", "West", CityTier.TIER_3),
        "4": ("Maharashtra/MP", "West", CityTier.TIER_3),
        "5": ("Karnataka/AP/Telangana", "South", CityTier.TIER_3),
        "6": ("Tamil Nadu/Kerala", "South", CityTier.TIER_3),
        "7": ("WB/Odisha/NE", "East", CityTier.TIER_3),
        "8": ("Bihar/Jharkhand", "East", CityTier.TIER_4),
    }
    state_desc, zone_name, default_tier = zone_map.get(zone_digit, ("Rest of India", "Central", CityTier.TIER_4))

    return {
        "city": f"Town {clean_pin[:3]}",
        "district": f"District {clean_pin[:3]}",
        "state": state_desc,
        "tier": default_tier,
        "zone": zone_name,
        "serviceable": [CarrierName.DELHIVERY, CarrierName.ECOM_EXPRESS, CarrierName.XPRESSBEES]
    }


def is_carrier_serviceable(carrier: CarrierName, pincode: str) -> bool:
    """Check whether a 3PL courier services the designated Indian PIN code."""
    info = get_pincode_info(pincode)
    return carrier in info.get("serviceable", [])
