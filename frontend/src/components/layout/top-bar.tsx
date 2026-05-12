import { useHealth, useDebugDb } from '@/hooks/use-health';
import { useLatestSignal, useLatestRegime } from '@/hooks/use-signal';
import { SignalBadge, RegimeBadge } from '@/components/widgets/regime-badge';
import { RefreshCw, BookOpen } from 'lucide-react';
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
    <div className="flex items-center justify-between gap-6 px-8 py-4 border-b border-border bg-bg-secondary/50 backdrop-blur-sm">
      {/* Status indicators */}
      <div className="flex items-center gap-5 flex-wrap min-w-0">
        {/* API */}
        <div className="flex items-center gap-2.5">
          <span className={`w-2.5 h-2.5 rounded-full ${apiOk ? 'bg-accent-green animate-pulse-dot' : healthError ? 'bg-accent-red' : 'bg-accent-amber animate-pulse-dot'}`} />
          <span className="text-sm font-semibold text-text-muted">API</span>
          <span className={`text-sm font-bold ${apiOk ? 'text-accent-green' : healthError ? 'text-accent-red' : 'text-accent-amber'}`}>
            {apiOk ? 'Online' : healthError ? 'Offline' : 'Checking'}
          </span>
        </div>

        {/* DB */}
        <div className="flex items-center gap-2.5">
          <span className={`w-2.5 h-2.5 rounded-full ${dbOk ? 'bg-accent-green' : dbError ? 'bg-accent-red' : 'bg-accent-amber animate-pulse-dot'}`} />
          <span className="text-sm font-semibold text-text-muted">DB</span>
          <span className={`text-sm font-bold ${dbOk ? 'text-accent-green' : dbError ? 'text-accent-red' : 'text-accent-amber'}`}>
            {dbOk ? 'Connected' : dbError ? 'Error' : 'Checking'}
          </span>
        </div>

        {/* Divider */}
        <div className="w-px h-5 bg-border" />

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
      <div className="flex items-center gap-3 shrink-0">
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-blue/15 border border-accent-blue/30 text-sm font-bold text-accent-blue hover:bg-accent-blue/25 hover:border-accent-blue/50 transition-all"
        >
          <BookOpen size={16} />
          API Docs
        </a>
        <a
          href="/redoc"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-bg-elevated border border-border text-sm font-bold text-text-secondary hover:text-text-primary hover:bg-border transition-all"
        >
          ReDoc
        </a>
        <button
          onClick={() => qc.invalidateQueries()}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-bg-elevated border border-border text-sm font-bold text-text-secondary hover:text-text-primary hover:bg-border transition-all cursor-pointer"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>
    </div>
  );
}
