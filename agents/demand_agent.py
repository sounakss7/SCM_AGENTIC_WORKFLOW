"""Demand Agent: Exposes ML-based forecast and uncertainty distributions to cooperating agents."""

from typing import Dict, Tuple, Any
from core.demand_data import STORES, SKUS
from forecasting.forecaster import forecaster
from agents.state import MultiEchelonAgentState, DisruptionEvent


def demand_agent_node(state: MultiEchelonAgentState) -> Dict:
    """Generate forecast and uncertainty intervals, adjusting for demand disruptions."""
    net = state["network"]
    T = net.planning_periods

    # Base ML forecast
    raw_forecast = forecaster.predict_horizon(horizon_length=T)

    disruption: DisruptionEvent = state.get("active_disruption")
    adjusted_forecast: Dict[Tuple[str, str, int], Dict[str, float]] = {}

    for key, f_dict in raw_forecast.items():
        store, sku, t = key
        pt = f_dict["point_forecast"]
        lb = f_dict["lower_bound_80"]
        ub = f_dict["upper_bound_80"]
        std = f_dict["std_dev"]

        # Check if demand spike disruption hits this store
        if disruption and disruption.disruption_type == "DEMAND_SPIKE":
            if disruption.affected_entity in [store, "ALL_STORES", "METRO_STORES"]:
                mult = disruption.severity_factor
                pt = round(pt * mult, 1)
                lb = round(lb * mult, 1)
                ub = round(ub * (mult + 0.2), 1)  # Increased uncertainty
                std = round(std * mult * 1.5, 2)

        adjusted_forecast[key] = {
            "point_forecast": pt,
            "lower_bound_80": lb,
            "upper_bound_80": ub,
            "std_dev": std
        }

    return {"forecast_demand": adjusted_forecast}
