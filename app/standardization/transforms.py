import numpy as np
import pandas as pd


def rolling_zscore(series: pd.Series, window: int = 52, min_periods: int | None = None) -> pd.Series:
    min_periods = min_periods or max(5, window // 4)
    mean = series.rolling(window, min_periods=min_periods).mean()
    std = series.rolling(window, min_periods=min_periods).std().replace(0, np.nan)
    return ((series - mean) / std).replace([np.inf, -np.inf], np.nan).fillna(0.0)


def momentum_z(series: pd.Series, short: int = 4, long: int = 13, z_window: int = 52) -> pd.Series:
    mom = series.rolling(short, min_periods=2).mean() - series.rolling(long, min_periods=4).mean()
    return rolling_zscore(mom, z_window)


def inventory_surprise_z(series: pd.Series, window: int = 52) -> pd.Series:
    return rolling_zscore(series.diff(), window)


def bounded_probability(score: float) -> float:
    return float(1 / (1 + np.exp(-score)))
