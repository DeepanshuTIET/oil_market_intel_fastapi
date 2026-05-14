import { useState } from 'react';
import { motion } from 'framer-motion';
import { useEiaHistory, useIngestEia, useRunEiaPdf } from '@/hooks/use-eia';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { KpiCard } from '@/components/widgets/kpi-card';
import { TvLineChart } from '@/components/charts/tv-line-chart';
import { SkeletonCard, SkeletonChart } from '@/components/loading/skeletons';
import { formatNumber, formatTimestamp } from '@/lib/utils';
import { Download, FileText, RefreshCw, TrendingUp, TrendingDown, Minus, Database } from 'lucide-react';
import { toUserFacingMessage } from '@/lib/api-error';

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
    } catch (e: unknown) {
      setPdfResult({ error: toUserFacingMessage(e) });
    }
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      
      {/* Header */}
      <motion.div variants={item}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2">
          <div>
            <h2 className="text-page-title text-text-primary">EIA WPSR</h2>
            <p className="text-muted mt-1">Weekly Petroleum Status Report data</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="bg-transparent border border-border rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-accent-blue"
            >
              {EIA_METRICS.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
            <Button size="sm" loading={ingestEia.isPending} onClick={() => ingestEia.mutate()}>
              <Download size={14} /> Ingest
            </Button>
            <Button variant="secondary" size="sm" loading={runPdf.isPending} onClick={handleRunPdf}>
              <FileText size={14} /> Parse PDF
            </Button>
            <Button variant="secondary" size="sm" onClick={() => refetch()}>
              <RefreshCw size={14} />
            </Button>
          </div>
        </div>
        {ingestEia.isSuccess && <p className="text-xs text-success font-mono mt-2">✓ EIA ingested: {(ingestEia.data as any)?.records} records</p>}
        {ingestEia.isError && (
          <p className="text-xs text-danger mt-2 leading-relaxed">{toUserFacingMessage(ingestEia.error)}</p>
        )}
      </motion.div>

      {/* KPIs */}
      <motion.div variants={item} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
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
              valueClassName={wow != null ? (wow > 0 ? 'text-success' : wow < 0 ? 'text-danger' : 'text-warning') : ''}
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
              valueClassName="text-text-secondary"
              subtitle={`Metric: ${metric}`}
            />
          </>
        )}
      </motion.div>

      {/* Chart */}
      <motion.div variants={item}>
        <Card noPadding className="overflow-hidden border-border bg-bg-panel">
          {isLoading ? (
            <div className="p-6"><SkeletonChart height="h-80" /></div>
          ) : chartData.length > 0 ? (
            <div className="p-1">
              <TvLineChart data={chartData} height={400} color="#3b82f6" />
            </div>
          ) : (
            <EmptyState
              className="border-0 bg-transparent rounded-none"
              icon={Database}
              title="No EIA series loaded"
              description="Pull the Weekly Petroleum Status Report into the database, then refresh this chart."
              action={
                <Button size="sm" loading={ingestEia.isPending} onClick={() => ingestEia.mutate()}>
                  <Download size={14} /> Ingest EIA data
                </Button>
              }
            />
          )}
        </Card>
      </motion.div>

      {/* PDF Report Result */}
      {pdfResult && (
        <motion.div variants={item}>
          <Card title="EIA PDF Report Output">
            <pre className="bg-[#050a10] border border-border rounded-lg p-6 overflow-auto max-h-96 text-xs font-mono text-text-secondary">
              {JSON.stringify(pdfResult, null, 2)}
            </pre>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
