import { useState } from 'react';
import { motion } from 'framer-motion';
import { useLatestSignal, useRunSignal, useLatestRegime } from '@/hooks/use-signal';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { KpiCard } from '@/components/widgets/kpi-card';
import { SignalBadge, RegimeBadge } from '@/components/widgets/regime-badge';
import { ProbabilityGauge } from '@/components/charts/gauge';
import { FeatureBarChart } from '@/components/charts/bar-chart';
import { formatPercent, formatNumber, formatTimestamp, signalColor } from '@/lib/utils';
import { apiPost } from '@/lib/api-client';
import { API } from '@/lib/constants';
import { Play, Send, TrendingUp } from 'lucide-react';

const anim = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export function SignalsPage() {
  const [instrument, setInstrument] = useState('WTI');
  const [horizon, setHorizon] = useState('5d');
  const { data: signal, isLoading } = useLatestSignal(instrument, horizon);
  const { data: regime } = useLatestRegime();
  const runSignal = useRunSignal();
  const [teamsResult, setTeamsResult] = useState<string | null>(null);

  const hasSignal = signal?.status === 'success' && signal.signal !== 'not_available';
  const contributions = hasSignal ? signal!.feature_contributions : {};
  const zscores = hasSignal ? signal!.feature_zscores : {};

  const sendTeams = async () => {
    try {
      await apiPost(API.ALERTS_TEAMS, { instrument, horizon });
      setTeamsResult('✓ Alert sent to Teams');
    } catch (e: any) {
      setTeamsResult(`✗ ${e?.message || 'Failed'}`);
    }
  };

  return (
    <motion.div initial="hidden" animate="show" transition={{ staggerChildren: 0.06 }} className="space-y-5">
      <motion.div variants={anim}>
        <Card title="Signal Engine" subtitle="Generate and analyze directional signals" headerRight={
          <div className="flex items-center gap-2">
            <select value={instrument} onChange={(e) => setInstrument(e.target.value)} className="bg-bg-input border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary">
              <option value="WTI">WTI</option><option value="BRENT">BRENT</option>
            </select>
            <select value={horizon} onChange={(e) => setHorizon(e.target.value)} className="bg-bg-input border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary">
              <option value="1d">1D</option><option value="5d">5D</option><option value="20d">20D</option>
            </select>
            <Button size="sm" loading={runSignal.isPending} onClick={() => runSignal.mutate({ instrument, horizon })}><Play size={14} /> Run</Button>
            <Button variant="secondary" size="sm" onClick={sendTeams}><Send size={14} /> Teams</Button>
          </div>
        }>
          {runSignal.isSuccess && <p className="text-xs text-accent-green font-mono">✓ Signal generated</p>}
          {teamsResult && <p className="text-xs text-text-muted font-mono">{teamsResult}</p>}
        </Card>
      </motion.div>

      {/* KPIs */}
      <motion.div variants={anim} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Signal" value={hasSignal ? signal!.signal.toUpperCase() : 'N/A'} valueClassName={signalColor(signal?.signal)} icon={<TrendingUp size={14} />} />
        <KpiCard label="Probability Up" value={hasSignal ? formatPercent(signal!.probability_up) : '—'} valueClassName="text-accent-blue" />
        <KpiCard label="Confidence" value={hasSignal ? formatPercent(signal!.confidence) : '—'} valueClassName="text-accent-purple" />
        <KpiCard label="Expected Return" value={hasSignal ? formatNumber(signal!.expected_return, 4) : '—'} valueClassName="text-text-primary" />
      </motion.div>

      {/* Gauges + Regime */}
      {hasSignal && (
        <motion.div variants={anim} className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <Card className="flex flex-col items-center py-6">
            <ProbabilityGauge value={signal!.probability_up!} label="Probability Up" size={180} />
            <SignalBadge signal={signal!.signal} size="lg" className="mt-4" />
          </Card>
          <Card className="flex flex-col items-center py-6">
            <ProbabilityGauge value={signal!.probability_down!} label="Probability Down" size={180} />
            <div className="text-xs text-text-muted mt-4">{formatTimestamp(signal!.timestamp)}</div>
          </Card>
          <Card className="flex flex-col items-center justify-center py-6">
            <div className="text-xs text-text-muted mb-3 uppercase tracking-wider">Market Regime</div>
            <RegimeBadge regime={signal!.regime} className="text-base px-5 py-2" />
            <div className="text-xs text-text-dim mt-3">{instrument} · {horizon}</div>
          </Card>
        </motion.div>
      )}

      {/* Contributions */}
      {hasSignal && Object.keys(contributions).length > 0 && (
        <motion.div variants={anim} className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <Card title="Feature Contributions" subtitle="Weighted factor model contributions">
            <FeatureBarChart data={contributions} height={300} />
          </Card>
          <Card title="Feature Z-Scores" subtitle="Standardized feature values">
            <FeatureBarChart data={zscores} height={300} colorPositive="#4f8cff" colorNegative="#f59e0b" />
          </Card>
        </motion.div>
      )}

      {/* Raw JSON */}
      {hasSignal && (
        <motion.div variants={anim}>
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
