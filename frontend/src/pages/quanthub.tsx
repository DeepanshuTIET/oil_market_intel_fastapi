import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQhHistory, useIngestQhOhlc } from '@/hooks/use-quanthub';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { KpiCard } from '@/components/widgets/kpi-card';
import { TvCandlestick } from '@/components/charts/tv-candlestick';
import { formatNumber, formatTimestamp } from '@/lib/utils';
import { Download, RefreshCw, BarChart3 } from 'lucide-react';

const anim = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export function QuantHubPage() {
  const [product, setProduct] = useState('CLN26');
  const [interval, setInterval_] = useState('1D');
  const [count, setCount] = useState(50);
  const { data, isLoading, refetch } = useQhHistory(product);
  const ingest = useIngestQhOhlc();
  const ohlcData = data?.ohlc || [];
  const latest = data?.latest || {};

  return (
    <motion.div initial="hidden" animate="show" transition={{ staggerChildren: 0.06 }} className="space-y-5">
      <motion.div variants={anim}>
        <Card title="QuantHub OHLC v2" subtitle="Fetch and visualize OHLC data">
          <div className="flex flex-wrap items-center gap-3 mb-3">
            <input value={product} onChange={(e) => setProduct(e.target.value)} className="bg-bg-input border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary w-24" placeholder="Code" />
            <select value={interval} onChange={(e) => setInterval_(e.target.value)} className="bg-bg-input border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary">
              <option value="1D">1D</option><option value="1H">1H</option><option value="5M">5M</option>
            </select>
            <input type="number" value={count} onChange={(e) => setCount(Number(e.target.value))} className="bg-bg-input border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary w-20" />
            <Button size="sm" loading={ingest.isPending} onClick={() => ingest.mutate({ instruments: product, interval, count })}><Download size={14} /> Fetch</Button>
            <Button variant="secondary" size="sm" onClick={() => refetch()}><RefreshCw size={14} /> Refresh</Button>
          </div>
          {ingest.isSuccess && <p className="text-xs text-accent-green font-mono">✓ {(ingest.data as any)?.records} records</p>}
        </Card>
      </motion.div>
      <motion.div variants={anim} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="Product" value={product} valueClassName="text-accent-blue" icon={<BarChart3 size={14} />} />
        <KpiCard label="Candles" value={String(ohlcData.length)} valueClassName="text-accent-purple" />
        <KpiCard label="Latest Close" value={formatNumber(latest.close as number)} subtitle={formatTimestamp(latest.timestamp as string)} />
        <KpiCard label="Volume" value={formatNumber(latest.volume as number, 0)} valueClassName="text-accent-amber" />
      </motion.div>
      <motion.div variants={anim}>
        <Card title="OHLC Chart">
          {ohlcData.length > 0 ? <TvCandlestick data={ohlcData} height={420} /> : <div className="h-64 flex items-center justify-center text-text-muted text-sm">No data</div>}
        </Card>
      </motion.div>
      {ohlcData.length > 0 && (
        <motion.div variants={anim}>
          <Card title="OHLC Table">
            <div className="overflow-auto max-h-80">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-border text-text-muted"><th className="text-left py-2 px-3">Time</th><th className="text-right py-2 px-3">O</th><th className="text-right py-2 px-3">H</th><th className="text-right py-2 px-3">L</th><th className="text-right py-2 px-3">C</th><th className="text-right py-2 px-3">Vol</th></tr></thead>
                <tbody>{[...ohlcData].reverse().slice(0, 40).map((r, i) => (
                  <tr key={i} className="border-b border-border/50 hover:bg-bg-elevated/50"><td className="py-1.5 px-3 font-mono text-text-secondary">{r.timestamp?.slice(0,10)}</td><td className="py-1.5 px-3 text-right">{formatNumber(r.open)}</td><td className="py-1.5 px-3 text-right text-accent-green">{formatNumber(r.high)}</td><td className="py-1.5 px-3 text-right text-accent-red">{formatNumber(r.low)}</td><td className="py-1.5 px-3 text-right font-bold">{formatNumber(r.close)}</td><td className="py-1.5 px-3 text-right text-text-muted">{formatNumber(r.volume,0)}</td></tr>
                ))}</tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
