import { cn } from '@/lib/utils';

export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div className={cn('rounded-2xl border border-border bg-bg-card p-5', className)}>
      <div className="h-4 w-24 bg-bg-elevated rounded-md mb-4 animate-shimmer" />
      <div className="h-8 w-32 bg-bg-elevated rounded-md mb-2 animate-shimmer" />
      <div className="h-3 w-20 bg-bg-elevated rounded-md animate-shimmer" />
    </div>
  );
}

export function SkeletonChart({ className, height = 'h-64' }: { className?: string; height?: string }) {
  return (
    <div className={cn('rounded-2xl border border-border bg-bg-card p-5', className)}>
      <div className="h-4 w-32 bg-bg-elevated rounded-md mb-4 animate-shimmer" />
      <div className={cn(height, 'bg-bg-input rounded-xl animate-shimmer')} />
    </div>
  );
}

export function SkeletonTable({ rows = 5, className }: { rows?: number; className?: string }) {
  return (
    <div className={cn('rounded-2xl border border-border bg-bg-card p-5', className)}>
      <div className="h-4 w-32 bg-bg-elevated rounded-md mb-4 animate-shimmer" />
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="h-8 bg-bg-elevated rounded-lg animate-shimmer" style={{ animationDelay: `${i * 0.1}s` }} />
        ))}
      </div>
    </div>
  );
}
