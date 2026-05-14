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

function decimalsForAxis(min: number, max: number): number {
  const span = Math.abs(max - min);
  if (!Number.isFinite(span) || span === 0) {
    const m = Math.max(Math.abs(min), Math.abs(max), 1);
    return m >= 1000 ? 0 : m >= 10 ? 1 : 2;
  }
  const mid = (Math.abs(min) + Math.abs(max)) / 2;
  const relative = span / Math.max(mid, 1e-12);
  if (relative > 0.02) return span >= 100 ? 0 : span >= 10 ? 1 : 2;
  if (relative > 0.001) return 2;
  return 0;
}

function axisPadding(min: number, max: number): number {
  const span = Math.abs(max - min);
  if (!Number.isFinite(span) || span === 0) {
    return Math.max(Math.abs(min), Math.abs(max), 1) * 0.02;
  }
  return Math.max(span * 0.35, Math.max(Math.abs(min), Math.abs(max)) * 0.002, 1e-9);
}

export function TvLineChart({ data, height = 320, color = '#4f8cff', areaColor }: TvLineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Area'> | null>(null);
  const rangeRef = useRef({ min: 0, max: 1 });

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
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height, color, areaColor]);

  useEffect(() => {
    if (!seriesRef.current || !data.length) return;
    const seen = new Set<string>();
    const formatted = data
      .filter((d) => d.time && !isNaN(d.value))
      .map((d) => ({ time: d.time.slice(0, 10), value: d.value }))
      .sort((a, b) => a.time.localeCompare(b.time))
      .filter((d) => {
        if (seen.has(d.time)) return false;
        seen.add(d.time);
        return true;
      });
    if (formatted.length === 0) return;

    const values = formatted.map((d) => d.value);
    const minV = Math.min(...values);
    const maxV = Math.max(...values);
    rangeRef.current = { min: minV, max: maxV };
    const pad = axisPadding(minV, maxV);
    const decimals = decimalsForAxis(minV, maxV);

    seriesRef.current.setData(formatted as any);
    seriesRef.current.applyOptions({
      autoscaleInfoProvider: () => ({
        priceRange: {
          minValue: minV - pad,
          maxValue: maxV + pad,
        },
        margins: { above: 0.12, below: 0.08 },
      }),
      priceFormat: {
        type: 'custom',
        minMove: 10 ** -Math.min(6, Math.max(0, decimals)),
        formatter: (priceValue: number) =>
          Number(priceValue).toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
          }),
      },
    });
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  return <div ref={containerRef} className="rounded-xl overflow-hidden border border-border" style={{ height }} />;
}
