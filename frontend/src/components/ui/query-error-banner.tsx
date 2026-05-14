import { AlertTriangle } from 'lucide-react';
import { toUserFacingMessage } from '@/lib/api-error';

interface QueryErrorBannerProps {
  error: unknown;
  title?: string;
  className?: string;
}

export function QueryErrorBanner({ error, title = 'Could not load data', className }: QueryErrorBannerProps) {
  const message = toUserFacingMessage(error);
  return (
    <div
      role="alert"
      className={`flex gap-3 rounded-lg border border-accent-amber/25 bg-accent-amber/10 px-4 py-3 text-sm text-text-secondary ${className ?? ''}`}
    >
      <AlertTriangle className="w-5 h-5 shrink-0 text-accent-amber mt-0.5" />
      <div>
        <p className="font-medium text-text-primary">{title}</p>
        <p className="mt-1 text-muted leading-relaxed">{message}</p>
      </div>
    </div>
  );
}
