/* EIA types — derived from GET /eia/history, POST /eia/pdf/run */

export interface EiaHistoryRow {
  timestamp: string | null;
  metric: string;
  value: number | null;
  metadata: Record<string, unknown>;
}

export interface EiaHistoryResponse {
  status: string;
  metric: string;
  count: number;
  rows: EiaHistoryRow[];
}

export interface EiaPdfRunResponse {
  status: string;
  message: string;
  summary: Record<string, unknown>;
  latest: Record<string, unknown>[];
  files: Record<string, string>;
}
