/* COT Petroleum types — derived from GET /cot/petroleum/history, GET /cot/petroleum/signals */

export interface CotHistoryRow {
  timestamp: string | null;
  contract: string;
  [key: string]: unknown; // Dynamic columns from pivot
}

export interface CotHistoryResponse {
  status: string;
  contract_contains: string;
  count: number;
  latest: Record<string, unknown>;
  wide: CotHistoryRow[];
}

export interface CotSignalsResponse {
  status: string;
  contract_contains: string;
  latest: Record<string, unknown>;
  rows: Record<string, unknown>[];
}

export interface CotContractsResponse {
  status: string;
  contracts_count: number;
  contracts: Record<string, number>;
}
