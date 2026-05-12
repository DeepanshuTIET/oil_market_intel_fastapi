import { cn } from '@/lib/utils';

interface KpiCardProps {
  label: string;
  value: string;
  className?: string;
  valueClassName?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'flat';
  subtitle?: string;
}

export function KpiCard({ label, value, className, valueClassName, icon, subtitle }: KpiCardProps) {
  return (
    <div className={cn(
      'rounded-2xl border border-border bg-bg-input p-4 flex flex-col gap-2 transition-all duration-200 hover:border-border-light',
      className
    )}>
      <div className="flex items-center gap-2">
        {icon && <span className="text-text-muted">{icon}</span>}
        <span className="text-xs font-medium text-text-muted uppercase tracking-wider">{label}</span>
      </div>
      <div className={cn('text-2xl font-black tracking-tight', valueClassName)}>
        {value}
      </div>
      {subtitle && <span className="text-xs text-text-dim">{subtitle}</span>}
    </div>
  );
}
