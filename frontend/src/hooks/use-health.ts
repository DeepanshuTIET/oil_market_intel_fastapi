import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api-client';
import { API, POLLING_INTERVALS } from '@/lib/constants';
import type { HealthResponse, DebugDbResponse, DebugConfigResponse, DebugRoutesResponse, DebugLogResponse } from '@/types/health';

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ['health'],
    queryFn: () => apiGet<HealthResponse>(API.HEALTH),
    refetchInterval: POLLING_INTERVALS.HEALTH,
    staleTime: 15_000,
    retry: 1,
  });
}

export function useDebugDb() {
  return useQuery<DebugDbResponse>({
    queryKey: ['debug', 'db'],
    queryFn: () => apiGet<DebugDbResponse>(API.DEBUG_DB),
    staleTime: 30_000,
    retry: 1,
  });
}

export function useDebugConfig() {
  return useQuery<DebugConfigResponse>({
    queryKey: ['debug', 'config'],
    queryFn: () => apiGet<DebugConfigResponse>(API.DEBUG_CONFIG),
    staleTime: 60_000,
  });
}

export function useDebugRoutes() {
  return useQuery<DebugRoutesResponse>({
    queryKey: ['debug', 'routes'],
    queryFn: () => apiGet<DebugRoutesResponse>(API.DEBUG_APP_ROUTES),
    staleTime: 300_000,
  });
}

export function useDebugLogs(type: 'app' | 'eia' = 'app', lines = 200) {
  const url = type === 'app' ? API.DEBUG_LOGS_APP : API.DEBUG_LOGS_EIA;
  return useQuery<DebugLogResponse>({
    queryKey: ['debug', 'logs', type, lines],
    queryFn: () => apiGet<DebugLogResponse>(url, { lines }),
    staleTime: 10_000,
    enabled: false, // Manual fetch only
  });
}
