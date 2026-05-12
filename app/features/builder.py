import pandas as pd

from app.standardization.transforms import (
    rolling_zscore,
    momentum_z,
    inventory_surprise_z,
)


DIRECTION = {
    "eia_crude_inventory_surprise_z": "bearish_when_positive",
    "eia_gasoline_inventory_surprise_z": "bearish_when_positive",
    "eia_distillate_inventory_surprise_z": "bearish_when_positive",
    "eia_propane_inventory_surprise_z": "bearish_when_positive",
    "eia_total_stocks_ex_spr_surprise_z": "bearish_when_positive",

    "eia_refinery_utilization_z": "bullish_when_positive",

    "eia_crude_production_momentum_z": "bearish_when_positive",
    "eia_import_momentum_z": "bearish_when_positive",

    "eia_export_momentum_z": "bullish_when_positive",
    "eia_refinery_input_momentum_z": "bullish_when_positive",
    "eia_total_product_supplied_momentum_z": "bullish_when_positive",
    "eia_gasoline_demand_momentum_z": "bullish_when_positive",
    "eia_distillate_demand_momentum_z": "bullish_when_positive",

    "cot_managed_money_crowding_z": "bearish_when_positive",

    "news_geopolitical_supply_risk_z": "bullish_when_positive",
    "news_opec_policy_z": "bullish_when_positive",
    "news_macro_growth_z": "bullish_when_positive",

    "x_geopolitical_supply_risk_z": "bullish_when_positive",
    "x_opec_policy_z": "bullish_when_positive",
    "x_inventory_event_z": "mixed",
    "x_macro_demand_z": "bullish_when_positive",

    "quanthub_oil_event_z": "bullish_when_positive",
}


def default_confidence(source: str) -> float:
    return {
        "EIA": 0.95,
        "EIA_PDF": 0.95,
        "CFTC_COT": 0.90,
        "CFTC_COT_SCRAPE": 0.88,
        "NEWS": 0.65,
        "X": 0.55,
        "QUANTHUB": 0.75,
    }.get(source, 0.70)


def safe_scaled_change(series: pd.Series, scale: float = 1.0) -> pd.Series:
    """
    Used when we only have latest PDF WoW changes.
    Converts raw change into bounded standardized-ish value.
    """
    if scale == 0:
        scale = 1.0

    return (series / scale).clip(-3, 3).fillna(0.0)


def safe_zscore(series: pd.Series, window: int = 52) -> pd.Series:
    """
    Compute rolling z-score with safety checks.
    """
    mean = series.rolling(window, min_periods=10).mean()
    std = series.rolling(window, min_periods=10).std()

    z = (series - mean) / std

    return z.replace([float("inf"), float("-inf")], 0).fillna(0).clip(-3, 3)


