"""Multi-Echelon Supply Chain Network Topology and Parameter Specification.

Defines the physical multi-tier structure:
- 3 Sourcing Suppliers (S1, S2, S3) with cost, lead time, capacity, and risk tiers
- 2 Regional Warehouses (W1, W2) with holding costs, storage capacities, and throughput limits
- 6 Retail Stores (R1 to R6) with local demand, holding costs, and stockout penalty rates
- 3 Representative Product SKUs
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SKU(BaseModel):
    sku_id: str
    name: str
    category: str
    base_price: float = Field(..., ge=0.0)
    holding_cost_multiplier: float = 1.0
    stockout_penalty_per_unit: float = Field(..., ge=0.0)


class Supplier(BaseModel):
    supplier_id: str
    name: str
    unit_procurement_costs: Dict[str, float]  # sku_id -> unit cost
    capacity_per_period: int = Field(..., ge=0)
    lead_time_periods: int = Field(..., ge=0)  # periods to reach warehouses
    reliability_score: float = Field(default=0.95, ge=0.0, le=1.0)
    transport_cost_to_warehouse: Dict[str, float] = Field(default_factory=dict)  # warehouse_id -> cost/unit


class Warehouse(BaseModel):
    warehouse_id: str
    name: str
    storage_capacity: int = Field(..., ge=0)
    holding_cost_per_unit_period: float = Field(..., ge=0.0)
    lead_time_to_stores: Dict[str, int] = Field(default_factory=dict)  # store_id -> periods
    shipping_cost_to_stores: Dict[str, float] = Field(default_factory=dict)  # store_id -> cost/unit
    initial_inventory: Dict[str, int] = Field(default_factory=dict)  # sku_id -> units


class Store(BaseModel):
    store_id: str
    name: str
    holding_cost_per_unit_period: float = Field(..., ge=0.0)
    stockout_penalty_per_unit: Dict[str, float] = Field(default_factory=dict)  # sku_id -> penalty
    initial_inventory: Dict[str, int] = Field(default_factory=dict)  # sku_id -> units


class MultiEchelonNetwork(BaseModel):
    suppliers: List[Supplier]
    warehouses: List[Warehouse]
    stores: List[Store]
    skus: List[SKU]
    planning_periods: int = 4  # e.g., 4 discrete weekly periods


def get_default_network() -> MultiEchelonNetwork:
    """Build the standard 3-Suppliers, 2-Warehouses, 6-Stores synthetic multi-echelon network."""
    skus = [
        SKU(
            sku_id="SKU_101",
            name="Fast-Moving Consumer Good (FMCG Core)",
            category="Consumer",
            base_price=30.0,
            holding_cost_multiplier=1.0,
            stockout_penalty_per_unit=40.0
        ),
        SKU(
            sku_id="SKU_202",
            name="Seasonal Apparel / Perishable Item",
            category="Apparel",
            base_price=55.0,
            holding_cost_multiplier=1.5,
            stockout_penalty_per_unit=70.0
        ),
        SKU(
            sku_id="SKU_303",
            name="High-Value Durable Electronics",
            category="Electronics",
            base_price=120.0,
            holding_cost_multiplier=2.0,
            stockout_penalty_per_unit=150.0
        )
    ]

    # Suppliers: S1 (Low Cost, Long Lead Time), S2 (Balanced), S3 (Expedited, High Cost)
    suppliers = [
        Supplier(
            supplier_id="S1",
            name="Global Bulk Manufacturer (S1)",
            unit_procurement_costs={"SKU_101": 14.0, "SKU_202": 24.0, "SKU_303": 50.0},
            capacity_per_period=350,
            lead_time_periods=2,  # 2 periods to arrive
            reliability_score=0.85,
            transport_cost_to_warehouse={"W1": 2.5, "W2": 3.0}
        ),
        Supplier(
            supplier_id="S2",
            name="Regional Nearshore Supplier (S2)",
            unit_procurement_costs={"SKU_101": 19.0, "SKU_202": 32.0, "SKU_303": 65.0},
            capacity_per_period=250,
            lead_time_periods=1,  # 1 period to arrive
            reliability_score=0.95,
            transport_cost_to_warehouse={"W1": 2.0, "W2": 2.0}
        ),
        Supplier(
            supplier_id="S3",
            name="Domestic Express Supplier (S3)",
            unit_procurement_costs={"SKU_101": 26.0, "SKU_202": 42.0, "SKU_303": 85.0},
            capacity_per_period=150,
            lead_time_periods=0,  # Same period arrival
            reliability_score=0.99,
            transport_cost_to_warehouse={"W1": 4.0, "W2": 4.0}
        )
    ]

    # Warehouses: W1 (North Hub), W2 (South Hub)
    warehouses = [
        Warehouse(
            warehouse_id="W1",
            name="Central Logistics Hub North (W1)",
            storage_capacity=500,
            holding_cost_per_unit_period=1.5,
            lead_time_to_stores={
                "R1": 1, "R2": 1, "R3": 1, "R4": 1, "R5": 2, "R6": 2
            },
            shipping_cost_to_stores={
                "R1": 3.0, "R2": 3.0, "R3": 4.0, "R4": 4.0, "R5": 7.0, "R6": 7.0
            },
            initial_inventory={"SKU_101": 50, "SKU_202": 30, "SKU_303": 15}
        ),
        Warehouse(
            warehouse_id="W2",
            name="Central Logistics Hub South (W2)",
            storage_capacity=500,
            holding_cost_per_unit_period=1.5,
            lead_time_to_stores={
                "R1": 2, "R2": 2, "R3": 1, "R4": 1, "R5": 1, "R6": 1
            },
            shipping_cost_to_stores={
                "R1": 7.0, "R2": 7.0, "R3": 4.0, "R4": 4.0, "R5": 3.0, "R6": 3.0
            },
            initial_inventory={"SKU_101": 50, "SKU_202": 30, "SKU_303": 15}
        )
    ]

    # Stores: R1-R6
    stores = [
        Store(
            store_id=f"R{i}",
            name=f"Retail Store R{i} ({'North' if i <= 2 else ('Central' if i <= 4 else 'South')})",
            holding_cost_per_unit_period=2.5,
            stockout_penalty_per_unit={"SKU_101": 40.0, "SKU_202": 70.0, "SKU_303": 150.0},
            initial_inventory={"SKU_101": 15, "SKU_202": 10, "SKU_303": 5}
        )
        for i in range(1, 7)
    ]

    return MultiEchelonNetwork(
        suppliers=suppliers,
        warehouses=warehouses,
        stores=stores,
        skus=skus,
        planning_periods=4
    )
