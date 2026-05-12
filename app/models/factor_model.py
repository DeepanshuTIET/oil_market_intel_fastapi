import numpy as np
import pandas as pd

from app.standardization.transforms import bounded_probability


BASE_WEIGHTS = {
    # EIA inventory pressure
    "eia_crude_inventory_surprise_z": -0.25,
    "eia_gasoline_inventory_surprise_z": -0.12,
    "eia_distillate_inventory_surprise_z": -0.12,
    "eia_cushing_inventory_surprise_z": -0.15,

    # EIA supply pressure
    "eia_crude_production_momentum_z": -0.10,
    "eia_import_momentum_z": -0.08,

    # EIA demand / exports
    "eia_export_momentum_z": 0.15,
    "eia_refinery_input_momentum_z": 0.12,
    "eia_refinery_utilization_z": 0.10,
    "eia_refinery_utilization_level_z": 0.08,
    "eia_gasoline_demand_momentum_z": 0.10,
    "eia_distillate_demand_momentum_z": 0.10,

    # COT positioning (legacy)
    "cot_managed_money_crowding_z": -0.15,

    # Event/news features
    "news_geopolitical_supply_risk_z": 0.20,
    "news_opec_policy_z": 0.15,
    "news_macro_growth_z": 0.10,

    # X features
    "x_geopolitical_supply_risk_z": 0.10,
    "x_opec_policy_z": 0.08,
    "x_macro_demand_z": 0.07,
    "x_inventory_event_z": 0.05,

    # QuantHub features
    "quanthub_oil_event_z": 0.12,
}


# COT Petroleum feature patterns with weights
COT_PETROLEUM_WEIGHTS = {
    "_mm_net_pct_oi_z": 0.12,      # Managed money net as % of OI
    "_mm_net_z": 0.10,              # Managed money net position
    "_mm_net_change_z": 0.08,       # Managed money net change
    "_dealer_vs_spec_z": -0.08,     # Dealer vs spec (contrarian)
    "_swap_net_pct_oi_z": -0.06,    # Swap dealer net as % of OI (contrarian)
}


def get_weight_for_feature(feature_name: str) -> float:
    """
    Get weight for a feature, handling dynamic COT petroleum features.
    """
    # Check exact match first
    if feature_name in BASE_WEIGHTS:
        return BASE_WEIGHTS[feature_name]

    # Check COT petroleum patterns
    if feature_name.startswith("cot_petroleum_"):
        for pattern, weight in COT_PETROLEUM_WEIGHTS.items():
            if feature_name.endswith(pattern):
                return weight

    return 0.0


REGIME_MULTIPLIERS = {
    "supply_shock_bullish": {
        "news_geopolitical_supply_risk_z": 1.6,
        "x_geopolitical_supply_risk_z": 1.4,
        "quanthub_oil_event_z": 1.3,
        "eia_export_momentum_z": 1.2,
    },
    "inventory_mean_reversion": {
        "eia_crude_inventory_surprise_z": 1.6,
        "eia_gasoline_inventory_surprise_z": 1.3,
        "eia_distillate_inventory_surprise_z": 1.3,
        "eia_cushing_inventory_surprise_z": 1.4,
    },
    "positioning_crowded": {
        "cot_managed_money_crowding_z": 1.6,
        # COT petroleum features get boosted in crowded positioning regime
        "cot_petroleum_wti_physical_new_york_mercantile_exchange_mm_net_pct_oi_z": 1.5,
        "cot_petroleum_brent_last_day_ice_futures_europe_mm_net_pct_oi_z": 1.5,
    },
    "macro_demand": {
        "news_macro_growth_z": 1.4,
        "x_macro_demand_z": 1.3,
        "eia_refinery_input_momentum_z": 1.25,
        "eia_gasoline_demand_momentum_z": 1.2,
        "eia_distillate_demand_momentum_z": 1.2,
    },
    "neutral": {},
}


def adjusted_weights(regime: str) -> dict:
    multipliers = REGIME_MULTIPLIERS.get(regime, {})

    return {
        feature: weight * multipliers.get(feature, 1.0)
        for feature, weight in BASE_WEIGHTS.items()
    }


def compute_score(
    row: pd.Series,
    regime: str = "neutral",
) -> tuple[float, dict]:
    weights = adjusted_weights(regime)

    contributions = {}
    score = 0.0

    # Process known BASE_WEIGHTS features
    for feature, weight in weights.items():
        value = float(row.get(feature, 0.0) or 0.0)
        contribution = value * weight

        contributions[feature] = contribution
        score += contribution

    # Process dynamic COT petroleum features in row
    for feature in row.index:
        if feature not in weights and feature.startswith("cot_petroleum_"):
            weight = get_weight_for_feature(feature)
            if weight != 0.0:
                value = float(row.get(feature, 0.0) or 0.0)
                contribution = value * weight
                contributions[feature] = contribution
                score += contribution

    return float(score), contributions


def confidence_from_contributions(contributions: dict) -> float:
    values = np.array(
        [
            value for value in contributions.values()
            if abs(value) > 1e-9
        ]
    )

    if len(values) == 0:
        return 0.0

    agreement = abs(np.sign(values).sum()) / len(values)
    magnitude = min(np.mean(np.abs(values)) / 0.75, 1.0)

    confidence = 0.5 * agreement + 0.5 * magnitude

    return float(
        max(
            0.0,
            min(1.0, confidence),
        )
    )


def signal_from_score(score: float) -> tuple[float, float, str, float]:
    probability_up = bounded_probability(score)
    probability_down = 1 - probability_up

    expected_return = (probability_up - 0.5) * 0.06

    if probability_up >= 0.55:
        signal = "bullish"
    elif probability_up <= 0.45:
        signal = "bearish"
    else:
        signal = "neutral"

    return (
        probability_up,
        probability_down,
        signal,
        expected_return,
    )