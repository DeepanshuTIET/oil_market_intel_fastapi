import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center px-6 py-16 max-w-md mx-auto rounded-xl border border-border bg-bg-panel/40',
        className
      )}
    >
      {Icon && (
        <div className="w-14 h-14 rounded-full bg-[rgba(255,255,255,0.03)] border border-border flex items-center justify-center mb-5">
          <Icon className="w-7 h-7 text-text-dim" strokeWidth={1.5} />
        </div>
      )}
      <h3 className="text-section-title text-text-primary mb-2">{title}</h3>
      {description && <p className="text-muted text-[13px] leading-relaxed mb-6">{description}</p>}
      {action && <div className="flex flex-wrap gap-2 justify-center">{action}</div>}
    </div>
  );
}
