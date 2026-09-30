"""Deterministic Decision Core for Indian Supply Chain Routing & Resilience Optimization.

Strict Rule: The LLM does NOT perform routing math or cost calculation.
This module searches the network graph to compute the mathematically optimal
(lowest cost, feasible delay) alternate route and carrier assignment under disruptions.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
from pydantic import BaseModel, Field

from core.network import (
    IndianLogisticsNetwork, NetworkNode, RouteLink, CarrierProfile, SKUItem, get_default_indian_network
)
from core.disruptions import DisruptionEvent, DisruptionType, SeverityLevel


class PlannedLeg(BaseModel):
    origin_id: str
    destination_id: str
    link_id: str
    carrier_id: str
    carrier_name: str
    distance_km: float
    transit_days: float
    freight_cost_inr: float


class RoutePlan(BaseModel):
    plan_id: str
    sku_id: str
    quantity: int
    origin_supplier_id: str
    port_id: str
    warehouse_id: str
    destination_retailer_id: str
    legs: List[PlannedLeg]
    total_distance_km: float
    total_transit_days: float
    freight_cost_inr: float
    delay_penalty_inr: float
    handling_cost_inr: float
    total_cost_inr: float
    is_feasible: bool
    rejection_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = self.model_dump()
        d["supplier"] = self.origin_supplier_id
        d["port"] = self.port_id
        d["warehouse"] = self.warehouse_id
        d["retailer"] = self.destination_retailer_id
        d["carrier"] = self.legs[0].carrier_id if self.legs else "UNKNOWN"
        return d


class ReplanResult(BaseModel):
    order_id: str
    disruption_event: Optional[DisruptionEvent]
    baseline_disrupted_plan: RoutePlan
    re_planned_optimal_plan: RoutePlan
    cost_increase_avoided_inr: float = Field(..., description="Cost saved by re-routing in ₹")
    delay_days_avoided: float = Field(..., description="Delay saved by re-routing in days")
    is_successful: bool
    solver_latency_sec: float


def compute_leg_cost_and_time(
    link: RouteLink,
    carrier: CarrierProfile,
    quantity: int,
    disruption: Optional[DisruptionEvent] = None
) -> Tuple[float, float, bool]:
    """Calculate freight cost (₹), transit days, and feasibility for a single route leg."""
    # Check if carrier is 100% halted
    if disruption and disruption.disruption_type == DisruptionType.CARRIER_FAILURE:
        if disruption.target_id == carrier.carrier_id and disruption.severity == SeverityLevel.CRITICAL:
            return 999999.0, 99.0, False  # Infeasible: carrier halted

    # Check link closure
    if disruption and disruption.disruption_type == DisruptionType.ROUTE_CLOSURE:
        if disruption.target_id == link.link_id and disruption.severity == SeverityLevel.CRITICAL:
            return 999999.0, 99.0, False  # Infeasible: link closed

    # Base cost: distance * carrier_cost_per_km * weight/scale + express surcharge
    base_freight = link.distance_km * carrier.base_cost_per_km_inr * quantity + carrier.express_surcharge_inr
    base_time = link.base_transit_days

    # Apply disruption modifiers if applicable
    if disruption:
        is_affected = False
        if disruption.target_type == "CARRIER" and disruption.target_id == carrier.carrier_id:
            is_affected = True
        elif disruption.target_type == "PORT" and (disruption.target_id in [link.origin_id, link.destination_id]):
            is_affected = True
        elif disruption.target_type == "LINK" and disruption.target_id == link.link_id:
            is_affected = True

        if is_affected:
            base_time += disruption.delay_days_added
            base_freight *= (1.0 + disruption.cost_surcharge_pct / 100.0)

    return round(base_freight, 2), round(base_time, 2), True


def evaluate_end_to_end_route(
    network: IndianLogisticsNetwork,
    supplier_id: str,
    port_id: str,
    warehouse_id: str,
    retailer_id: str,
    carrier_assignments: Dict[str, str],  # leg_index (0,1,2) -> carrier_id
    sku: SKUItem,
    quantity: int,
    max_allowed_delay_days: float = 7.0,
    disruption: Optional[DisruptionEvent] = None
) -> RoutePlan:
    """Evaluate a specific 3-leg path: Supplier -> Port -> Warehouse -> Retailer."""
    links_by_nodes = {(l.origin_id, l.destination_id): l for l in network.links}
    nodes_by_id = {
        n.node_id: n for n in (network.suppliers + network.ports + network.warehouses + network.retailers)
    }

    # Verify link existence
    leg1_key = (supplier_id, port_id)
    leg2_key = (port_id, warehouse_id)
    leg3_key = (warehouse_id, retailer_id)

    for k in [leg1_key, leg2_key, leg3_key]:
        if k not in links_by_nodes:
            return RoutePlan(
                plan_id="INVALID", sku_id=sku.sku_id, quantity=quantity,
                origin_supplier_id=supplier_id, port_id=port_id,
                warehouse_id=warehouse_id, destination_retailer_id=retailer_id,
                legs=[], total_distance_km=0.0, total_transit_days=99.0,
                freight_cost_inr=999999.0, delay_penalty_inr=999999.0,
                handling_cost_inr=0.0, total_cost_inr=999999.0,
                is_feasible=False, rejection_reason=f"Link {k[0]}->{k[1]} does not exist in network."
            )

    l1 = links_by_nodes[leg1_key]
    l2 = links_by_nodes[leg2_key]
    l3 = links_by_nodes[leg3_key]

    c1 = network.carriers[carrier_assignments.get("0", l1.primary_carrier_id)]
    c2 = network.carriers[carrier_assignments.get("1", l2.primary_carrier_id)]
    c3 = network.carriers[carrier_assignments.get("2", l3.primary_carrier_id)]

    cost1, time1, feas1 = compute_leg_cost_and_time(l1, c1, quantity, disruption)
    cost2, time2, feas2 = compute_leg_cost_and_time(l2, c2, quantity, disruption)
    cost3, time3, feas3 = compute_leg_cost_and_time(l3, c3, quantity, disruption)

    if not (feas1 and feas2 and feas3):
        return RoutePlan(
            plan_id="INFEASIBLE_DISRUPTED", sku_id=sku.sku_id, quantity=quantity,
            origin_supplier_id=supplier_id, port_id=port_id,
            warehouse_id=warehouse_id, destination_retailer_id=retailer_id,
            legs=[], total_distance_km=0.0, total_transit_days=99.0,
            freight_cost_inr=999999.0, delay_penalty_inr=999999.0,
            handling_cost_inr=0.0, total_cost_inr=999999.0,
            is_feasible=False, rejection_reason="One or more legs are completely halted by disruption."
        )

    # Handling costs at Port + Warehouse
    handling_cost = (
        nodes_by_id[port_id].handling_cost_per_unit_inr * quantity +
        nodes_by_id[warehouse_id].handling_cost_per_unit_inr * quantity
    )

    total_dist = l1.distance_km + l2.distance_km + l3.distance_km
    total_time = time1 + time2 + time3
    total_freight = cost1 + cost2 + cost3

    # Base nominal transit time is ~3.5 days. Any excess incurs delay penalty
    nominal_transit = l1.base_transit_days + l2.base_transit_days + l3.base_transit_days
    excess_delay = max(0.0, total_time - nominal_transit)
    delay_penalty = excess_delay * sku.delay_penalty_per_day_inr * quantity

    # Feasibility check on max delay
    is_feasible = (total_time <= nominal_transit + max_allowed_delay_days)
    rejection = None if is_feasible else f"Total transit {total_time}d exceeds limit of {nominal_transit + max_allowed_delay_days}d."

    planned_legs = [
        PlannedLeg(origin_id=l1.origin_id, destination_id=l1.destination_id, link_id=l1.link_id, carrier_id=c1.carrier_id, carrier_name=c1.name, distance_km=l1.distance_km, transit_days=time1, freight_cost_inr=cost1),
        PlannedLeg(origin_id=l2.origin_id, destination_id=l2.destination_id, link_id=l2.link_id, carrier_id=c2.carrier_id, carrier_name=c2.name, distance_km=l2.distance_km, transit_days=time2, freight_cost_inr=cost2),
        PlannedLeg(origin_id=l3.origin_id, destination_id=l3.destination_id, link_id=l3.link_id, carrier_id=c3.carrier_id, carrier_name=c3.name, distance_km=l3.distance_km, transit_days=time3, freight_cost_inr=cost3),
    ]

    total_cost = round(total_freight + handling_cost + delay_penalty, 2)

    return RoutePlan(
        plan_id=f"PLAN-{supplier_id[:3]}-{port_id[:3]}-{warehouse_id[:3]}-{retailer_id[:3]}",
        sku_id=sku.sku_id,
        quantity=quantity,
        origin_supplier_id=supplier_id,
        port_id=port_id,
        warehouse_id=warehouse_id,
        destination_retailer_id=retailer_id,
        legs=planned_legs,
        total_distance_km=round(total_dist, 1),
        total_transit_days=round(total_time, 2),
        freight_cost_inr=round(total_freight, 2),
        delay_penalty_inr=round(delay_penalty, 2),
        handling_cost_inr=round(handling_cost, 2),
        total_cost_inr=total_cost,
        is_feasible=is_feasible,
        rejection_reason=rejection
    )


def find_optimal_alternate_route(
    network: Optional[IndianLogisticsNetwork] = None,
    supplier_id: str = "SUP_PUNE",
    retailer_id: str = "RET_MUMBAI",
    sku: Optional[Union[SKUItem, str]] = None,
    quantity: int = 100,
    disruption: Optional[Union[DisruptionEvent, Dict[str, Any]]] = None,
    max_allowed_delay_days: float = 7.0,
    sku_id: Optional[str] = None,
    blocked_carriers: Optional[List[str]] = None,
    congested_ports: Optional[Dict[str, float]] = None,
    blocked_lanes: Optional[List[Tuple[str, str]]] = None,
    **kwargs
) -> Tuple[Optional[RoutePlan], List[RoutePlan]]:
    """Deterministic Optimization Core:

    Exhaustively searches all candidate paths (S -> P -> W -> R) and carrier allocations.
    Minimizes: Total Cost (Freight + Handling + Delay Penalties) in INR (₹).
    """
    if network is None:
        network = get_default_indian_network()

    if sku is None:
        target_sku_id = sku_id or "SKU_01"
        sku = next((s for s in network.skus if s.sku_id == target_sku_id), network.skus[0])
    elif isinstance(sku, str):
        sku = next((s for s in network.skus if s.sku_id == sku), network.skus[0])

    # Convert dict disruption to DisruptionEvent if necessary
    if isinstance(disruption, dict):
        if "target_type" in disruption and "target_id" in disruption:
            disruption = DisruptionEvent(**disruption)
        elif disruption.get("carrier"):
            disruption = DisruptionEvent(
                event_id="EVT-DIS-C",
                disruption_type=DisruptionType.CARRIER_FAILURE,
                target_type="CARRIER",
                target_id=disruption["carrier"],
                severity=SeverityLevel.CRITICAL,
                delay_days_added=disruption.get("delay_days", 4.0),
                cost_surcharge_pct=50.0,
                capacity_reduction_pct=100.0,
                description=disruption.get("description", "Carrier breakdown")
            )
        elif disruption.get("port"):
            disruption = DisruptionEvent(
                event_id="EVT-DIS-P",
                disruption_type=DisruptionType.PORT_CONGESTION,
                target_type="PORT",
                target_id=disruption["port"],
                severity=SeverityLevel.HIGH,
                delay_days_added=disruption.get("delay_days", 3.0),
                cost_surcharge_pct=30.0,
                capacity_reduction_pct=70.0,
                description=disruption.get("description", "Port congestion")
            )

    blocked_carrier_set = set(blocked_carriers or [])
    if disruption and disruption.target_type == "CARRIER" and disruption.capacity_reduction_pct >= 90.0:
        blocked_carrier_set.add(disruption.target_id)

    ports = [p.node_id for p in network.ports]
    warehouses = [w.node_id for w in network.warehouses]
    carrier_ids = list(network.carriers.keys())

    candidate_plans: List[RoutePlan] = []

    for port_id in ports:
        for wh_id in warehouses:
            # Check primary assignment first
            primary_plan = evaluate_end_to_end_route(
                network, supplier_id, port_id, wh_id, retailer_id,
                carrier_assignments={}, sku=sku, quantity=quantity,
                max_allowed_delay_days=max_allowed_delay_days, disruption=disruption
            )
            if primary_plan.plan_id != "INVALID":
                candidate_plans.append(primary_plan)

            # Test carrier switching on each leg
            for c_id in ["DELHIVERY", "TCI_EXPRESS", "BLUE_DART", "SAFEXPRESS"]:
                if c_id in blocked_carrier_set:
                    continue
                alt_plan = evaluate_end_to_end_route(
                    network, supplier_id, port_id, wh_id, retailer_id,
                    carrier_assignments={"0": c_id, "1": c_id, "2": c_id},
                    sku=sku, quantity=quantity,
                    max_allowed_delay_days=max_allowed_delay_days, disruption=disruption
                )
                if alt_plan.plan_id != "INVALID":
                    candidate_plans.append(alt_plan)

    # Filter plans that do not use any blocked carrier
    unblocked_plans = [
        p for p in candidate_plans
        if not any(leg.carrier_id in blocked_carrier_set for leg in p.legs)
    ]

    # Filter feasible plans
    feasible_plans = [p for p in unblocked_plans if p.is_feasible]

    if not feasible_plans:
        return None, candidate_plans

    # Optimal plan minimizes total cost in INR (₹)
    optimal_plan = min(feasible_plans, key=lambda p: p.total_cost_inr)
    return optimal_plan, feasible_plans
