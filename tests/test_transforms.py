import pandas as pd
from app.standardization.transforms import rolling_zscore


def test_rolling_zscore_runs():
    s = pd.Series(range(20), dtype=float)
    z = rolling_zscore(s, window=5)
    assert len(z) == 20
    assert z.iloc[-1] > 0
