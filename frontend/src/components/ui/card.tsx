import { cn } from '@/lib/utils';

interface CardProps {
  title?: React.ReactNode;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  headerRight?: React.ReactNode;
  noPadding?: boolean;
}

export function Card({ title, subtitle, children, className, headerRight, noPadding }: CardProps) {
  return (
    <div className={cn(
      'rounded-xl border border-border bg-bg-panel transition-all duration-200',
      className
    )}>
      {(title || headerRight || subtitle) && (
        <div className={cn("flex items-start justify-between", noPadding ? "p-6 pb-0" : "px-6 pt-6")}>
          <div className="flex flex-col gap-1">
            {title && <h3 className="text-card-title text-text-primary">{title}</h3>}
            {subtitle && <div className="text-muted">{subtitle}</div>}
          </div>
          {headerRight && <div>{headerRight}</div>}
        </div>
      )}
      <div className={cn(noPadding ? '' : 'p-6', (!title && !headerRight && !subtitle && !noPadding) ? 'pt-6' : '')}>
        {children}
      </div>
    </div>
  );
}
