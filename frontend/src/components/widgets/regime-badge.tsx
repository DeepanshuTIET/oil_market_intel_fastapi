import { cn } from '@/lib/utils';
import type { SignalDirection } from '@/types/signal';
import { REGIME_LABELS, REGIME_COLORS } from '@/types/signal';

interface RegimeBadgeProps {
  regime: string | null | undefined;
  className?: string;
}

export function RegimeBadge({ regime, className }: RegimeBadgeProps) {
  const label = regime ? REGIME_LABELS[regime] || regime.replace(/_/g, ' ') : 'Unknown';
  const color = regime ? REGIME_COLORS[regime] || '#7a8baa' : '#7a8baa';

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border',
        className
      )}
      style={{
        color,
        borderColor: `${color}33`,
        backgroundColor: `${color}15`,
      }}
    >
      <span className="w-1.5 h-1.5 rounded-full animate-pulse-dot" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

interface SignalBadgeProps {
  signal: SignalDirection | string | null | undefined;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function SignalBadge({ signal, size = 'md', className }: SignalBadgeProps) {
  const colors: Record<string, string> = {
    bullish: 'text-accent-green bg-accent-green/15 border-accent-green/30',
    bearish: 'text-accent-red bg-accent-red/15 border-accent-red/30',
    neutral: 'text-accent-amber bg-accent-amber/15 border-accent-amber/30',
    not_available: 'text-text-muted bg-bg-elevated border-border',
  };

  const sizes = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-3 py-1',
    lg: 'text-base px-4 py-1.5',
  };

  const s = signal || 'not_available';

  return (
    <span className={cn(
      'inline-flex items-center font-extrabold uppercase tracking-wider rounded-full border',
      colors[s] || colors.not_available,
      sizes[size],
      className
    )}>
      {s === 'not_available' ? 'N/A' : s}
    </span>
  );
}
