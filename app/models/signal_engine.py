from datetime import timezone
import pandas as pd
from app.models.regime import detect_latest_regime
from app.models.factor_model import compute_score, confidence_from_contributions, signal_from_score


def run_signal_engine(feature_matrix: pd.DataFrame, instrument: str = 'WTI', horizon: str = '5d') -> dict:
    if feature_matrix.empty:
        raise ValueError('No features available. Run ingestion and feature build first.')
    feature_matrix = feature_matrix.sort_index().fillna(0.0)
    latest_ts = feature_matrix.index[-1]
    latest_row = feature_matrix.iloc[-1]
    regime = detect_latest_regime(feature_matrix)
    score, contributions = compute_score(latest_row, regime=regime)
    p_up, p_down, signal, expected_return = signal_from_score(score)
    confidence = confidence_from_contributions(contributions)
    return {
        'timestamp': latest_ts.to_pydatetime() if hasattr(latest_ts, 'to_pydatetime') else latest_ts,
        'instrument': instrument,
        'horizon': horizon,
        'probability_up': p_up,
        'probability_down': p_down,
        'expected_return': expected_return,
        'confidence': confidence,
        'signal': signal,
        'regime': regime,
        'feature_contributions': contributions,
        'feature_zscores': {k: float(v) for k, v in latest_row.to_dict().items()},
    }
