import { useEffect, useRef } from 'react';
import { createChart, type IChartApi, type ISeriesApi, ColorType, CrosshairMode, AreaSeries } from 'lightweight-charts';

interface DataPoint {
  time: string;
  value: number;
}

interface TvLineChartProps {
  data: DataPoint[];
  height?: number;
  color?: string;
  areaColor?: string;
}

export function TvLineChart({ data, height = 320, color = '#4f8cff', areaColor }: TvLineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null);

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
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: '#1e2b45' },
      timeScale: { borderColor: '#1e2b45' },
    });

    const series = chart.addSeries(AreaSeries, {
      lineColor: color,
      topColor: areaColor || `${color}33`,
      bottomColor: `${color}05`,
      lineWidth: 2,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth });
    };
    window.addEventListener('resize', handleResize);
    return () => { window.removeEventListener('resize', handleResize); chart.remove(); };
  }, [height, color, areaColor]);

  useEffect(() => {
    if (!seriesRef.current || !data.length) return;
    const seen = new Set<string>();
    const formatted = data
      .filter(d => d.time && !isNaN(d.value))
      .map(d => ({ time: d.time.slice(0, 10), value: d.value }))
      .sort((a, b) => a.time.localeCompare(b.time))
      .filter(d => { if (seen.has(d.time)) return false; seen.add(d.time); return true; });
    if (formatted.length > 0) {
      seriesRef.current.setData(formatted as any);
      chartRef.current?.timeScale().fitContent();
    }
  }, [data]);

  return <div ref={containerRef} className="rounded-xl overflow-hidden border border-border" style={{ height }} />;
}
