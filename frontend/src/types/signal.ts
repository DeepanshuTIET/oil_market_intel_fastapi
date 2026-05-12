/* Signal & regime types — derived from GET /signals/latest and GET /regime/latest */

export type SignalDirection = 'bullish' | 'neutral' | 'bearish' | 'not_available';

export interface SignalResponse {
  status: string;
  timestamp: string | null;
  instrument: string;
  horizon: string;
  probability_up: number | null;
  probability_down: number | null;
  expected_return: number | null;
  confidence: number | null;
  signal: SignalDirection;
  regime: string | null;
  feature_contributions: Record<string, number>;
  feature_zscores: Record<string, number>;
  message?: string;
  fix?: string;
}

export interface SignalRunResponse {
  status: string;
  signal: {
    timestamp: string;
    instrument: string;
    horizon: string;
    probability_up: number;
    probability_down: number;
    expected_return: number;
    confidence: number;
    signal: SignalDirection;
    regime: string | null;
    feature_contributions: Record<string, number>;
    feature_zscores: Record<string, number>;
  };
}

export interface RegimeResponse {
  timestamp: string;
  regime: string;
  status: string;
}

export const REGIME_LABELS: Record<string, string> = {
  neutral: 'Neutral',
  inventory_mean_reversion: 'Inventory Mean Reversion',
  supply_shock_bullish: 'Supply Shock (Bullish)',
  positioning_crowded: 'Positioning Crowded',
  macro_demand: 'Macro Demand',
};

export const REGIME_COLORS: Record<string, string> = {
  neutral: '#f59e0b',
  inventory_mean_reversion: '#06b6d4',
  supply_shock_bullish: '#ef4444',
  positioning_crowded: '#8b5cf6',
  macro_demand: '#22c55e',
};
