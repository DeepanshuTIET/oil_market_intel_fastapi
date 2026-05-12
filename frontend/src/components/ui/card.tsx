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
        <div className="flex items-center justify-between px-5 pt-4 pb-2">
          <div>
            {title && <h3 className="text-base font-bold text-text-primary">{title}</h3>}
            {subtitle && <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>}
          </div>
          {headerRight}
        </div>
      )}
      <div className={cn(noPadding ? '' : 'px-5 pb-5', !title && !headerRight && !noPadding && 'pt-5')}>
        {children}
      </div>
    </div>
  );
}
