import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

REGIME_NAMES = {
    0: 'neutral',
    1: 'inventory_mean_reversion',
    2: 'supply_shock_bullish',
    3: 'positioning_crowded',
}

REGIME_FEATURES = [
    'eia_crude_inventory_surprise_z',
    'eia_refinery_utilization_z',
    'cot_managed_money_crowding_z',
    'news_geopolitical_supply_risk_z',
]


def detect_latest_regime(features: pd.DataFrame) -> str:
    if features.empty or len(features) < 10:
        return 'neutral'
    X = features.copy()
    for c in REGIME_FEATURES:
        if c not in X:
            X[c] = 0.0
    X = X[REGIME_FEATURES].fillna(0.0)
    n_clusters = min(4, max(2, len(X) // 10))
    scaled = StandardScaler().fit_transform(X)
    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(scaled)
    latest_label = int(labels[-1])
    # Overlay deterministic labels for interpretability.
    latest = X.iloc[-1]
    if latest.get('news_geopolitical_supply_risk_z', 0) > 1.0:
        return 'supply_shock_bullish'
    if abs(latest.get('eia_crude_inventory_surprise_z', 0)) > 1.2:
        return 'inventory_mean_reversion'
    if abs(latest.get('cot_managed_money_crowding_z', 0)) > 1.5:
        return 'positioning_crowded'
    return REGIME_NAMES.get(latest_label, 'neutral')
