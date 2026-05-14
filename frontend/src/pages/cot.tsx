import { useState } from 'react';
import { motion } from 'framer-motion';
import { useCotHistory, useCotSignals, useIngestCotPetroleum } from '@/hooks/use-cot';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { KpiCard } from '@/components/widgets/kpi-card';
import { TvLineChart } from '@/components/charts/tv-line-chart';
import { formatNumber, formatLargeNumber, cn } from '@/lib/utils';
import { cotTableColumnLabel } from '@/lib/display-names';
import { Download, RefreshCw } from 'lucide-react';

const anim = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export function CotPage() {
  const [mode, setMode] = useState('futures');
  const [contract, setContract] = useState('WTI');
  const { data: history, isLoading, refetch } = useCotHistory(contract, mode);
  const { data: signals } = useCotSignals(contract);
  const ingest = useIngestCotPetroleum();

  const latest = history?.latest || {};
  const wide = history?.wide || [];

  // Build chart data for mm_net
  const mmNetData = wide
    .filter((r: any) => r.timestamp && r.mm_net != null)
    .map((r: any) => ({ time: r.timestamp, value: Number(r.mm_net) }));

  const dealerData = wide
    .filter((r: any) => r.timestamp && r.dealer_vs_spec != null)
    .map((r: any) => ({ time: r.timestamp, value: Number(r.dealer_vs_spec) }));

  const interpMmNet = (v: number) => v > 50000 ? 'Heavily Long' : v < -50000 ? 'Heavily Short' : v > 0 ? 'Net Long' : 'Net Short';
  const interpColor = (v: number) => v > 0 ? 'text-accent-green' : 'text-accent-red';

  const tableKeys =
    wide.length > 0
      ? (() => {
          const keys = Object.keys(wide[0]);
          const priority = ['timestamp', 'contract'];
          return [...priority.filter((k) => keys.includes(k)), ...keys.filter((k) => !priority.includes(k))].slice(0, 8);
        })()
      : [];

  return (
    <motion.div initial="hidden" animate="show" transition={{ staggerChildren: 0.06 }} className="space-y-5">
      <motion.div variants={anim}>
        <Card title="CFTC COT Petroleum" subtitle="Commitments of Traders positioning data">
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <select value={mode} onChange={(e) => setMode(e.target.value)} className="bg-bg-input border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary">
              <option value="futures">Futures Only</option><option value="combined">Futures + Options</option>
            </select>
            <input value={contract} onChange={(e) => setContract(e.target.value)} className="bg-bg-input border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary w-24" placeholder="Contract" />
            <Button size="sm" loading={ingest.isPending} onClick={() => ingest.mutate({ mode })}><Download size={14} /> Fetch COT</Button>
            <Button variant="secondary" size="sm" onClick={() => refetch()}><RefreshCw size={14} /> Refresh</Button>
          </div>
          {ingest.isSuccess && <p className="text-xs text-accent-green font-mono">✓ {(ingest.data as any)?.records} records</p>}
        </Card>
      </motion.div>

      <motion.div variants={anim} className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <KpiCard label="Open interest" value={formatLargeNumber(latest.open_interest as number)} valueClassName="text-accent-blue" />
        <KpiCard label="MM net" value={formatLargeNumber(latest.mm_net as number)} valueClassName={latest.mm_net != null ? interpColor(Number(latest.mm_net)) : ''} />
        <KpiCard label="MM net % OI" value={latest.mm_net_pct != null ? `${formatNumber(Number(latest.mm_net_pct), 1)}%` : '—'} />
        <KpiCard label="Dealer vs spec" value={formatLargeNumber(latest.dealer_vs_spec as number)} valueClassName={latest.dealer_vs_spec != null ? interpColor(Number(latest.dealer_vs_spec)) : ''} />
      </motion.div>

      {/* Interpretation */}
      {latest.mm_net != null && (
        <motion.div variants={anim}>
          <Card title="COT interpretation">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                { label: 'MM Positioning', value: interpMmNet(Number(latest.mm_net)), color: interpColor(Number(latest.mm_net)) },
                { label: 'Crowding', value: signals?.latest?.mm_net_z != null ? (Math.abs(Number(signals.latest.mm_net_z)) > 1.5 ? 'Crowded' : 'Normal') : '—', color: signals?.latest?.mm_net_z != null && Math.abs(Number(signals.latest.mm_net_z)) > 1.5 ? 'text-accent-amber' : 'text-accent-green' },
                { label: 'Swap Pressure', value: latest.swap_dealer_net != null ? (Number(latest.swap_dealer_net) > 0 ? 'Long Bias' : 'Short Bias') : '—', color: latest.swap_dealer_net != null ? interpColor(Number(latest.swap_dealer_net)) : '' },
                { label: 'Producer Bias', value: latest.prod_merc_net != null ? (Number(latest.prod_merc_net) < 0 ? 'Hedging' : 'Unwinding') : '—', color: 'text-accent-cyan' },
              ].map((chip) => (
                <div key={chip.label} className="bg-bg-input border border-border rounded-xl p-3 text-center">
                  <div className="text-[11px] text-text-muted mb-1">{chip.label}</div>
                  <div className={`text-sm font-bold ${chip.color}`}>{chip.value}</div>
                </div>
              ))}
            </div>
          </Card>
        </motion.div>
      )}

      <motion.div variants={anim} className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card title="Managed Money Net Positioning">
          {mmNetData.length > 1 ? <TvLineChart data={mmNetData} height={280} color="#22c55e" /> : <div className="h-48 flex items-center justify-center text-text-muted text-sm">Need multiple dates</div>}
        </Card>
        <Card title="Dealer vs Spec Divergence">
          {dealerData.length > 1 ? <TvLineChart data={dealerData} height={280} color="#8b5cf6" /> : <div className="h-48 flex items-center justify-center text-text-muted text-sm">Need multiple dates</div>}
        </Card>
      </motion.div>

      {wide.length > 0 && (
        <motion.div variants={anim}>
          <Card title="COT Data Table">
            <div className="overflow-auto max-h-80 min-w-0">
              <table className="w-full text-xs table-fixed border-collapse min-w-0">
                <thead>
                  <tr className="border-b border-border text-text-muted">
                    {tableKeys.map((k) => (
                      <th
                        key={k}
                        className={cn(
                          'py-2 px-2 text-left font-medium whitespace-nowrap',
                          k === 'contract' && 'w-[44%]',
                        )}
                      >
                        {cotTableColumnLabel(k)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[...wide].reverse().slice(0, 30).map((r: Record<string, unknown>, i) => (
                    <tr key={i} className="border-b border-border/50 hover:bg-bg-elevated/50">
                      {tableKeys.map((k) => {
                        const raw = r[k];
                        const display =
                          typeof raw === 'number' ? formatNumber(raw, 0) : String(raw ?? '');
                        const isContract = k === 'contract';
                        return (
                          <td
                            key={k}
                            className={cn(
                              'py-1.5 px-2 text-text-secondary align-top tabular-nums',
                              isContract && 'max-w-0 overflow-hidden text-ellipsis whitespace-nowrap font-sans',
                            )}
                            title={isContract ? display : undefined}
                          >
                            {display}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
