import { useState } from 'react';
import { motion } from 'framer-motion';
import { useLatestSignal, useRunSignal, useLatestRegime } from '@/hooks/use-signal';
import { useLatestFeatures, useBuildFeatures } from '@/hooks/use-features';
import { useQhHistory } from '@/hooks/use-quanthub';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { QueryErrorBanner } from '@/components/ui/query-error-banner';
import { SignalBadge, RegimeBadge } from '@/components/widgets/regime-badge';
import { TvCandlestick } from '@/components/charts/tv-candlestick';
import { FeatureBarChart } from '@/components/charts/bar-chart';
import { SkeletonCard } from '@/components/loading/skeletons';
import { formatPercent, formatTimestamp } from '@/lib/utils';
import { apiPost } from '@/lib/api-client';
import { API } from '@/lib/constants';
import { toUserFacingMessage } from '@/lib/api-error';
import { Play, Sparkles, LineChart } from 'lucide-react';

const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export function OverviewPage() {
  const { data: signal, isLoading: signalLoading, isError: signalError, error: signalQueryError } = useLatestSignal();
  const { data: regime } = useLatestRegime();
  const runSignal = useRunSignal();
  const buildFeatures = useBuildFeatures();

  const { data: qhData } = useQhHistory('CLN26');
  const ohlcData = qhData?.ohlc || [];

  const [pipelineStatus, setPipelineStatus] = useState<string>('');
  const [pipelineRunning, setPipelineRunning] = useState(false);

  const runDemoFlow = async () => {
    setPipelineRunning(true);
    try {
      setPipelineStatus('Ingesting demo data…');
      await apiPost(API.INGEST_DEMO);
      setPipelineStatus('Building features…');
      await apiPost(API.FEATURES_BUILD);
      setPipelineStatus('Running signal engine…');
      await apiPost(API.SIGNALS_RUN, { instrument: 'WTI', horizon: '5d' });
      setPipelineStatus('Pipeline finished successfully.');
    } catch (e: unknown) {
      setPipelineStatus(toUserFacingMessage(e));
    } finally {
      setPipelineRunning(false);
    }
  };

  const hasSignal = signal?.status === 'success' && signal.signal !== 'not_available';

  if (signalLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-12">
      {signalError && signalQueryError && (
        <motion.div variants={item}>
          <QueryErrorBanner error={signalQueryError} title="Market signal unavailable" />
        </motion.div>
      )}

      <motion.div variants={item}>
        <div className="rounded-xl border border-border bg-bg-panel overflow-hidden relative">
          <div
            className="absolute top-0 left-0 w-full h-1"
            style={{
              background:
                'linear-gradient(90deg, var(--color-accent-blue), color-mix(in srgb, var(--color-accent-blue) 10%, transparent))',
            }}
          />

          <div className="p-8 md:p-12">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 mb-12">
              <div>
                <h2 className="text-card-title mb-2">Market signal</h2>
                <div className="flex items-center gap-4">
                  {hasSignal ? (
                    <SignalBadge signal={signal!.signal} size="lg" />
                  ) : (
                    <span className="text-muted">No signal yet</span>
                  )}
                  {hasSignal && (
                    <span className="text-text-dim text-sm font-mono">{formatTimestamp(signal!.timestamp)}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button variant="secondary" size="sm" loading={buildFeatures.isPending} onClick={() => buildFeatures.mutate()}>
                  Build features
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  loading={runSignal.isPending}
                  onClick={() => runSignal.mutate({ instrument: 'WTI', horizon: '5d' })}
                >
                  Run signal
                </Button>
                <Button variant="ghost" size="sm" loading={pipelineRunning} onClick={runDemoFlow} title="Run full demo pipeline">
                  <Sparkles size={14} className="text-accent-blue" />
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
              <div className="flex flex-col gap-4">
                <span className="text-card-title">Probability up</span>
                <span className="text-[64px] font-mono font-bold leading-none text-text-primary tracking-tighter">
                  {hasSignal ? formatPercent(signal!.probability_up) : '—'}
                </span>
              </div>

              <div className="flex flex-col gap-4">
                <span className="text-card-title">Confidence</span>
                <span className="text-metric text-text-primary">
                  {hasSignal ? formatPercent(signal!.confidence) : '—'}
                </span>
              </div>

              <div className="flex flex-col gap-4">
                <span className="text-card-title">Market regime</span>
                <div className="pt-2">
                  {hasSignal ? <RegimeBadge regime={signal!.regime} /> : <span className="text-metric text-text-dim">—</span>}
                </div>
              </div>
            </div>

            {pipelineStatus && (
              <div className="mt-8 text-sm text-text-secondary border-t border-border pt-4">
                <span className="text-text-dim">Status: </span>
                {pipelineStatus}
              </div>
            )}
          </div>
        </div>
      </motion.div>

      <motion.div variants={item}>
        <div className="mb-6">
          <h2 className="text-section-title text-text-primary">Price action</h2>
          <p className="text-muted mt-1">CLN26 WTI crude oil</p>
        </div>
        <Card noPadding className="overflow-hidden">
          {ohlcData.length > 0 ? (
            <div className="p-1">
              <TvCandlestick data={ohlcData} height={400} />
            </div>
          ) : (
            <EmptyState
              className="border-0 bg-transparent py-12"
              icon={LineChart}
              title="No price data yet"
              description="Ingest OHLC from QuantHub to plot CLN26 here, or run the demo pipeline from the card above."
            />
          )}
        </Card>
      </motion.div>

      <motion.div variants={item}>
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-section-title text-text-primary">Supporting factors</h2>
            <p className="text-muted mt-1">Drivers behind the latest model read</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Feature scores" subtitle="Latest z-scores contributing to the model">
            {hasSignal && Object.keys(signal!.feature_zscores).length > 0 ? (
              <div className="mt-4">
                <FeatureBarChart data={signal!.feature_zscores} height={250} />
              </div>
            ) : (
              <EmptyState
                className="border-0 bg-transparent py-10"
                title="No feature scores"
                description="Run the signal engine after features are built to see which inputs mattered most."
              />
            )}
          </Card>

          <Card title="Signal payload" subtitle="Structured response from the inference engine">
            {hasSignal ? (
              <div className="mt-4">
                <pre className="bg-[#050a10] border border-border rounded-lg p-6 overflow-auto max-h-[250px] text-[13px] font-mono text-text-secondary">
                  {JSON.stringify(signal, null, 2)}
                </pre>
              </div>
            ) : (
              <EmptyState
                className="border-0 bg-transparent py-10"
                title="No payload yet"
                description="Run a signal to inspect the raw JSON returned by the engine."
              />
            )}
          </Card>
        </div>
      </motion.div>
    </motion.div>
  );
}
