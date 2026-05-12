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

export type PageId = 'overview' | 'eia' | 'quanthub' | 'cot' | 'features' | 'signals' | 'debug';

interface NavItem {
  id: PageId;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
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
}

export function Sidebar({ activePage, onNavigate, collapsed, onToggleCollapse }: SidebarProps) {
  return (
    <aside
      className={cn(
        'flex flex-col h-screen bg-gradient-to-b from-bg-secondary to-bg-primary border-r border-border transition-all duration-300 overflow-hidden',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Brand */}
      <div className={cn(
        'flex items-center gap-3 border-b border-border transition-all duration-300',
        collapsed ? 'px-3 py-4 justify-center' : 'px-5 py-5'
      )}>
        <div className="w-8 h-8 rounded-lg bg-accent-blue/20 flex items-center justify-center shrink-0">
          <Droplets size={18} className="text-accent-blue" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <h1 className="text-sm font-extrabold tracking-tight text-text-primary truncate">Oil Intelligence</h1>
            <p className="text-[10px] text-text-dim truncate">Market Analytics Engine</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={cn(
              'w-full flex items-center gap-3 rounded-xl font-semibold cursor-pointer transition-all duration-150',
              collapsed ? 'justify-center px-2 py-3' : 'px-3 py-2.5 text-left',
              activePage === item.id
                ? 'bg-accent-blue text-white shadow-lg shadow-accent-blue/20'
                : 'text-text-muted hover:bg-bg-elevated hover:text-text-primary'
            )}
            title={collapsed ? item.label : undefined}
          >
            <span className="shrink-0">{item.icon}</span>
            {!collapsed && <span className="text-sm truncate">{item.label}</span>}
          </button>
        ))}
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-border p-2">
        <button
          onClick={onToggleCollapse}
          className="w-full flex items-center justify-center py-2 rounded-xl text-text-dim hover:text-text-secondary hover:bg-bg-elevated transition-colors cursor-pointer"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  );
}
