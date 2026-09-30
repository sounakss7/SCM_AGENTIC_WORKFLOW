"""Indian Logistics Network Topology and Product Catalog Specification.

Simulates a realistic Indian supply chain corridor:
- 3 Sourcing Hubs: Pune, Surat, Ahmedabad
- 3 Sea/Container Ports: Nhava Sheva (JNPT), Mundra Port, Chennai Port
- 3 Distribution Centers: Mumbai (Bhiwandi), Delhi-NCR (Bilaspur), Bengaluru (Nelamangala)
- 4 Consumer Retail Zones: Mumbai, Delhi, Bengaluru, Chennai
- 4 Named Indian Transporters: Safexpress, Delhivery, TCI Express, Blue Dart
- 25 FMCG / Retail SKUs with Indian Rupee (₹) pricing and delay penalties
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SKUItem(BaseModel):
    sku_id: str
    name: str
    category: str
    unit_cost_inr: float = Field(..., ge=0.0)
    selling_price_inr: float = Field(..., ge=0.0)
    weight_kg: float = Field(default=1.0, ge=0.1)
    daily_demand: int = Field(..., ge=1)
    delay_penalty_per_day_inr: float = Field(..., ge=0.0)


class CarrierProfile(BaseModel):
    carrier_id: str
    name: str
    base_cost_per_km_inr: float
    avg_speed_km_day: float
    reliability_rating: float = Field(..., ge=0.0, le=1.0)
    daily_capacity_units: int
    express_surcharge_inr: float = 0.0


class NetworkNode(BaseModel):
    node_id: str
    name: str
    node_type: str  # SUPPLIER, PORT, WAREHOUSE, RETAILER
    state: str
    city: str
    capacity_units: int
    handling_cost_per_unit_inr: float


class RouteLink(BaseModel):
    link_id: str
    origin_id: str
    destination_id: str
    distance_km: float
    base_transit_days: float
    primary_carrier_id: str
    available_carrier_ids: List[str]
    capacity_units: int


class IndianLogisticsNetwork(BaseModel):
    suppliers: List[NetworkNode]
    ports: List[NetworkNode]
    warehouses: List[NetworkNode]
    retailers: List[NetworkNode]
    carriers: Dict[str, CarrierProfile]
    links: List[RouteLink]
    skus: List[SKUItem]


def get_default_indian_network() -> IndianLogisticsNetwork:
    """Build the synthetic Indian logistics network with realistic INR costs and transit times."""
    # 1. Sourcing Suppliers
    suppliers = [
        NetworkNode(node_id="SUP_PUNE", name="Pune Industrial Cluster", node_type="SUPPLIER", state="Maharashtra", city="Pune", capacity_units=2000, handling_cost_per_unit_inr=15.0),
        NetworkNode(node_id="SUP_SURAT", name="Surat Manufacturing Zone", node_type="SUPPLIER", state="Gujarat", city="Surat", capacity_units=2500, handling_cost_per_unit_inr=12.0),
        NetworkNode(node_id="SUP_AHMEDABAD", name="Ahmedabad Sourcing Hub", node_type="SUPPLIER", state="Gujarat", city="Ahmedabad", capacity_units=1800, handling_cost_per_unit_inr=14.0),
    ]

    # 2. Key Ports
    ports = [
        NetworkNode(node_id="PORT_JNPT", name="Nhava Sheva (JNPT)", node_type="PORT", state="Maharashtra", city="Navi Mumbai", capacity_units=3000, handling_cost_per_unit_inr=35.0),
        NetworkNode(node_id="PORT_MUNDRA", name="Mundra Port", node_type="PORT", state="Gujarat", city="Kutch", capacity_units=3500, handling_cost_per_unit_inr=30.0),
        NetworkNode(node_id="PORT_CHENNAI", name="Chennai Port", node_type="PORT", state="Tamil Nadu", city="Chennai", capacity_units=2200, handling_cost_per_unit_inr=38.0),
    ]

    # 3. Inland Warehouses / Hubs
    warehouses = [
        NetworkNode(node_id="WH_MUMBAI", name="Bhiwandi Central Hub", node_type="WAREHOUSE", state="Maharashtra", city="Mumbai", capacity_units=1500, handling_cost_per_unit_inr=25.0),
        NetworkNode(node_id="WH_DELHI", name="Bilaspur Logistics Hub", node_type="WAREHOUSE", state="Haryana", city="Delhi-NCR", capacity_units=1800, handling_cost_per_unit_inr=28.0),
        NetworkNode(node_id="WH_BLR", name="Nelamangala Logistics Park", node_type="WAREHOUSE", state="Karnataka", city="Bengaluru", capacity_units=1400, handling_cost_per_unit_inr=26.0),
    ]

    # 4. Retail Consumption Zones
    retailers = [
        NetworkNode(node_id="RET_MUMBAI", name="Mumbai Metro Retail", node_type="RETAILER", state="Maharashtra", city="Mumbai", capacity_units=1000, handling_cost_per_unit_inr=10.0),
        NetworkNode(node_id="RET_DELHI", name="Delhi-NCR Supermarkets", node_type="RETAILER", state="Delhi", city="New Delhi", capacity_units=1200, handling_cost_per_unit_inr=12.0),
        NetworkNode(node_id="RET_BLR", name="Bengaluru Hypermarkets", node_type="RETAILER", state="Karnataka", city="Bengaluru", capacity_units=900, handling_cost_per_unit_inr=11.0),
        NetworkNode(node_id="RET_CHENNAI", name="Chennai Retail Network", node_type="RETAILER", state="Tamil Nadu", city="Chennai", capacity_units=850, handling_cost_per_unit_inr=10.0),
    ]

    # 5. Named Transporters
    carriers = {
        "SAFEXPRESS": CarrierProfile(
            carrier_id="SAFEXPRESS",
            name="Safexpress Logistics",
            base_cost_per_km_inr=0.08,
            avg_speed_km_day=380.0,
            reliability_rating=0.90,
            daily_capacity_units=800,
            express_surcharge_inr=0.0
        ),
        "DELHIVERY": CarrierProfile(
            carrier_id="DELHIVERY",
            name="Delhivery Express",
            base_cost_per_km_inr=0.10,
            avg_speed_km_day=480.0,
            reliability_rating=0.94,
            daily_capacity_units=600,
            express_surcharge_inr=25.0
        ),
        "TCI_EXPRESS": CarrierProfile(
            carrier_id="TCI_EXPRESS",
            name="TCI Express Multimodal",
            base_cost_per_km_inr=0.13,
            avg_speed_km_day=550.0,
            reliability_rating=0.97,
            daily_capacity_units=400,
            express_surcharge_inr=50.0
        ),
        "BLUE_DART": CarrierProfile(
            carrier_id="BLUE_DART",
            name="Blue Dart Surface & Air",
            base_cost_per_km_inr=0.18,
            avg_speed_km_day=700.0,
            reliability_rating=0.99,
            daily_capacity_units=250,
            express_surcharge_inr=100.0
        ),
    }

    # 6. Physical Highway / Port Transit Links
    links = [
        # Supplier -> Port links
        RouteLink(link_id="L_PUNE_JNPT", origin_id="SUP_PUNE", destination_id="PORT_JNPT", distance_km=145.0, base_transit_days=1.0, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "DELHIVERY", "TCI_EXPRESS"], capacity_units=900),
        RouteLink(link_id="L_PUNE_CHN", origin_id="SUP_PUNE", destination_id="PORT_CHENNAI", distance_km=1150.0, base_transit_days=3.0, primary_carrier_id="TCI_EXPRESS", available_carrier_ids=["TCI_EXPRESS", "SAFEXPRESS"], capacity_units=600),
        RouteLink(link_id="L_SURAT_MUNDRA", origin_id="SUP_SURAT", destination_id="PORT_MUNDRA", distance_km=620.0, base_transit_days=2.0, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "DELHIVERY", "TCI_EXPRESS"], capacity_units=1000),
        RouteLink(link_id="L_SURAT_JNPT", origin_id="SUP_SURAT", destination_id="PORT_JNPT", distance_km=280.0, base_transit_days=1.5, primary_carrier_id="DELHIVERY", available_carrier_ids=["DELHIVERY", "SAFEXPRESS", "TCI_EXPRESS"], capacity_units=850),
        RouteLink(link_id="L_AHM_MUNDRA", origin_id="SUP_AHMEDABAD", destination_id="PORT_MUNDRA", distance_km=350.0, base_transit_days=1.5, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "DELHIVERY"], capacity_units=750),
        RouteLink(link_id="L_AHM_JNPT", origin_id="SUP_AHMEDABAD", destination_id="PORT_JNPT", distance_km=520.0, base_transit_days=2.0, primary_carrier_id="DELHIVERY", available_carrier_ids=["DELHIVERY", "SAFEXPRESS", "TCI_EXPRESS"], capacity_units=750),

        # Port -> Warehouse links
        RouteLink(link_id="L_JNPT_MUM", origin_id="PORT_JNPT", destination_id="WH_MUMBAI", distance_km=60.0, base_transit_days=0.5, primary_carrier_id="DELHIVERY", available_carrier_ids=["DELHIVERY", "SAFEXPRESS", "BLUE_DART"], capacity_units=1200),
        RouteLink(link_id="L_JNPT_DEL", origin_id="PORT_JNPT", destination_id="WH_DELHI", distance_km=1420.0, base_transit_days=3.5, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "DELHIVERY", "TCI_EXPRESS", "BLUE_DART"], capacity_units=900),
        RouteLink(link_id="L_JNPT_BLR", origin_id="PORT_JNPT", destination_id="WH_BLR", distance_km=980.0, base_transit_days=2.5, primary_carrier_id="DELHIVERY", available_carrier_ids=["DELHIVERY", "SAFEXPRESS", "TCI_EXPRESS", "BLUE_DART"], capacity_units=700),
        RouteLink(link_id="L_MUNDRA_DEL", origin_id="PORT_MUNDRA", destination_id="WH_DELHI", distance_km=1100.0, base_transit_days=3.0, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "DELHIVERY", "TCI_EXPRESS"], capacity_units=1100),
        RouteLink(link_id="L_MUNDRA_MUM", origin_id="PORT_MUNDRA", destination_id="WH_MUMBAI", distance_km=850.0, base_transit_days=2.0, primary_carrier_id="DELHIVERY", available_carrier_ids=["DELHIVERY", "SAFEXPRESS", "TCI_EXPRESS"], capacity_units=800),
        RouteLink(link_id="L_MUNDRA_BLR", origin_id="PORT_MUNDRA", destination_id="WH_BLR", distance_km=1700.0, base_transit_days=4.0, primary_carrier_id="TCI_EXPRESS", available_carrier_ids=["TCI_EXPRESS", "SAFEXPRESS"], capacity_units=650),
        RouteLink(link_id="L_CHN_BLR", origin_id="PORT_CHENNAI", destination_id="WH_BLR", distance_km=350.0, base_transit_days=1.0, primary_carrier_id="DELHIVERY", available_carrier_ids=["DELHIVERY", "SAFEXPRESS", "TCI_EXPRESS"], capacity_units=700),
        RouteLink(link_id="L_CHN_DEL", origin_id="PORT_CHENNAI", destination_id="WH_DELHI", distance_km=2150.0, base_transit_days=4.5, primary_carrier_id="TCI_EXPRESS", available_carrier_ids=["TCI_EXPRESS", "SAFEXPRESS"], capacity_units=600),
        RouteLink(link_id="L_CHN_MUM", origin_id="PORT_CHENNAI", destination_id="WH_MUMBAI", distance_km=1330.0, base_transit_days=3.5, primary_carrier_id="TCI_EXPRESS", available_carrier_ids=["TCI_EXPRESS", "SAFEXPRESS"], capacity_units=650),

        # Warehouse -> Retailer links
        RouteLink(link_id="L_MUM_RETMUM", origin_id="WH_MUMBAI", destination_id="RET_MUMBAI", distance_km=40.0, base_transit_days=0.5, primary_carrier_id="DELHIVERY", available_carrier_ids=["DELHIVERY", "SAFEXPRESS", "BLUE_DART"], capacity_units=900),
        RouteLink(link_id="L_MUM_RETBLR", origin_id="WH_MUMBAI", destination_id="RET_BLR", distance_km=990.0, base_transit_days=2.5, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "DELHIVERY", "TCI_EXPRESS"], capacity_units=600),
        RouteLink(link_id="L_MUM_RETDEL", origin_id="WH_MUMBAI", destination_id="RET_DELHI", distance_km=1410.0, base_transit_days=3.5, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "DELHIVERY", "TCI_EXPRESS"], capacity_units=600),
        RouteLink(link_id="L_MUM_RETCHN", origin_id="WH_MUMBAI", destination_id="RET_CHENNAI", distance_km=1330.0, base_transit_days=3.0, primary_carrier_id="TCI_EXPRESS", available_carrier_ids=["TCI_EXPRESS", "DELHIVERY"], capacity_units=500),
        RouteLink(link_id="L_DEL_RETDEL", origin_id="WH_DELHI", destination_id="RET_DELHI", distance_km=55.0, base_transit_days=0.5, primary_carrier_id="DELHIVERY", available_carrier_ids=["DELHIVERY", "SAFEXPRESS", "BLUE_DART"], capacity_units=1100),
        RouteLink(link_id="L_DEL_RETMUM", origin_id="WH_DELHI", destination_id="RET_MUMBAI", distance_km=1410.0, base_transit_days=3.5, primary_carrier_id="TCI_EXPRESS", available_carrier_ids=["TCI_EXPRESS", "DELHIVERY", "BLUE_DART"], capacity_units=500),
        RouteLink(link_id="L_DEL_RETBLR", origin_id="WH_DELHI", destination_id="RET_BLR", distance_km=2150.0, base_transit_days=4.5, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "TCI_EXPRESS"], capacity_units=500),
        RouteLink(link_id="L_DEL_RETCHN", origin_id="WH_DELHI", destination_id="RET_CHENNAI", distance_km=2180.0, base_transit_days=4.5, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "TCI_EXPRESS"], capacity_units=500),
        RouteLink(link_id="L_BLR_RETBLR", origin_id="WH_BLR", destination_id="RET_BLR", distance_km=35.0, base_transit_days=0.5, primary_carrier_id="DELHIVERY", available_carrier_ids=["DELHIVERY", "SAFEXPRESS", "BLUE_DART"], capacity_units=850),
        RouteLink(link_id="L_BLR_RETCHN", origin_id="WH_BLR", destination_id="RET_CHENNAI", distance_km=345.0, base_transit_days=1.0, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "DELHIVERY", "TCI_EXPRESS"], capacity_units=700),
        RouteLink(link_id="L_BLR_RETMUM", origin_id="WH_BLR", destination_id="RET_MUMBAI", distance_km=990.0, base_transit_days=2.5, primary_carrier_id="SAFEXPRESS", available_carrier_ids=["SAFEXPRESS", "DELHIVERY"], capacity_units=600),
        RouteLink(link_id="L_BLR_RETDEL", origin_id="WH_BLR", destination_id="RET_DELHI", distance_km=2150.0, base_transit_days=4.5, primary_carrier_id="TCI_EXPRESS", available_carrier_ids=["TCI_EXPRESS", "SAFEXPRESS"], capacity_units=500),
    ]

    # 7. 25 Indian FMCG & Retail SKUs
    skus_data = [
        ("SKU_01", "Aashirvaad Shudh Chakki Atta 10kg", "Staples", 420.0, 490.0, 10.0, 85, 45.0),
        ("SKU_02", "Fortune Sunlite Refined Oil 5L", "Edible Oil", 650.0, 740.0, 4.6, 60, 60.0),
        ("SKU_03", "Tata Salt Vacuum Evaporated 1kg", "Staples", 22.0, 28.0, 1.0, 150, 15.0),
        ("SKU_04", "India Gate Basmati Rice Feast 5kg", "Staples", 380.0, 460.0, 5.0, 70, 40.0),
        ("SKU_05", "Amul Butter Pasteurised 500g", "Dairy", 240.0, 275.0, 0.5, 90, 80.0),
        ("SKU_06", "Surf Excel Easy Wash Detergent 5kg", "Home Care", 580.0, 690.0, 5.0, 50, 35.0),
        ("SKU_07", "Dettol Antiseptic Liquid 1L", "Personal Care", 310.0, 360.0, 1.0, 45, 50.0),
        ("SKU_08", "Parle-G Gold Biscuits 1kg Pack", "Packaged Snacks", 95.0, 120.0, 1.0, 120, 20.0),
        ("SKU_09", "Maggi 2-Minute Masala Noodles 24-Pack", "Packaged Snacks", 280.0, 336.0, 1.7, 110, 40.0),
        ("SKU_10", "Tata Tea Gold Leaf Tea 1kg", "Beverages", 460.0, 550.0, 1.0, 80, 50.0),
        ("SKU_11", "Colgate Strong Teeth Toothpaste 500g Combo", "Oral Care", 210.0, 260.0, 0.6, 95, 30.0),
        ("SKU_12", "Head & Shoulders Anti-Dandruff 650ml", "Personal Care", 480.0, 599.0, 0.7, 40, 55.0),
        ("SKU_13", "Haldiram Bhujia Sev 1kg", "Packaged Snacks", 220.0, 270.0, 1.0, 75, 25.0),
        ("SKU_14", "Dabur Honey 100% Pure 1kg", "Health Foods", 340.0, 430.0, 1.0, 35, 45.0),
        ("SKU_15", "Vim Dishwash Gel Lemon 2L", "Home Care", 330.0, 410.0, 2.1, 55, 30.0),
        ("SKU_16", "Cadbury Dairy Milk Silk Family Pack", "Confectionery", 150.0, 195.0, 0.25, 80, 70.0),
        ("SKU_17", "Whisper Ultra Clean Sanitary Pads 44s", "Personal Care", 380.0, 475.0, 0.4, 65, 50.0),
        ("SKU_18", "Bournvita Chocolate Nutrition Drink 1kg", "Beverages", 360.0, 440.0, 1.0, 50, 40.0),
        ("SKU_19", "Lizol Disinfectant Floor Cleaner 2L", "Home Care", 310.0, 399.0, 2.1, 60, 35.0),
        ("SKU_20", "Patanjali Cow Ghee 1L Tin", "Dairy", 590.0, 680.0, 1.0, 45, 65.0),
        ("SKU_21", "Bru Instant Coffee Jar 200g", "Beverages", 290.0, 375.0, 0.3, 50, 45.0),
        ("SKU_22", "Lipton Green Tea Honey Lemon 100 Bags", "Beverages", 450.0, 580.0, 0.3, 30, 60.0),
        ("SKU_23", "Godrej No.1 Bathing Soap Pack of 8", "Personal Care", 180.0, 230.0, 0.8, 85, 25.0),
        ("SKU_24", "Everest Garam Masala Powder 500g", "Spices", 290.0, 360.0, 0.5, 65, 35.0),
        ("SKU_25", "Kurkure Masala Munch 100g Box (20s)", "Packaged Snacks", 320.0, 400.0, 2.0, 90, 30.0),
    ]

    skus = [
        SKUItem(
            sku_id=item[0],
            name=item[1],
            category=item[2],
            unit_cost_inr=item[3],
            selling_price_inr=item[4],
            weight_kg=item[5],
            daily_demand=item[6],
            delay_penalty_per_day_inr=item[7]
        )
        for item in skus_data
    ]

    return IndianLogisticsNetwork(
        suppliers=suppliers,
        ports=ports,
        warehouses=warehouses,
        retailers=retailers,
        carriers=carriers,
        links=links,
        skus=skus
    )


# Singleton instance of Indian Logistics Network
NETWORK = get_default_indian_network()
build_indian_logistics_network = get_default_indian_network
SUPPLIERS_DB = {s.node_id: s for s in NETWORK.suppliers}
PORTS_DB = {p.node_id: p for p in NETWORK.ports}
WAREHOUSES_DB = {w.node_id: w for w in NETWORK.warehouses}
RETAILERS_DB = {r.node_id: r for r in NETWORK.retailers}
CARRIERS_DB = NETWORK.carriers
SKUS_DB = {s.sku_id: s for s in NETWORK.skus}
LINKS_DB = {l.link_id: l for l in NETWORK.links}
