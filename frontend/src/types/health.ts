/* Health & Debug types — derived from GET /health, GET /debug/config, GET /debug/db */

export interface HealthResponse {
  status: string;
  dashboard: string;
  docs: string;
  debug_config: string;
  debug_db: string;
  database_url: string;
  sources: {
    eia_pdf: {
      configured: boolean;
      note: string;
    };
    quanthub: {
      base_url: string | null;
      username_loaded: boolean;
      password_loaded: boolean;
      access_token_loaded: boolean;
      refresh_token_loaded: boolean;
      endpoints: string[];
    };
    x: {
      bearer_token_loaded: boolean;
    };
  };
}

export interface DebugDbResponse {
  status: string;
  database_url: string;
  result: Record<string, unknown>;
}

export interface DebugConfigResponse {
  app_name: string;
  env: string;
  database_url: string;
  sources: Record<string, unknown>;
}

export interface DebugRouteEntry {
  path: string;
  name: string;
  methods: string[];
}

export interface DebugRoutesResponse {
  status: string;
  routes: DebugRouteEntry[];
}

export interface DebugLogResponse {
  status: string;
  path: string;
  lines: number;
  content: string[];
}
