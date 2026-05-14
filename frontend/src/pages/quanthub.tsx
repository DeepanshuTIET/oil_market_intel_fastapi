import { useState } from 'react';
import { motion } from 'framer-motion';
import { useQhHistory, useIngestQhOhlc } from '@/hooks/use-quanthub';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TvCandlestick } from '@/components/charts/tv-candlestick';
import { EmptyState } from '@/components/ui/empty-state';
import { formatNumber, formatTimestamp } from '@/lib/utils';
import { Download, RefreshCw, BarChart3, Clock, LineChart } from 'lucide-react';

const anim = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export function QuantHubPage() {
  const [product, setProduct] = useState('CLN26');
  const [interval, setInterval_] = useState('1D');
  const [count, setCount] = useState(50);
  const { data, isLoading, refetch } = useQhHistory(product);
  const ingest = useIngestQhOhlc();
  const ohlcData = data?.ohlc || [];
  const latest = data?.latest || {};

  const lastOhlc = ohlcData.length > 0 ? ohlcData[ohlcData.length - 1] : null;
  const isUp = lastOhlc ? (lastOhlc.close ?? 0) >= (lastOhlc.open ?? 0) : false;

  return (
    <motion.div initial="hidden" animate="show" transition={{ staggerChildren: 0.06 }} className="space-y-6">
      
      {/* Header & Controls */}
      <motion.div variants={anim}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-2">
          <div>
            <h2 className="text-page-title text-text-primary">QuantHub OHLC</h2>
            <p className="text-muted mt-1">Fetch and visualize market data</p>
          </div>
          
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center border border-border rounded-md bg-transparent overflow-hidden focus-within:border-accent-blue">
              <input value={product} onChange={(e) => setProduct(e.target.value)} className="bg-transparent px-3 py-1.5 text-sm text-text-primary w-24 outline-none border-r border-border" placeholder="Code" />
              <select value={interval} onChange={(e) => setInterval_(e.target.value)} className="bg-transparent px-3 py-1.5 text-sm text-text-primary outline-none border-r border-border">
                <option value="1D">1D</option><option value="1H">1H</option><option value="5M">5M</option>
              </select>
              <input type="number" value={count} onChange={(e) => setCount(Number(e.target.value))} className="bg-transparent px-3 py-1.5 text-sm text-text-primary w-20 outline-none" placeholder="Count" />
            </div>
            <Button size="sm" loading={ingest.isPending} onClick={() => ingest.mutate({ instruments: product, interval, count })}><Download size={14} /> Fetch</Button>
            <Button variant="secondary" size="sm" onClick={() => refetch()}><RefreshCw size={14} /></Button>
          </div>
        </div>
        {ingest.isSuccess && <p className="text-xs text-success font-mono mt-2">✓ {(ingest.data as any)?.records} records updated</p>}
      </motion.div>

      {/* Inline Compact Metrics Bar */}
      {ohlcData.length > 0 && (
        <motion.div variants={anim}>
          <div className="flex items-center gap-6 px-4 py-3 bg-[rgba(255,255,255,0.02)] border border-border rounded-lg">
            <div className="flex items-center gap-2">
              <BarChart3 size={16} className="text-accent-blue" />
              <span className="font-bold text-text-primary tracking-wide">{product}</span>
            </div>
            <div className="w-px h-4 bg-border" />
            <div className="flex items-center gap-2">
              <span className={isUp ? 'text-success font-numeric font-bold' : 'text-danger font-numeric font-bold'}>
                {formatNumber(latest.close as number)}
              </span>
              {isUp ? <span className="text-success text-xs">▲</span> : <span className="text-danger text-xs">▼</span>}
            </div>
            <div className="w-px h-4 bg-border" />
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted">Vol</span>
              <span className="font-numeric text-text-secondary">{formatNumber(latest.volume as number, 0)}</span>
            </div>
            <div className="w-px h-4 bg-border" />
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted">Candles</span>
              <span className="font-numeric text-text-secondary">{ohlcData.length}</span>
            </div>
            <div className="w-px h-4 bg-border" />
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted">Interval</span>
              <span className="font-numeric text-text-secondary">{interval}</span>
            </div>
            <div className="w-px h-4 bg-border hidden sm:block" />
            <div className="hidden sm:flex items-center gap-2 text-xs text-muted ml-auto">
              <Clock size={12} />
              <span>{formatTimestamp(latest.timestamp as string)}</span>
            </div>
          </div>
        </motion.div>
      )}

      {/* Chart */}
      <motion.div variants={anim}>
        <Card noPadding className="overflow-hidden border-border bg-bg-panel">
          {ohlcData.length > 0 ? (
            <div className="p-1">
              <TvCandlestick data={ohlcData} height={450} />
            </div>
          ) : (
            <EmptyState
              className="border-0 bg-transparent h-[450px] justify-center"
              icon={LineChart}
              title="No candles loaded"
              description="Fetch OHLC for your symbol and interval to populate the chart and table."
              action={
                <Button size="sm" loading={ingest.isPending} onClick={() => ingest.mutate({ instruments: product, interval, count })}>
                  <Download size={14} /> Fetch OHLC
                </Button>
              }
            />
          )}
        </Card>
      </motion.div>

      {/* OHLC Table */}
      {ohlcData.length > 0 && (
        <motion.div variants={anim}>
          <Card title="OHLC Data Table" noPadding>
            <div className="overflow-x-auto max-h-80 overflow-y-auto">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-bg-panel border-b border-border z-10">
                  <tr>
                    <th className="table-header py-2 px-4">Time</th>
                    <th className="table-header py-2 px-4 text-right">O</th>
                    <th className="table-header py-2 px-4 text-right">H</th>
                    <th className="table-header py-2 px-4 text-right">L</th>
                    <th className="table-header py-2 px-4 text-right">C</th>
                    <th className="table-header py-2 px-4 text-right">Vol</th>
                  </tr>
                </thead>
                <tbody>
                  {[...ohlcData].reverse().slice(0, 40).map((r, i) => (
                    <tr key={i} className="table-row">
                      <td className="py-2 px-4 font-mono text-text-secondary text-xs">{r.timestamp?.slice(0, 10)}</td>
                      <td className="py-2 px-4 text-right font-numeric text-text-secondary text-sm">{formatNumber(r.open)}</td>
                      <td className="py-2 px-4 text-right font-numeric text-success text-sm">{formatNumber(r.high)}</td>
                      <td className="py-2 px-4 text-right font-numeric text-danger text-sm">{formatNumber(r.low)}</td>
                      <td className="py-2 px-4 text-right font-numeric font-medium text-text-primary text-sm">{formatNumber(r.close)}</td>
                      <td className="py-2 px-4 text-right font-numeric text-muted text-sm">{formatNumber(r.volume, 0)}</td>
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
