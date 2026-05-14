import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Fuel,
  BarChart3,
  LineChart,
  Layers,
  Activity,
  Bug,
  ChevronLeft,
  ChevronRight,
  Droplets,
} from 'lucide-react';
import { isDebugUiEnabled } from '@/lib/debug-ui';

export type PageId = 'overview' | 'eia' | 'quanthub' | 'cot' | 'features' | 'signals' | 'debug';

interface NavItem {
  id: PageId;
  label: string;
  icon: React.ReactNode;
}

const allNavItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: <LayoutDashboard size={18} /> },
  { id: 'eia', label: 'EIA WPSR', icon: <Fuel size={18} /> },
  { id: 'quanthub', label: 'QuantHub', icon: <BarChart3 size={18} /> },
  { id: 'cot', label: 'COT Petroleum', icon: <LineChart size={18} /> },
  { id: 'features', label: 'Features', icon: <Layers size={18} /> },
  { id: 'signals', label: 'Signals', icon: <Activity size={18} /> },
  { id: 'debug', label: 'Debug / Admin', icon: <Bug size={18} /> },
];

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  /** When false, Debug / Admin is hidden from navigation (production). */
  showDebug?: boolean;
}

export function Sidebar({
  activePage,
  onNavigate,
  collapsed,
  onToggleCollapse,
  showDebug = isDebugUiEnabled(),
}: SidebarProps) {
  const navItems = showDebug ? allNavItems : allNavItems.filter((i) => i.id !== 'debug');
  return (
    <aside
      className={cn(
        'flex flex-col h-screen bg-bg-panel border-r border-border transition-all duration-300 overflow-hidden',
        collapsed ? 'w-20' : 'w-64'
      )}
    >
      {/* Brand */}
      <div className={cn(
        'flex items-center gap-3 border-b border-border transition-all duration-300',
        collapsed ? 'px-4 py-5 justify-center' : 'px-5 py-5'
      )}>
        <div className="w-8 h-8 rounded-md bg-accent-blue/10 flex items-center justify-center shrink-0">
          <Droplets size={18} className="text-accent-blue" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <h1 className="text-[14px] font-bold tracking-tight text-text-primary truncate">Oil Intelligence</h1>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-6 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={cn(
              'w-full flex items-center gap-3 font-medium cursor-pointer transition-all duration-150',
              collapsed ? 'justify-center py-3' : 'px-5 py-2.5 text-left',
              activePage === item.id
                ? 'bg-accent-blue/10 border-l-2 border-accent-blue text-accent-blue'
                : 'text-text-secondary hover:bg-[rgba(255,255,255,0.04)] hover:text-text-primary border-l-2 border-transparent opacity-80 hover:opacity-100'
            )}
            title={collapsed ? item.label : undefined}
          >
            <span className="shrink-0">{item.icon}</span>
            {!collapsed && <span className="text-sm truncate">{item.label}</span>}
          </button>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-border p-4">
        <button
          onClick={onToggleCollapse}
          className="w-full flex items-center justify-center py-2 rounded-md text-text-dim hover:text-text-secondary hover:bg-[rgba(255,255,255,0.04)] transition-colors cursor-pointer"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>
    </aside>
  );
}
