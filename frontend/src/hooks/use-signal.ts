import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/lib/api-client';
import { API, POLLING_INTERVALS } from '@/lib/constants';
import type { SignalResponse, SignalRunResponse, RegimeResponse } from '@/types/signal';

export function useLatestSignal(instrument = 'WTI', horizon = '5d') {
  return useQuery<SignalResponse>({
    queryKey: ['signal', instrument, horizon],
    queryFn: () => apiGet<SignalResponse>(API.SIGNALS_LATEST, { instrument, horizon }),
    refetchInterval: POLLING_INTERVALS.SIGNAL,
    staleTime: 10_000,
  });
}

export function useRunSignal() {
  const qc = useQueryClient();
  return useMutation<SignalRunResponse, Error, { instrument: string; horizon: string }>({
    mutationFn: ({ instrument, horizon }) =>
      apiPost<SignalRunResponse>(API.SIGNALS_RUN, { instrument, horizon }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['signal'] });
      qc.invalidateQueries({ queryKey: ['regime'] });
    },
  });
}

export function useLatestRegime() {
  return useQuery<RegimeResponse>({
    queryKey: ['regime'],
    queryFn: () => apiGet<RegimeResponse>(API.REGIME_LATEST),
    refetchInterval: POLLING_INTERVALS.SIGNAL,
    staleTime: 10_000,
    retry: 1,
  });
}
