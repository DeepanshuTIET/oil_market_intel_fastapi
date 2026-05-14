import { useState } from 'react';
import { motion } from 'framer-motion';
import { useLatestSignal, useRunSignal } from '@/hooks/use-signal';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { KpiCard } from '@/components/widgets/kpi-card';
import { SignalBadge, RegimeBadge } from '@/components/widgets/regime-badge';
import { ProbabilityGauge } from '@/components/charts/gauge';
import { FeatureBarChart } from '@/components/charts/bar-chart';
import { formatPercent, formatNumber, formatTimestamp, signalColor, formatSignalLabel } from '@/lib/utils';
import { apiPost } from '@/lib/api-client';
import { API } from '@/lib/constants';
import { toUserFacingMessage } from '@/lib/api-error';
import { Play, Send, TrendingUp, AlertCircle } from 'lucide-react';

const anim = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export function SignalsPage() {
  const [instrument, setInstrument] = useState('WTI');
  const [horizon, setHorizon] = useState('5d');
  const { data: signal, isLoading } = useLatestSignal(instrument, horizon);
  const runSignal = useRunSignal();
  const [teamsResult, setTeamsResult] = useState<string | null>(null);

  const hasSignal = signal?.status === 'success' && signal.signal !== 'not_available';
  const contributions = hasSignal ? signal!.feature_contributions : {};
  const zscores = hasSignal ? signal!.feature_zscores : {};

  const sendTeams = async () => {
    try {
      await apiPost(API.ALERTS_TEAMS, { instrument, horizon });
      setTeamsResult('✓ Alert sent to Teams');
    } catch (e: unknown) {
      setTeamsResult(`Could not send: ${toUserFacingMessage(e)}`);
    }
  };

  return (
    <motion.div initial="hidden" animate="show" transition={{ staggerChildren: 0.06 }} className="space-y-6">
      {/* Header */}
      <motion.div variants={anim}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
          <div>
            <h2 className="text-page-title text-text-primary">Signal engine</h2>
            <p className="text-muted mt-1">Generate and analyze directional signals</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <select value={instrument} onChange={(e) => setInstrument(e.target.value)} className="bg-transparent border border-border rounded-md px-3 py-1.5 text-sm text-text-primary outline-none focus:border-accent-blue">
              <option value="WTI">WTI</option><option value="BRENT">BRENT</option>
            </select>
            <select value={horizon} onChange={(e) => setHorizon(e.target.value)} className="bg-transparent border border-border rounded-md px-3 py-1.5 text-sm text-text-primary outline-none focus:border-accent-blue">
              <option value="1d">1D</option><option value="5d">5D</option><option value="20d">20D</option>
            </select>
            <Button size="sm" loading={runSignal.isPending} onClick={() => runSignal.mutate({ instrument, horizon })}><Play size={14} /> Run</Button>
            <Button variant="secondary" size="sm" onClick={sendTeams}><Send size={14} /> Teams</Button>
          </div>
        </div>
      </motion.div>

      {!hasSignal && !isLoading ? (
        <motion.div variants={anim} className="py-24">
          <div className="flex flex-col items-center justify-center text-center max-w-md mx-auto">
            <div className="w-16 h-16 bg-[rgba(255,255,255,0.02)] border border-border rounded-full flex items-center justify-center mb-6">
              <AlertCircle size={24} className="text-muted" />
            </div>
            <h3 className="text-section-title text-text-primary mb-2">No signal generated yet</h3>
            <p className="text-muted mb-8 leading-relaxed">
              Run the pipeline to generate a directional forecast based on EIA data, COT positioning, and OHLC features.
            </p>
            <Button loading={runSignal.isPending} onClick={() => runSignal.mutate({ instrument, horizon })}>
              <Play size={16} /> Generate Signal Now
            </Button>
          </div>
        </motion.div>
      ) : (
        <>
          {/* Hero: single probability gauge + classification */}
          <motion.div variants={anim} className="flex justify-center">
            <Card className="w-full max-w-xl flex flex-col items-center py-10 px-6">
              <p className="text-xs uppercase tracking-wider text-text-muted mb-2">Probability up · next horizon</p>
              <ProbabilityGauge value={signal!.probability_up} label="" size={220} mode="probability" />
              <SignalBadge signal={signal!.signal} size="lg" className="mt-8" />
              <dl className="mt-10 grid w-full grid-cols-1 gap-6 border-t border-border pt-8 sm:grid-cols-3 sm:text-center">
                <div>
                  <dt className="text-[11px] font-medium uppercase tracking-wide text-text-muted">Confidence</dt>
                  <dd className="mt-1 text-lg font-semibold tabular-nums text-text-primary">{formatPercent(signal!.confidence)}</dd>
                </div>
                <div className="flex flex-col items-start sm:items-center">
                  <dt className="text-[11px] font-medium uppercase tracking-wide text-text-muted">Regime</dt>
                  <dd className="mt-2">
                    <RegimeBadge regime={signal!.regime} className="text-sm px-4 py-1.5" />
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] font-medium uppercase tracking-wide text-text-muted">As of</dt>
                  <dd className="mt-1 font-mono text-sm text-text-secondary">{formatTimestamp(signal!.timestamp)}</dd>
                </div>
              </dl>
              <p className="mt-6 text-xs text-muted">{instrument} · {horizon}</p>
            </Card>
          </motion.div>

          {/* Core metrics */}
          <motion.div variants={anim} className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard label="Signal" value={formatSignalLabel(signal!.signal)} valueClassName={signalColor(signal?.signal)} icon={<TrendingUp size={14} />} />
            <KpiCard label="Probability up" value={formatPercent(signal!.probability_up)} valueClassName="text-accent-blue" />
            <KpiCard label="Confidence" value={formatPercent(signal!.confidence)} />
            <KpiCard label="Expected return" value={formatNumber(signal!.expected_return, 4)} />
          </motion.div>

          {/* Charts — full width, stacked for hierarchy */}
          {Object.keys(contributions).length > 0 && (
            <motion.div variants={anim} className="space-y-6">
              <Card title="Feature contributions" subtitle="Weighted factor model contributions">
                <div className="mt-4">
                  <FeatureBarChart data={contributions} height={320} />
                </div>
              </Card>
              <Card title="Feature z-scores" subtitle="Standardized feature values">
                <div className="mt-4">
                  <FeatureBarChart data={zscores} height={320} colorPositive="#3b82f6" colorNegative="#f59e0b" />
                </div>
              </Card>
            </motion.div>
          )}

          <motion.div variants={anim}>
            <Card title="Raw payload" subtitle="JSON response">
              <pre className="bg-[#050a10] border border-border rounded-lg p-6 overflow-auto max-h-64 text-xs font-mono text-text-secondary mt-4">
                {JSON.stringify(signal, null, 2)}
              </pre>
            </Card>
          </motion.div>
        </>
      )}
    </motion.div>
  );
}
