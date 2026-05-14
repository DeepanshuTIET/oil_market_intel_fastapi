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
      'rounded-xl border border-border bg-bg-panel min-h-[88px] px-5 py-4 flex flex-col justify-center transition-all duration-200',
      className
    )}>
      <div className="flex items-center gap-2 mb-2">
        {icon && <span className="text-text-muted">{icon}</span>}
        <span className="text-card-title text-text-muted">{label}</span>
      </div>
      <div className={cn('text-metric', valueClassName)}>
        {value}
      </div>
      {subtitle && <span className="text-muted mt-4">{subtitle}</span>}
    </div>
  );
}
