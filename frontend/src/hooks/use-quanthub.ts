import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/lib/api-client';
import { API } from '@/lib/constants';
import type { QhHistoryResponse } from '@/types/quanthub';
import type { IngestionResponse } from '@/types/common';

export function useQhHistory(product = 'CLN26', endpointKey = 'ohlc_v2', limit = 300) {
  return useQuery<QhHistoryResponse>({
    queryKey: ['qh', 'history', product, endpointKey, limit],
    queryFn: () =>
      apiGet<QhHistoryResponse>(API.QH_HISTORY, { product, endpoint_key: endpointKey, limit }),
    staleTime: 30_000,
  });
}

export function useIngestQhOhlc() {
  const qc = useQueryClient();
  return useMutation<IngestionResponse, Error, { instruments: string; interval?: string; count?: number }>({
    mutationFn: ({ instruments, interval = '1D', count = 50 }) =>
      apiPost<IngestionResponse>(API.INGEST_QH_OHLC, { instruments, interval, count }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['qh'] });
    },
  });
}
