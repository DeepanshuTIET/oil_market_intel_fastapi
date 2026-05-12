import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/lib/api-client';
import { API, POLLING_INTERVALS } from '@/lib/constants';
import type { FeatureRecord, FeatureMatrixResponse, FeatureBuildResponse } from '@/types/feature';

export function useLatestFeatures() {
  return useQuery<FeatureRecord[]>({
    queryKey: ['features', 'latest'],
    queryFn: () => apiGet<FeatureRecord[]>(API.FEATURES_LATEST),
    refetchInterval: POLLING_INTERVALS.FEATURES,
    staleTime: 15_000,
  });
}

export function useFeatureMatrix() {
  return useQuery<FeatureMatrixResponse>({
    queryKey: ['features', 'matrix'],
    queryFn: () => apiGet<FeatureMatrixResponse>(API.FEATURES_MATRIX),
    staleTime: 30_000,
  });
}

export function useBuildFeatures() {
  const qc = useQueryClient();
  return useMutation<FeatureBuildResponse, Error>({
    mutationFn: () => apiPost<FeatureBuildResponse>(API.FEATURES_BUILD),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['features'] });
    },
  });
}
