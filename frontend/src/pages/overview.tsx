import { useState } from 'react';
import { motion } from 'framer-motion';
import { useLatestSignal, useRunSignal, useLatestRegime } from '@/hooks/use-signal';
import { useLatestFeatures, useBuildFeatures } from '@/hooks/use-features';
import { useHealth } from '@/hooks/use-health';
import { KpiCard } from '@/components/widgets/kpi-card';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SignalBadge, RegimeBadge } from '@/components/widgets/regime-badge';
import { ProbabilityGauge } from '@/components/charts/gauge';
import { FeatureBarChart } from '@/components/charts/bar-chart';
import { SkeletonCard, SkeletonChart } from '@/components/loading/skeletons';
import { formatPercent, formatNumber, signalColor, formatTimestamp } from '@/lib/utils';
import { apiPost } from '@/lib/api-client';
import { API } from '@/lib/constants';
import { Zap, TrendingUp, Shield, Gauge, Play, RotateCw, Sparkles } from 'lucide-react';

const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export function OverviewPage() {
  const { data: signal, isLoading: signalLoading } = useLatestSignal();
  const { data: regime, isLoading: regimeLoading } = useLatestRegime();
  const { data: health } = useHealth();
  const runSignal = useRunSignal();
  const buildFeatures = useBuildFeatures();

  const [pipelineStatus, setPipelineStatus] = useState<string>('');
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineProgress, setPipelineProgress] = useState(0);

  const runDemoFlow = async () => {
    setPipelineRunning(true);
    setPipelineProgress(0);
    try {
      setPipelineStatus('Ingesting demo data...');
      setPipelineProgress(20);
      await apiPost(API.INGEST_DEMO);

      setPipelineStatus('Building features...');
      setPipelineProgress(50);
      await apiPost(API.FEATURES_BUILD);

      setPipelineStatus('Running signal engine...');
      setPipelineProgress(75);
      await apiPost(API.SIGNALS_RUN, { instrument: 'WTI', horizon: '5d' });

      setPipelineStatus('✓ Pipeline complete');
      setPipelineProgress(100);
    } catch (e: any) {
      setPipelineStatus(`Error: ${e?.message || 'Pipeline failed'}`);
    } finally {
      setPipelineRunning(false);
    }
  };

  const hasSignal = signal?.status === 'success' && signal.signal !== 'not_available';

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
      {/* KPI Row */}
      <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {signalLoading ? (
          <>
            <SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard />
          </>
        ) : (
          <>
            <KpiCard
              label="API Status"
              value={health?.status === 'api_running' ? 'Online' : 'Offline'}
              valueClassName={health?.status === 'api_running' ? 'text-accent-green' : 'text-accent-red'}
              icon={<Shield size={14} />}
            />
            <KpiCard
              label="Latest Signal"
              value={hasSignal ? signal!.signal!.toUpperCase() : 'N/A'}
              valueClassName={signalColor(signal?.signal)}
              icon={<TrendingUp size={14} />}
              subtitle={hasSignal ? `Confidence: ${formatPercent(signal!.confidence)}` : 'Run pipeline first'}
            />
            <KpiCard
              label="Probability Up"
              value={hasSignal ? formatPercent(signal!.probability_up) : '—'}
              valueClassName="text-accent-blue"
              icon={<Gauge size={14} />}
              subtitle={hasSignal ? `Expected Return: ${formatNumber(signal!.expected_return, 4)}` : undefined}
            />
            <KpiCard
              label="Market Regime"
              value={regime?.regime?.replace(/_/g, ' ').toUpperCase() || 'N/A'}
              valueClassName="text-accent-cyan"
              icon={<Zap size={14} />}
              subtitle={regime?.timestamp ? formatTimestamp(String(regime.timestamp)) : undefined}
            />
          </>
        )}
      </motion.div>

      {/* Pipeline Runner */}
      <motion.div variants={item}>
        <Card title="Pipeline" subtitle="Execute the full ingestion → features → signal pipeline">
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <Button
              variant="primary"
              size="sm"
              onClick={() => apiPost(API.INGEST_EIA).then(() => setPipelineStatus('EIA ingested'))}
            >
              <Fuel size={14} /> Ingest EIA
            </Button>
            <Button
              variant="secondary"
              size="sm"
              loading={buildFeatures.isPending}
              onClick={() => buildFeatures.mutate()}
            >
              <Layers size={14} /> Build Features
            </Button>
            <Button
              variant="secondary"
              size="sm"
              loading={runSignal.isPending}
              onClick={() => runSignal.mutate({ instrument: 'WTI', horizon: '5d' })}
            >
              <Activity size={14} /> Run Signal
            </Button>
            <div className="w-px h-6 bg-border mx-1" />
            <Button variant="demo" size="sm" loading={pipelineRunning} onClick={runDemoFlow}>
              <Sparkles size={14} /> Demo Full Flow
            </Button>
          </div>

          {/* Progress bar */}
          <div className="h-2 bg-bg-input rounded-full overflow-hidden border border-border">
            <motion.div
              className="h-full bg-gradient-to-r from-accent-blue to-accent-green rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${pipelineProgress}%` }}
              transition={{ duration: 0.3 }}
            />
          </div>
          {pipelineStatus && (
            <p className="text-xs text-text-muted mt-2 font-mono">{pipelineStatus}</p>
          )}
        </Card>
      </motion.div>

      {/* Signal + Features */}
      <motion.div variants={item} className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Signal gauge */}
        <Card title="Signal Analysis" subtitle={hasSignal ? `${signal!.instrument} · ${signal!.horizon}` : undefined}>
          {hasSignal ? (
            <div className="flex flex-col items-center gap-4">
              <div className="flex items-center gap-8">
                <ProbabilityGauge value={signal!.probability_up!} label="Prob Up" size={150} />
                <div className="text-center space-y-3">
                  <SignalBadge signal={signal!.signal} size="lg" />
                  <RegimeBadge regime={signal!.regime} />
                  <div className="text-xs text-text-muted">
                    {formatTimestamp(signal!.timestamp)}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-text-muted">
              <Play size={32} className="mb-3 opacity-40" />
              <p className="text-sm">No signal available</p>
              <p className="text-xs mt-1">Run the pipeline to generate signals</p>
            </div>
          )}
        </Card>

        {/* Feature contributions */}
        <Card title="Feature Z-Scores" subtitle="Latest standardized feature values">
          {hasSignal && Object.keys(signal!.feature_zscores).length > 0 ? (
            <FeatureBarChart data={signal!.feature_zscores} height={250} />
          ) : (
            <div className="flex items-center justify-center py-16 text-text-muted text-sm">
              No feature data — run pipeline first
            </div>
          )}
        </Card>
      </motion.div>

      {/* Signal JSON */}
      {hasSignal && (
        <motion.div variants={item}>
          <Card title="Raw Signal Response">
            <pre className="bg-bg-input border border-border rounded-xl p-4 overflow-auto max-h-64 text-xs font-mono text-text-secondary">
              {JSON.stringify(signal, null, 2)}
            </pre>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}

// Tiny icon imports used in JSX
function Fuel(props: { size: number }) {
  return <svg width={props.size} height={props.size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 22V6a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"/><path d="M15 22H3"/><path d="M15 10h2a2 2 0 0 1 2 2v2a2 2 0 0 0 2 2h0a2 2 0 0 0 2-2V9.83a2 2 0 0 0-.59-1.42L18 4"/><path d="M7 10h4"/></svg>;
}
function Layers(props: { size: number }) {
  return <svg width={props.size} height={props.size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>;
}
function Activity(props: { size: number }) {
  return <svg width={props.size} height={props.size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>;
}
