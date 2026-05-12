import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/lib/api-client';
import { API } from '@/lib/constants';
import type { EiaHistoryResponse } from '@/types/eia';
import type { IngestionResponse } from '@/types/common';

export function useEiaHistory(metric = 'refinery_utilization', limit = 260) {
  return useQuery<EiaHistoryResponse>({
    queryKey: ['eia', 'history', metric, limit],
    queryFn: () => apiGet<EiaHistoryResponse>(API.EIA_HISTORY, { metric, limit }),
    staleTime: 30_000,
  });
}

export function useIngestEia() {
  const qc = useQueryClient();
  return useMutation<IngestionResponse, Error>({
    mutationFn: () => apiPost<IngestionResponse>(API.INGEST_EIA),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['eia'] });
    },
  });
}

export function useRunEiaPdf() {
  return useMutation({
    mutationFn: () => apiPost(API.EIA_PDF_RUN),
  });
}
