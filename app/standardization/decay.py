import numpy as np


def exponential_decay(age_days: float, half_life_days: float) -> float:
    if half_life_days <= 0:
        return 0.0
    return float(np.exp(-np.log(2) * age_days / half_life_days))


def half_life_for_feature(feature_name: str) -> float:
    if feature_name.startswith('news_'):
        return 5.0
    if feature_name.startswith('cot_'):
        return 21.0
    if 'inventory' in feature_name:
        return 10.0
    if 'momentum' in feature_name:
        return 14.0
    return 10.0
