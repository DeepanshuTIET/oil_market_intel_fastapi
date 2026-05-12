import { useState } from 'react';
import { motion } from 'framer-motion';
import { useEiaHistory, useIngestEia, useRunEiaPdf } from '@/hooks/use-eia';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { KpiCard } from '@/components/widgets/kpi-card';
import { TvLineChart } from '@/components/charts/tv-line-chart';
import { SkeletonCard, SkeletonChart } from '@/components/loading/skeletons';
import { formatNumber, formatTimestamp } from '@/lib/utils';
import { Download, FileText, RefreshCw, TrendingUp, TrendingDown, Minus } from 'lucide-react';

const container = { hidden: {}, show: { transition: { staggerChildren: 0.06 } } };
const item = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

const EIA_METRICS = [
  { value: 'refinery_utilization', label: 'Refinery Utilization' },
  { value: 'us_crude_stocks_ex_spr', label: 'US Crude Stocks (ex SPR)' },
  { value: 'cushing_crude_stocks', label: 'Cushing Crude Stocks' },
  { value: 'crude_imports', label: 'Crude Imports' },
  { value: 'crude_exports', label: 'Crude Exports' },
];

export function EiaPage() {
  const [metric, setMetric] = useState('refinery_utilization');
  const { data, isLoading, refetch } = useEiaHistory(metric);
  const ingestEia = useIngestEia();
  const runPdf = useRunEiaPdf();
  const [pdfResult, setPdfResult] = useState<any>(null);

  const rows = data?.rows || [];
  const latestRow = rows[rows.length - 1];
  const prevRow = rows.length > 1 ? rows[rows.length - 2] : null;
  const wow = latestRow && prevRow && latestRow.value != null && prevRow.value != null
    ? latestRow.value - prevRow.value
    : null;

  // 4-week average
  const last4 = rows.slice(-4).filter(r => r.value != null);
  const avg4w = last4.length > 0 ? last4.reduce((s, r) => s + (r.value || 0), 0) / last4.length : null;

  const chartData = rows
    .filter(r => r.timestamp && r.value != null)
    .map(r => ({ time: r.timestamp!, value: r.value! }));

  const handleRunPdf = async () => {
    try {
      const result = await runPdf.mutateAsync();
      setPdfResult(result);
    } catch (e: any) {
      setPdfResult({ error: e.message });
    }
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-5">
      {/* Controls */}
      <motion.div variants={item}>
        <Card title="EIA Weekly Petroleum Status Report" subtitle="Ingest, parse, and visualize WPSR data">
          <div className="flex flex-wrap items-center gap-3 mb-4">
            <Button size="sm" loading={ingestEia.isPending} onClick={() => ingestEia.mutate()}>
              <Download size={14} /> Ingest EIA PDF
            </Button>
            <Button variant="secondary" size="sm" loading={runPdf.isPending} onClick={handleRunPdf}>
              <FileText size={14} /> Parse PDF Report
            </Button>
            <Button variant="secondary" size="sm" onClick={() => refetch()}>
              <RefreshCw size={14} /> Refresh Chart
            </Button>
            <div className="w-px h-6 bg-border" />
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="bg-bg-input border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-accent-blue"
            >
              {EIA_METRICS.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          {/* Status messages */}
          {ingestEia.isSuccess && (
            <p className="text-xs text-accent-green font-mono">✓ EIA ingested: {(ingestEia.data as any)?.records} records</p>
          )}
          {ingestEia.isError && (
            <p className="text-xs text-accent-red font-mono">✗ {(ingestEia.error as any)?.message}</p>
          )}
        </Card>
      </motion.div>

      {/* KPIs */}
      <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          <><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></>
        ) : (
          <>
            <KpiCard
              label={`Latest ${EIA_METRICS.find(m => m.value === metric)?.label || metric}`}
              value={latestRow ? formatNumber(latestRow.value, metric === 'refinery_utilization' ? 1 : 0) : '—'}
              valueClassName="text-accent-blue"
              subtitle={latestRow ? formatTimestamp(latestRow.timestamp) : undefined}
            />
            <KpiCard
              label="WoW Change"
              value={wow != null ? `${wow >= 0 ? '+' : ''}${formatNumber(wow, metric === 'refinery_utilization' ? 2 : 0)}` : '—'}
              valueClassName={wow != null ? (wow > 0 ? 'text-accent-green' : wow < 0 ? 'text-accent-red' : 'text-accent-amber') : ''}
              icon={wow != null ? (wow > 0 ? <TrendingUp size={14} /> : wow < 0 ? <TrendingDown size={14} /> : <Minus size={14} />) : undefined}
            />
            <KpiCard
              label="4-Week Average"
              value={avg4w != null ? formatNumber(avg4w, metric === 'refinery_utilization' ? 1 : 0) : '—'}
              valueClassName="text-text-primary"
            />
            <KpiCard
              label="Data Points"
              value={String(rows.length)}
              valueClassName="text-accent-purple"
              subtitle={`Metric: ${metric}`}
            />
          </>
        )}
      </motion.div>

      {/* Chart */}
      <motion.div variants={item}>
        <Card title={`${EIA_METRICS.find(m => m.value === metric)?.label || metric} — Weekly`} subtitle="Historical EIA data stored in database">
          {isLoading ? (
            <SkeletonChart height="h-80" />
          ) : chartData.length > 0 ? (
            <TvLineChart data={chartData} height={360} color="#4f8cff" />
          ) : (
            <div className="flex items-center justify-center h-64 text-text-muted text-sm">
              No data — ingest EIA data first
            </div>
          )}
        </Card>
      </motion.div>

      {/* PDF Report Result */}
      {pdfResult && (
        <motion.div variants={item}>
          <Card title="EIA PDF Report Output">
            <pre className="bg-bg-input border border-border rounded-xl p-4 overflow-auto max-h-96 text-xs font-mono text-text-secondary">
              {JSON.stringify(pdfResult, null, 2)}
            </pre>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
