/* Feature types — derived from GET /features/latest and GET /features/matrix */

export interface FeatureRecord {
  timestamp: string | null;
  feature_name: string;
  source: string;
  raw_value: number | null;
  standardized_value: number;
  confidence: number;
  decay: number;
  horizon: string;
  directional_impact: string | null;
  metadata: Record<string, unknown>;
}

export interface FeatureMatrixResponse {
  timestamps: string[];
  features: string[];
  rows: Record<string, number>[];
  status: string;
}

export interface FeatureBuildResponse {
  status: string;
  features_written: number;
  feature_names?: string[];
  sample?: Record<string, unknown>[];
  message?: string;
  raw_rows?: number;
  raw_series?: string[];
}
