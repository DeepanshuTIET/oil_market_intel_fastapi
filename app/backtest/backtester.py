import numpy as np
import pandas as pd


def forward_returns(price: pd.Series, horizons=(1, 5, 20)) -> pd.DataFrame:
    out = pd.DataFrame(index=price.index)
    for h in horizons:
        out[f'ret_fwd_{h}d'] = price.shift(-h) / price - 1
        out[f'up_fwd_{h}d'] = (out[f'ret_fwd_{h}d'] > 0).astype(int)
    return out


def performance_metrics(strategy_returns: pd.Series) -> dict:
    r = strategy_returns.dropna()
    if r.empty:
        return {}
    equity = (1 + r).cumprod()
    ann_ret = r.mean() * 252
    ann_vol = r.std() * np.sqrt(252)
    return {
        'annual_return': float(ann_ret),
        'annual_vol': float(ann_vol),
        'sharpe': float(ann_ret / ann_vol) if ann_vol else None,
        'max_drawdown': float((equity / equity.cummax() - 1).min()),
        'hit_rate': float((r > 0).mean()),
    }