def build_features_from_raw(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()

    df = raw.copy()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        utc=True,
    )

    pivot = df.pivot_table(
        index="timestamp",
        columns="series_name",
        values="raw_value",
        aggfunc="last",
    ).sort_index()

    features = pd.DataFrame(index=pivot.index)

    # =========================
    # EIA PDF WoW change features
    # =========================

    if "commercial_crude_stocks_wow_change" in pivot:
        features["eia_crude_inventory_surprise_z"] = safe_scaled_change(
            pivot["commercial_crude_stocks_wow_change"],
            scale=5.0,
        )

    if "gasoline_stocks_wow_change" in pivot:
        features["eia_gasoline_inventory_surprise_z"] = safe_scaled_change(
            pivot["gasoline_stocks_wow_change"],
            scale=4.0,
        )

    if "distillate_stocks_wow_change" in pivot:
        features["eia_distillate_inventory_surprise_z"] = safe_scaled_change(
            pivot["distillate_stocks_wow_change"],
            scale=4.0,
        )

    if "propane_stocks_wow_change" in pivot:
        features["eia_propane_inventory_surprise_z"] = safe_scaled_change(
            pivot["propane_stocks_wow_change"],
            scale=4.0,
        )

    if "total_stocks_ex_spr_wow_change" in pivot:
        features["eia_total_stocks_ex_spr_surprise_z"] = safe_scaled_change(
            pivot["total_stocks_ex_spr_wow_change"],
            scale=10.0,
        )

    if "crude_production_wow_change" in pivot:
        features["eia_crude_production_momentum_z"] = safe_scaled_change(
            pivot["crude_production_wow_change"],
            scale=300.0,
        )

    if "crude_imports_wow_change" in pivot:
        features["eia_import_momentum_z"] = safe_scaled_change(
            pivot["crude_imports_wow_change"],
            scale=500.0,
        )

    if "crude_exports_wow_change" in pivot:
        features["eia_export_momentum_z"] = safe_scaled_change(
            pivot["crude_exports_wow_change"],
            scale=500.0,
        )

    if "refinery_crude_inputs_wow_change" in pivot:
        features["eia_refinery_input_momentum_z"] = safe_scaled_change(
            pivot["refinery_crude_inputs_wow_change"],
            scale=300.0,
        )

    if "total_product_supplied_wow_change" in pivot:
        features["eia_total_product_supplied_momentum_z"] = safe_scaled_change(
            pivot["total_product_supplied_wow_change"],
            scale=750.0,
        )

    if "gasoline_product_supplied_wow_change" in pivot:
        features["eia_gasoline_demand_momentum_z"] = safe_scaled_change(
            pivot["gasoline_product_supplied_wow_change"],
            scale=300.0,
        )

    if "distillate_product_supplied_wow_change" in pivot:
        features["eia_distillate_demand_momentum_z"] = safe_scaled_change(
            pivot["distillate_product_supplied_wow_change"],
            scale=300.0,
        )

    if "refinery_utilization_wow_change" in pivot:
        features["eia_refinery_utilization_z"] = safe_scaled_change(
            pivot["refinery_utilization_wow_change"],
            scale=2.0,
        )

    if "refinery_utilization" in pivot:
        features["eia_refinery_utilization_level_z"] = safe_scaled_change(
            pivot["refinery_utilization"] - 85.0,
            scale=5.0,
        )

    # =========================
    # Historical raw-value fallback
    # =========================

    if (
        "commercial_crude_stocks" in pivot
        and "eia_crude_inventory_surprise_z" not in features.columns
    ):
        features["eia_crude_inventory_surprise_z"] = inventory_surprise_z(
            pivot["commercial_crude_stocks"],
            window=52,
        )

    if (
        "gasoline_stocks" in pivot
        and "eia_gasoline_inventory_surprise_z" not in features.columns
    ):
        features["eia_gasoline_inventory_surprise_z"] = inventory_surprise_z(
            pivot["gasoline_stocks"],
            window=52,
        )

    if (
        "distillate_stocks" in pivot
        and "eia_distillate_inventory_surprise_z" not in features.columns
    ):
        features["eia_distillate_inventory_surprise_z"] = inventory_surprise_z(
            pivot["distillate_stocks"],
            window=52,
        )

    if (
        "crude_production" in pivot
        and "eia_crude_production_momentum_z" not in features.columns
    ):
        features["eia_crude_production_momentum_z"] = momentum_z(
            pivot["crude_production"],
            short=4,
            long=13,
            z_window=52,
        )

    if (
        "crude_imports" in pivot
        and "eia_import_momentum_z" not in features.columns
    ):
        features["eia_import_momentum_z"] = momentum_z(
            pivot["crude_imports"],
            short=4,
            long=13,
            z_window=52,
        )

    if (
        "crude_exports" in pivot
        and "eia_export_momentum_z" not in features.columns
    ):
        features["eia_export_momentum_z"] = momentum_z(
            pivot["crude_exports"],
            short=4,
            long=13,
            z_window=52,
        )

    if (
        "refinery_crude_inputs" in pivot
        and "eia_refinery_input_momentum_z" not in features.columns
    ):
        features["eia_refinery_input_momentum_z"] = momentum_z(
            pivot["refinery_crude_inputs"],
            short=4,
            long=13,
            z_window=52,
        )

    if (
        "gasoline_product_supplied" in pivot
        and "eia_gasoline_demand_momentum_z" not in features.columns
    ):
        features["eia_gasoline_demand_momentum_z"] = momentum_z(
            pivot["gasoline_product_supplied"],
            short=4,
            long=13,
            z_window=52,
        )

    if (
        "distillate_product_supplied" in pivot
        and "eia_distillate_demand_momentum_z" not in features.columns
    ):
        features["eia_distillate_demand_momentum_z"] = momentum_z(
            pivot["distillate_product_supplied"],
            short=4,
            long=13,
            z_window=52,
        )

    # =========================
    # COT (Legacy)
    # =========================

    if "managed_money_net_crude" in pivot:
        features["cot_managed_money_crowding_z"] = rolling_zscore(
            pivot["managed_money_net_crude"],
            window=156,
        )

    # =========================
    # COT Petroleum Features
    # =========================

    cot_petroleum_cols = [c for c in pivot.columns if c.startswith("cot_petroleum_")]

    for col in cot_petroleum_cols:
        # Generate z-score features for key metrics
        if col.endswith("_mm_net_pct_oi"):
            feature_name = col + "_z"
            features[feature_name] = safe_zscore(pivot[col], window=52)
            DIRECTION[feature_name] = "bullish_when_positive"

        if col.endswith("_mm_net"):
            feature_name = col + "_z"
            features[feature_name] = safe_zscore(pivot[col], window=52)
            DIRECTION[feature_name] = "bullish_when_positive"

        if col.endswith("_dealer_vs_spec"):
            feature_name = col + "_z"
            features[feature_name] = safe_zscore(pivot[col], window=52)
            DIRECTION[feature_name] = "bearish_when_positive"

        if col.endswith("_mm_net_change"):
            feature_name = col + "_z"
            features[feature_name] = safe_scaled_change(pivot[col], scale=50000.0)
            DIRECTION[feature_name] = "bullish_when_positive"

        if col.endswith("_swap_net_pct_oi"):
            feature_name = col + "_z"
            features[feature_name] = safe_zscore(pivot[col], window=52)
            DIRECTION[feature_name] = "bearish_when_positive"

    # =========================
    # News / X / QuantHub
    # =========================

    event_cols = [
        col for col in pivot.columns
        if col.startswith("news_")
        or col.startswith("x_")
        or col.startswith("quanthub_")
    ]

    for col in event_cols:
        feature_name = f"{col}_z"

        features[feature_name] = rolling_zscore(
            pivot[col].fillna(0),
            window=30,
            min_periods=5,
        )

    out = []

    for ts, row in features.dropna(how="all").iterrows():
        for feature_name, value in row.dropna().items():
            if feature_name.startswith("eia_"):
                source = "EIA_PDF"
            elif feature_name.startswith("cot_"):
                source = "CFTC_COT"
            elif feature_name.startswith("news_"):
                source = "NEWS"
            elif feature_name.startswith("x_"):
                source = "X"
            elif feature_name.startswith("quanthub_"):
                source = "QUANTHUB"
            else:
                source = "UNKNOWN"

            out.append(
                {
                    "timestamp": ts.to_pydatetime(),
                    "feature_name": feature_name,
                    "source": source,
                    "raw_value": None,
                    "standardized_value": float(value),
                    "confidence": default_confidence(source),
                    "decay": 1.0,
                    "horizon": "5d",
                    "directional_impact": DIRECTION.get(feature_name),
                    "metadata": {},
                }
            )

    return pd.DataFrame(out)