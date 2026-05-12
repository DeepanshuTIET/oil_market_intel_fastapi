/* Shared types used across the frontend */

export interface ApiError {
  status: string;
  message: string;
  fix?: string;
  traceback?: string;
  raw_error?: string;
  database_url?: string;
}

export interface IngestionResponse {
  source: string;
  records: number;
  status: string;
  message?: string;
  columns?: string[];
  sample?: Record<string, unknown>[];
  warning?: string;
}

export interface PipelineStep {
  id: string;
  label: string;
  endpoint: string;
  method: 'GET' | 'POST';
  status: 'idle' | 'running' | 'success' | 'error';
  result?: unknown;
  error?: string;
}
