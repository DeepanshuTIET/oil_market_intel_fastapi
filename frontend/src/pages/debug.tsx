import { useState } from 'react';
import { motion } from 'framer-motion';
import { useHealth, useDebugDb, useDebugConfig, useDebugRoutes, useDebugLogs } from '@/hooks/use-health';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { KpiCard } from '@/components/widgets/kpi-card';
import { apiPost, apiGet } from '@/lib/api-client';
import { toUserFacingMessage } from '@/lib/api-error';
import { API } from '@/lib/constants';
import { RefreshCw, Terminal, Database, Settings, Route, Trash2, Sparkles } from 'lucide-react';

const anim = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export function DebugPage() {
  const { data: health } = useHealth();
  const { data: dbData } = useDebugDb();
  const { data: config } = useDebugConfig();
  const { data: routes } = useDebugRoutes();
  const appLogs = useDebugLogs('app');
  const eiaLogs = useDebugLogs('eia');
  const [demoResult, setDemoResult] = useState<string | null>(null);

  const apiOk = health?.status === 'api_running';
  const dbOk = dbData?.status === 'connected';

  const ingestDemo = async () => {
    try {
      const r = await apiPost<any>(API.INGEST_DEMO);
      setDemoResult(`✓ ${r.records} synthetic records created`);
    } catch (e: unknown) {
      setDemoResult(toUserFacingMessage(e));
    }
  };

  return (
    <motion.div initial="hidden" animate="show" transition={{ staggerChildren: 0.06 }} className="space-y-5">
      {/* Status KPIs */}
      <motion.div variants={anim} className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard label="API Status" value={apiOk ? 'Online' : 'Offline'} valueClassName={apiOk ? 'text-accent-green' : 'text-accent-red'} icon={<Settings size={14} />} />
        <KpiCard label="Database" value={dbOk ? 'Connected' : 'Error'} valueClassName={dbOk ? 'text-accent-green' : 'text-accent-red'} icon={<Database size={14} />} subtitle={config?.database_url?.slice(0, 30)} />
        <KpiCard label="Environment" value={config?.env?.toUpperCase() || '—'} valueClassName="text-accent-purple" />
        <KpiCard label="Routes" value={String(routes?.routes?.length || 0)} valueClassName="text-accent-blue" icon={<Route size={14} />} />
      </motion.div>

      {/* Actions */}
      <motion.div variants={anim}>
        <Card title="Admin Actions">
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" onClick={ingestDemo}><Sparkles size={14} /> Generate Demo Data</Button>
            <Button variant="secondary" size="sm" onClick={() => appLogs.refetch()}><Terminal size={14} /> Fetch App Logs</Button>
            <Button variant="secondary" size="sm" onClick={() => eiaLogs.refetch()}><Terminal size={14} /> Fetch EIA Logs</Button>
          </div>
          {demoResult && <p className="text-xs text-text-muted font-mono mt-2">{demoResult}</p>}
        </Card>
      </motion.div>

      {/* Config */}
      {config && (
        <motion.div variants={anim}>
          <Card title="Configuration" subtitle="/debug/config">
            <pre className="bg-bg-input border border-border rounded-xl p-4 overflow-auto max-h-64 text-xs font-mono text-text-secondary">
              {JSON.stringify(config, null, 2)}
            </pre>
          </Card>
        </motion.div>
      )}

      {/* Routes */}
      {routes?.routes && (
        <motion.div variants={anim}>
          <Card title="Registered Routes" subtitle={`${routes.routes.length} routes`}>
            <div className="overflow-auto max-h-80">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-border text-text-muted"><th className="py-2 px-3 text-left">Path</th><th className="py-2 px-3 text-left">Methods</th><th className="py-2 px-3 text-left">Name</th></tr></thead>
                <tbody>{routes.routes.map((r, i) => (
                  <tr key={i} className="border-b border-border/50 hover:bg-bg-elevated/50">
                    <td className="py-1.5 px-3 font-mono text-accent-blue">{r.path}</td>
                    <td className="py-1.5 px-3">{r.methods.map(m => (
                      <span key={m} className={`inline-block mr-1 px-1.5 py-0.5 rounded text-[10px] font-bold ${m === 'POST' ? 'bg-accent-green/20 text-accent-green' : 'bg-accent-blue/20 text-accent-blue'}`}>{m}</span>
                    ))}</td>
                    <td className="py-1.5 px-3 text-text-muted">{r.name}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Logs */}
      {appLogs.data?.content && (
        <motion.div variants={anim}>
          <Card title="Application Logs" subtitle={appLogs.data.path}>
            <pre className="bg-bg-input border border-border rounded-xl p-4 overflow-auto max-h-96 text-[10px] font-mono text-text-secondary leading-relaxed">
              {appLogs.data.content.slice(-100).join('\n')}
            </pre>
          </Card>
        </motion.div>
      )}

      {eiaLogs.data?.content && (
        <motion.div variants={anim}>
          <Card title="EIA Parser Logs" subtitle={eiaLogs.data.path}>
            <pre className="bg-bg-input border border-border rounded-xl p-4 overflow-auto max-h-96 text-[10px] font-mono text-text-secondary leading-relaxed">
              {eiaLogs.data.content.slice(-100).join('\n')}
            </pre>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
