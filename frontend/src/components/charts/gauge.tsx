import { cn } from '@/lib/utils';

export type GaugeMode = 'probability' | 'confidence';

interface GaugeProps {
  value: number | null | undefined; // 0 to 1
  label?: string;
  size?: number;
  className?: string;
  /** `probability`: green above ~55%, red below ~45%. `confidence`: more is better (model certainty). */
  mode?: GaugeMode;
}

function confidenceColor(clamped: number): string {
  if (clamped >= 0.66) return '#22c55e';
  if (clamped >= 0.4) return '#f59e0b';
  return '#ef4444';
}

export function ProbabilityGauge({ value, label, size = 140, className, mode = 'probability' }: GaugeProps) {
  const hasValue = value != null && !isNaN(Number(value));
  const clamped = hasValue ? Math.max(0, Math.min(1, Number(value))) : 0;
  const angle = clamped * 180;
  const radius = size / 2 - 12;
  const cx = size / 2;
  const cy = size / 2 + 10;

  const startAngle = Math.PI;
  const endAngle = Math.PI - (angle * Math.PI) / 180;
  const x1 = cx + radius * Math.cos(startAngle);
  const y1 = cy + radius * Math.sin(startAngle);
  const x2 = cx + radius * Math.cos(endAngle);
  const y2 = cy + radius * Math.sin(endAngle);
  const largeArc = angle > 180 ? 1 : 0;

  let color = '#f59e0b';
  if (hasValue) {
    if (mode === 'probability') {
      if (clamped >= 0.55) color = '#22c55e';
      else if (clamped <= 0.45) color = '#ef4444';
    } else {
      color = confidenceColor(clamped);
    }
  } else {
    color = '#4a5a7a';
  }

  return (
    <div className={cn('flex flex-col items-center', className)}>
      <svg width={size} height={size / 2 + 24} viewBox={`0 0 ${size} ${size / 2 + 24}`}>
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke="#1e2b45"
          strokeWidth={10}
          strokeLinecap="round"
        />
        {clamped > 0 && hasValue && (
          <path
            d={`M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`}
            fill="none"
            stroke={color}
            strokeWidth={10}
            strokeLinecap="round"
            style={{
              filter: `drop-shadow(0 0 6px ${color}66)`,
              transition: 'all 0.6s ease-out',
            }}
          />
        )}
        <text
          x={cx}
          y={cy - 6}
          textAnchor="middle"
          fill={color}
          fontSize={size / 5}
          fontWeight="900"
          fontFamily="Inter, sans-serif"
        >
          {hasValue ? `${(clamped * 100).toFixed(1)}%` : '—'}
        </text>
      </svg>
      {label && <span className="text-xs text-text-muted font-medium mt-1 text-center max-w-48 leading-snug">{label}</span>}
    </div>
  );
}
