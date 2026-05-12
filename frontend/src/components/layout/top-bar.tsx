import { useHealth, useDebugDb } from '@/hooks/use-health';
import { useLatestSignal, useLatestRegime } from '@/hooks/use-signal';
import { SignalBadge, RegimeBadge } from '@/components/widgets/regime-badge';
import { RefreshCw, ExternalLink } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';

export function TopBar() {
  const qc = useQueryClient();
  const { data: health, isError: healthError } = useHealth();
  const { data: dbData, isError: dbError } = useDebugDb();
  const { data: signal } = useLatestSignal();
  const { data: regime } = useLatestRegime();

  const apiOk = health?.status === 'api_running';
  const dbOk = dbData?.status === 'connected';

  return (
    <div className="flex items-center justify-between gap-4 px-6 py-3 border-b border-border bg-bg-secondary/50 backdrop-blur-sm">
      {/* Status indicators */}
      <div className="flex items-center gap-4 flex-wrap min-w-0">
        {/* API */}
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${apiOk ? 'bg-accent-green animate-pulse-dot' : healthError ? 'bg-accent-red' : 'bg-accent-amber animate-pulse-dot'}`} />
          <span className="text-xs font-medium text-text-muted">API</span>
          <span className={`text-xs font-bold ${apiOk ? 'text-accent-green' : healthError ? 'text-accent-red' : 'text-accent-amber'}`}>
            {apiOk ? 'Online' : healthError ? 'Offline' : 'Checking'}
          </span>
        </div>

        {/* DB */}
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${dbOk ? 'bg-accent-green' : dbError ? 'bg-accent-red' : 'bg-accent-amber animate-pulse-dot'}`} />
          <span className="text-xs font-medium text-text-muted">DB</span>
          <span className={`text-xs font-bold ${dbOk ? 'text-accent-green' : dbError ? 'text-accent-red' : 'text-accent-amber'}`}>
            {dbOk ? 'Connected' : dbError ? 'Error' : 'Checking'}
          </span>
        </div>

        {/* Divider */}
        <div className="w-px h-4 bg-border" />

        {/* Signal */}
        {signal?.signal && signal.signal !== 'not_available' && (
          <SignalBadge signal={signal.signal} size="sm" />
        )}

        {/* Regime */}
        {regime?.regime && (
          <RegimeBadge regime={regime.regime} />
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 shrink-0">
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-text-muted hover:text-accent-blue transition-colors"
        >
          <ExternalLink size={12} />
          API Docs
        </a>
        <button
          onClick={() => qc.invalidateQueries()}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-bg-elevated border border-border text-xs font-bold text-text-secondary hover:text-text-primary hover:bg-border transition-all cursor-pointer"
        >
          <RefreshCw size={12} />
          Refresh
        </button>
      </div>
    </div>
  );
}
