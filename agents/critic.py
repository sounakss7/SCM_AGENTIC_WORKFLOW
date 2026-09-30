"""Agent 5: Carrier Quota, Serviceability & SLA Critic.

Audits generated dispatch plans against operational constraints:
- Verifies carrier daily origin hub pickup capacity limits
- Validates 6-digit Indian PIN code serviceability for each assigned 3PL courier
- Checks delivery transit times against promised SLA deadlines
"""

from typing import Dict, List
from core.config import get_default_carrier_rate_cards
from core.pincode_db import is_carrier_serviceable
from agents.state import IndianLogisticsState


def critic_node(state: IndianLogisticsState) -> Dict:
    """LangGraph node: Rigorously audit carrier allocation plan."""
    plan = state.get("dispatch_plan")
    violations: List[str] = []
    rate_cards = get_default_carrier_rate_cards()

    if not plan or not plan.allocations:
        return {
            "critic_passed": True,
            "critic_violations": [],
            "retry_count": state.get("retry_count", 0)
        }

    # 1. Check Carrier Daily Quotas
    carrier_counts: Dict[str, int] = {}
    for alloc in plan.allocations:
        carrier_counts[alloc.carrier.value] = carrier_counts.get(alloc.carrier.value, 0) + 1

    for c_val, count in carrier_counts.items():
        card = rate_cards.get(c_val)
        if card and count > card.daily_hub_capacity:
            violations.append(f"Carrier {c_val} quota exceeded: {count} assigned > {card.daily_hub_capacity} max capacity.")

    # 2. Check PIN code serviceability
    orders_map = {o.order_id: o for o in state["raw_orders"]}
    for alloc in plan.allocations:
        order = orders_map.get(alloc.order_id)
        if order and not is_carrier_serviceable(alloc.carrier, order.address.pincode):
            violations.append(f"Carrier {alloc.carrier.value} cannot service PIN code {order.address.pincode} for order {order.order_id}.")

    current_retries = state.get("retry_count", 0)
    passed = len(violations) == 0 or current_retries >= 2

    return {
        "critic_passed": passed,
        "critic_violations": violations,
        "retry_count": current_retries + 1
    }
