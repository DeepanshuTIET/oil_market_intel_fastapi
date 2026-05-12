import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/lib/api-client';
import { API } from '@/lib/constants';
import type { CotHistoryResponse, CotSignalsResponse, CotContractsResponse } from '@/types/cot';
import type { IngestionResponse } from '@/types/common';

export function useCotHistory(contractContains = 'WTI', mode?: string, limit = 260) {
  return useQuery<CotHistoryResponse>({
    queryKey: ['cot', 'history', contractContains, mode, limit],
    queryFn: () =>
      apiGet<CotHistoryResponse>(API.COT_HISTORY, {
        contract_contains: contractContains,
        ...(mode ? { mode } : {}),
        limit,
      }),
    staleTime: 30_000,
  });
}

export function useCotSignals(contractContains = 'WTI') {
  return useQuery<CotSignalsResponse>({
    queryKey: ['cot', 'signals', contractContains],
    queryFn: () => apiGet<CotSignalsResponse>(API.COT_SIGNALS, { contract_contains: contractContains }),
    staleTime: 30_000,
  });
}

export function useCotContracts() {
  return useQuery<CotContractsResponse>({
    queryKey: ['cot', 'contracts'],
    queryFn: () => apiGet<CotContractsResponse>(API.COT_CONTRACTS),
    staleTime: 60_000,
  });
}

export function useIngestCotPetroleum() {
  const qc = useQueryClient();
  return useMutation<IngestionResponse, Error, { mode?: string }>({
    mutationFn: ({ mode = 'futures' }) =>
      apiPost<IngestionResponse>(API.INGEST_COT_PETROLEUM, { mode }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['cot'] });
    },
  });
}
