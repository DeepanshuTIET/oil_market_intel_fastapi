import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnimatePresence, motion } from 'framer-motion';
import { Sidebar, type PageId } from '@/components/layout/sidebar';
import { TopBar } from '@/components/layout/top-bar';
import { OverviewPage } from '@/pages/overview';
import { EiaPage } from '@/pages/eia';
import { QuantHubPage } from '@/pages/quanthub';
import { CotPage } from '@/pages/cot';
import { FeaturesPage } from '@/pages/features';
import { SignalsPage } from '@/pages/signals';
import { DebugPage } from '@/pages/debug';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
      staleTime: 10_000,
    },
  },
});

const PAGE_TITLES: Record<PageId, string> = {
  overview: 'Overview',
  eia: 'EIA WPSR',
  quanthub: 'QuantHub',
  cot: 'COT Petroleum',
  features: 'Features',
  signals: 'Signals',
  debug: 'Debug / Admin',
};

function AppLayout() {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [collapsed, setCollapsed] = useState(false);

  const renderPage = () => {
    switch (activePage) {
      case 'overview': return <OverviewPage />;
      case 'eia': return <EiaPage />;
      case 'quanthub': return <QuantHubPage />;
      case 'cot': return <CotPage />;
      case 'features': return <FeaturesPage />;
      case 'signals': return <SignalsPage />;
      case 'debug': return <DebugPage />;
      default: return <OverviewPage />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
      />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="mb-5">
            <h2 className="text-xl font-extrabold tracking-tight">{PAGE_TITLES[activePage]}</h2>
            <p className="text-xs text-text-muted mt-0.5">Oil Market Intelligence — Real-time Analytics</p>
          </div>
          <AnimatePresence mode="wait">
            <motion.div
              key={activePage}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
            >
              {renderPage()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppLayout />
    </QueryClientProvider>
  );
}
