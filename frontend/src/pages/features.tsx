import { motion } from 'framer-motion';
import { useLatestFeatures, useFeatureMatrix, useBuildFeatures } from '@/hooks/use-features';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/empty-state';
import { formatNumber, formatTimestamp, featureDisplayName } from '@/lib/utils';
import { RefreshCw, Hammer } from 'lucide-react';

const anim = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export function FeaturesPage() {
  const { data: features, isLoading, refetch } = useLatestFeatures();
  const build = useBuildFeatures();

  const featureList = features || [];

  // Group by timestamp → latest set
  const latestTs = featureList.length > 0 ? featureList[0].timestamp : null;
  const latestFeatures = featureList.filter(f => f.timestamp === latestTs);

  // Sort by absolute standardized value (Z-Score) to find the most impactful features
  const sortedFeatures = [...latestFeatures].sort((a, b) => Math.abs(b.standardized_value) - Math.abs(a.standardized_value));
  
  // TOP 10 Features
  const top10 = sortedFeatures.slice(0, 10);

  return (
    <motion.div initial="hidden" animate="show" transition={{ staggerChildren: 0.06 }} className="space-y-6">
      
      {/* Header Card */}
      <motion.div variants={anim}>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h2 className="text-page-title text-text-primary">Features</h2>
            <p className="text-muted mt-1">Standardized engineering pipeline output</p>
          </div>
          <div className="flex gap-2">
            <Button size="sm" loading={build.isPending} onClick={() => build.mutate()}>
              <Hammer size={14} /> Build
            </Button>
            <Button variant="secondary" size="sm" onClick={() => refetch()}>
              <RefreshCw size={14} />
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Top 10 Features Table */}
      <motion.div variants={anim}>
        <Card title="Top 10 Impactful Features" subtitle={latestTs ? `Latest observation: ${formatTimestamp(latestTs)}` : 'No data'} noPadding>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="table-header py-3 px-6">Feature Name</th>
                  <th className="table-header py-3 px-6">Source</th>
                  <th className="table-header py-3 px-6 text-right">Raw Value</th>
                  <th className="table-header py-3 px-6 text-right">Z-Score</th>
                  <th className="table-header py-3 px-6 text-right w-32">Impact</th>
                </tr>
              </thead>
              <tbody>
                {top10.length > 0 ? top10.map((f, i) => {
                  const z = f.standardized_value;
                  const isPositive = z > 0;
                  const absZ = Math.min(Math.abs(z), 4); // Cap at 4 for visual bar
                  const barWidth = `${(absZ / 4) * 100}%`;
                  
                  return (
                    <tr key={i} className="table-row">
                      <td className="py-2 px-6">
                        <div className="font-medium text-text-primary truncate max-w-[250px]" title={featureDisplayName(f.feature_name)}>
                          {featureDisplayName(f.feature_name)}
                        </div>
                      </td>
                      <td className="py-2 px-6 text-muted">{f.source}</td>
                      <td className="py-2 px-6 text-right font-numeric text-text-secondary">{formatNumber(f.raw_value, 2)}</td>
                      <td className="py-2 px-6 text-right font-numeric font-medium">
                        <span className={z > 1 ? 'text-success' : z < -1 ? 'text-danger' : 'text-text-primary'}>
                          {z > 0 ? '+' : ''}{formatNumber(z, 2)}
                        </span>
                      </td>
                      <td className="py-2 px-6">
                        {/* Visual Impact Bar */}
                        <div className="w-24 h-1.5 bg-border rounded-full overflow-hidden ml-auto flex">
                          {isPositive ? (
                            <>
                              <div className="w-1/2" />
                              <div className="w-1/2 flex justify-start"><div className="h-full bg-success rounded-full" style={{ width: barWidth }} /></div>
                            </>
                          ) : (
                            <>
                              <div className="w-1/2 flex justify-end"><div className="h-full bg-danger rounded-full" style={{ width: barWidth }} /></div>
                              <div className="w-1/2" />
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                }) : (
                  <tr>
                    <td colSpan={5} className="p-0">
                      <EmptyState
                        className="border-0 bg-transparent max-w-none"
                        title="No feature data yet"
                        description="Build the feature matrix from ingested market data, then refresh this page."
                        action={
                          <Button size="sm" loading={build.isPending} onClick={() => build.mutate()}>
                            <Hammer size={14} /> Build features
                          </Button>
                        }
                      />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </motion.div>

      {/* Full Features Table */}
      {latestFeatures.length > 10 && (
        <motion.div variants={anim}>
          <Card title="All Features" subtitle={`${latestFeatures.length} total active features`} noPadding>
            <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
              <table className="w-full text-left border-collapse">
                <thead className="sticky top-0 bg-bg-panel border-b border-border z-10">
                  <tr>
                    <th className="table-header py-3 px-6">Feature</th>
                    <th className="table-header py-3 px-6">Source</th>
                    <th className="table-header py-3 px-6 text-right">Z-Score</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedFeatures.map((f, i) => (
                    <tr key={i} className="table-row">
                      <td className="py-2 px-6 font-medium text-text-primary truncate max-w-[200px]" title={featureDisplayName(f.feature_name)}>
                        {featureDisplayName(f.feature_name)}
                      </td>
                      <td className="py-2 px-6 text-muted">{f.source}</td>
                      <td className="py-2 px-6 text-right font-numeric text-text-secondary">{formatNumber(f.standardized_value, 2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      )}

    </motion.div>
  );
}
