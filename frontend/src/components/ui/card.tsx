import { cn } from '@/lib/utils';

interface CardProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  headerRight?: React.ReactNode;
  noPadding?: boolean;
}

export function Card({ title, subtitle, children, className, headerRight, noPadding }: CardProps) {
  return (
    <div className={cn(
      'rounded-2xl border border-border bg-gradient-to-b from-bg-card to-bg-card-alt shadow-lg shadow-black/20 transition-all duration-200',
      className
    )}>
      {(title || headerRight) && (
        <div className="flex items-center justify-between px-6 pt-6 pb-4">
          <div>
            {title && <h3 className="text-lg font-bold text-text-primary tracking-tight">{title}</h3>}
            {subtitle && <p className="text-sm text-text-muted mt-1">{subtitle}</p>}
          </div>
          {headerRight}
        </div>
      )}
      <div className={cn(noPadding ? '' : 'px-6 pb-6', !title && !headerRight && !noPadding && 'pt-6')}>
        {children}
      </div>
    </div>
  );
}
