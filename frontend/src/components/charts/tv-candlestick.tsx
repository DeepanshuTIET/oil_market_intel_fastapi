import { useEffect, useRef } from 'react';
import { createChart, type IChartApi, type ISeriesApi, ColorType, CrosshairMode, CandlestickSeries } from 'lightweight-charts';
import type { QhOhlcRow } from '@/types/quanthub';

interface TvCandlestickProps {
  data: QhOhlcRow[];
  height?: number;
}

export function TvCandlestick({ data, height = 400 }: TvCandlestickProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height,
      layout: {
        background: { type: ColorType.Solid, color: '#080e1d' },
        textColor: '#7a8baa',
        fontFamily: 'Inter, sans-serif',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#1a2340' },
        horzLines: { color: '#1a2340' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: { borderColor: '#1e2b45' },
      timeScale: { borderColor: '#1e2b45' },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e88',
      wickDownColor: '#ef444488',
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth });
    };
    window.addEventListener('resize', handleResize);
    return () => { window.removeEventListener('resize', handleResize); chart.remove(); };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current || !data.length) return;
    const formatted = data
      .filter(d => d.timestamp && d.open != null && d.high != null && d.low != null && d.close != null)
      .map(d => ({ time: d.timestamp.slice(0, 10), open: d.open!, high: d.high!, low: d.low!, close: d.close! }))
      .sort((a, b) => a.time.localeCompare(b.time));
    if (formatted.length > 0) {
      seriesRef.current.setData(formatted as any);
      chartRef.current?.timeScale().fitContent();
    }
  }, [data]);

  return <div ref={containerRef} className="rounded-xl overflow-hidden border border-border" style={{ height }} />;
}
