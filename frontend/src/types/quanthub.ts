/* QuantHub types — derived from GET /quanthub/history */

export interface QhOhlcRow {
  timestamp: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
}

export interface QhHistoryResponse {
  status: string;
  product: string;
  endpoint_key: string;
  count: number;
  latest: Record<string, unknown>;
  ohlc: QhOhlcRow[];
  raw_rows_count: number;
  expected_prefix: string;
  message?: string;
}
