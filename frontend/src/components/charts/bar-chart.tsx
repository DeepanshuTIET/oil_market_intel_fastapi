import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { featureDisplayName } from '@/lib/utils';

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

export function FeatureBarChart({
  data,
  height = 300,
  colorPositive = '#22c55e',
  colorNegative = '#ef4444',
}: FeatureBarChartProps) {
  const entries: FeatureBarEntry[] = Object.entries(data)
    .map(([name, value]) => ({ name: featureDisplayName(name), value: Number(value) || 0 }))
    .sort((a, b) => b.value - a.value);

  if (entries.length === 0) {
    return <div className="flex items-center justify-center h-32 text-text-muted text-sm">No data available</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(height, entries.length * 28)}>
      <BarChart data={entries} layout="vertical" margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
        <XAxis type="number" stroke="#4a5a7a" fontSize={10} tickLine={false} axisLine={false} />
        <YAxis type="category" dataKey="name" width={200} stroke="#4a5a7a" fontSize={10} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{
            background: '#121a2f',
            border: '1px solid #1e2b45',
            borderRadius: '12px',
            fontSize: '12px',
            color: '#eef3ff',
          }}
          formatter={(value: any) => [Number(value).toFixed(4), 'Value']}
        />
        <ReferenceLine x={0} stroke="#1e2b45" />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={16}>
          {entries.map((entry, index) => (
            <Cell key={index} fill={entry.value >= 0 ? colorPositive : colorNegative} fillOpacity={0.8} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
