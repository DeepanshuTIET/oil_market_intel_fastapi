import { cn } from '@/lib/utils';

interface GaugeProps {
  value: number; // 0 to 1
  label?: string;
  size?: number;
  className?: string;
}

export function ProbabilityGauge({ value, label, size = 140, className }: GaugeProps) {
  const clamped = Math.max(0, Math.min(1, value || 0));
  const angle = clamped * 180;
  const radius = size / 2 - 12;
  const cx = size / 2;
  const cy = size / 2 + 10;

  // Arc path
  const startAngle = Math.PI;
  const endAngle = Math.PI - (angle * Math.PI) / 180;
  const x1 = cx + radius * Math.cos(startAngle);
  const y1 = cy + radius * Math.sin(startAngle);
  const x2 = cx + radius * Math.cos(endAngle);
  const y2 = cy + radius * Math.sin(endAngle);
  const largeArc = angle > 180 ? 1 : 0;

  // Color interpolation
  let color = '#f59e0b'; // neutral
  if (clamped >= 0.55) color = '#22c55e';
  else if (clamped <= 0.45) color = '#ef4444';

  return (
    <div className={cn('flex flex-col items-center', className)}>
      <svg width={size} height={size / 2 + 24} viewBox={`0 0 ${size} ${size / 2 + 24}`}>
        {/* Background arc */}
        <path
          d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
          fill="none"
          stroke="#1e2b45"
          strokeWidth={10}
          strokeLinecap="round"
        />
        {/* Value arc */}
        {clamped > 0 && (
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
        {/* Center text */}
        <text
          x={cx}
          y={cy - 6}
          textAnchor="middle"
          fill={color}
          fontSize={size / 5}
          fontWeight="900"
          fontFamily="Inter, sans-serif"
        >
          {(clamped * 100).toFixed(1)}%
        </text>
      </svg>
      {label && <span className="text-xs text-text-muted font-medium mt-1">{label}</span>}
    </div>
  );
}
