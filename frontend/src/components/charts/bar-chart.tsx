import { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { featureDisplayName } from '@/lib/display-names';

interface FeatureBarEntry {
  name: string;
  value: number;
}

interface FeatureBarChartProps {
  data: Record<string, number>;
  height?: number;
  colorPositive?: string;
  colorNegative?: string;
}

const TICK_MAX = 36;

function truncateLabel(name: string): string {
  if (name.length <= TICK_MAX) return name;
  return `${name.slice(0, TICK_MAX - 1)}…`;
}

export function FeatureBarChart({
  data,
  height = 300,
  colorPositive = '#22c55e',
  colorNegative = '#ef4444',
}: FeatureBarChartProps) {
  const entries: FeatureBarEntry[] = useMemo(
    () =>
      Object.entries(data)
        .map(([name, value]) => ({ name: featureDisplayName(name), value: Number(value) || 0 }))
        .sort((a, b) => b.value - a.value),
    [data]
  );

  const yAxisWidth = useMemo(() => {
    const longest = entries.reduce((m, e) => Math.max(m, e.name.length), 0);
    return Math.min(320, Math.max(160, 12 + longest * 6.5));
  }, [entries]);

  const chartHeight = Math.max(height, entries.length * 32);

  if (entries.length === 0) {
    return <div className="flex items-center justify-center h-32 text-text-muted text-sm">No data available</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart data={entries} layout="vertical" margin={{ top: 8, right: 28, left: 8, bottom: 8 }}>
        <XAxis type="number" stroke="#4a5a7a" fontSize={12} tickLine={false} axisLine={false} />
        <YAxis
          type="category"
          dataKey="name"
          width={yAxisWidth}
          stroke="#94a3b8"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          interval={0}
          tick={{ fill: '#94a3b8' }}
          tickFormatter={truncateLabel}
        />
        <Tooltip
          contentStyle={{
            background: '#121a2f',
            border: '1px solid #1e2b45',
            borderRadius: '12px',
            fontSize: '13px',
            color: '#eef3ff',
            maxWidth: 360,
          }}
          labelFormatter={(_, items) => {
            const row = items?.[0]?.payload as FeatureBarEntry | undefined;
            return row?.name ?? '';
          }}
          formatter={(value) => [Number(value ?? 0).toFixed(4), 'Value']}
        />
        <ReferenceLine x={0} stroke="#1e2b45" />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={18}>
          {entries.map((entry, index) => (
            <Cell key={index} fill={entry.value >= 0 ? colorPositive : colorNegative} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
