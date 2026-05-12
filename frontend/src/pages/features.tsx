import { motion } from 'framer-motion';
import { useLatestFeatures, useFeatureMatrix, useBuildFeatures } from '@/hooks/use-features';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FeatureBarChart } from '@/components/charts/bar-chart';
import { formatNumber, formatTimestamp, featureDisplayName } from '@/lib/utils';
import { Layers, RefreshCw, Hammer } from 'lucide-react';

const anim = { hidden: { opacity: 0, y: 12 }, show: { opacity: 1, y: 0 } };

export function FeaturesPage() {
  const { data: features, isLoading, refetch } = useLatestFeatures();
  const { data: matrix } = useFeatureMatrix();
  const build = useBuildFeatures();

  const featureList = features || [];

  // Group by timestamp → latest set
  const latestTs = featureList.length > 0 ? featureList[0].timestamp : null;
  const latestFeatures = featureList.filter(f => f.timestamp === latestTs);

  // z-score dict for bar chart
  const zscores: Record<string, number> = {};
  latestFeatures.forEach(f => { zscores[f.feature_name] = f.standardized_value; });

  // Heatmap-like matrix display
  const matrixTs = matrix?.timestamps || [];
  const matrixFeats = matrix?.features || [];
  const matrixRows = matrix?.rows || [];

  return (
    <motion.div initial="hidden" animate="show" transition={{ staggerChildren: 0.06 }} className="space-y-5">
      <motion.div variants={anim}>
        <Card title="Feature Engineering" subtitle="Standardized features from raw observations" headerRight={
          <div className="flex gap-2">
            <Button size="sm" loading={build.isPending} onClick={() => build.mutate()}><Hammer size={14} /> Build</Button>
            <Button variant="secondary" size="sm" onClick={() => refetch()}><RefreshCw size={14} /></Button>
          </div>
        }>
          {build.isSuccess && <p className="text-xs text-accent-green font-mono mt-1">✓ {build.data.features_written} features written</p>}
          {build.isError && <p className="text-xs text-accent-red font-mono mt-1">✗ {build.error.message}</p>}
          <div className="text-xs text-text-muted mt-2">Latest: {latestTs ? formatTimestamp(latestTs) : '—'} · {latestFeatures.length} features</div>
        </Card>
      </motion.div>

      {/* Z-score bar chart */}
      {Object.keys(zscores).length > 0 && (
        <motion.div variants={anim}>
          <Card title="Feature Z-Scores" subtitle="Standardized values for latest timestamp">
            <FeatureBarChart data={zscores} height={350} />
          </Card>
        </motion.div>
      )}

      {/* Feature matrix heatmap */}
      {matrixTs.length > 0 && matrixFeats.length > 0 && (
        <motion.div variants={anim}>
          <Card title="Feature Matrix Heatmap" subtitle={`${matrixTs.length} timestamps × ${matrixFeats.length} features`} noPadding>
            <div className="overflow-auto max-h-[500px]">
              <table className="w-full text-[10px]">
                <thead className="sticky top-0 bg-bg-card z-10">
                  <tr><th className="py-2 px-2 text-left text-text-muted">Date</th>
                    {matrixFeats.map(f => <th key={f} className="py-2 px-1 text-text-muted font-normal whitespace-nowrap" title={f}>{f.slice(0, 12)}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {matrixRows.slice(-30).map((row, i) => (
                    <tr key={i} className="border-t border-border/30">
                      <td className="py-1 px-2 font-mono text-text-secondary whitespace-nowrap">{matrixTs[matrixTs.length - 30 + i]?.slice(0, 10)}</td>
                      {matrixFeats.map(f => {
                        const v = Number(row[f]) || 0;
                        const intensity = Math.min(Math.abs(v) / 2, 1);
                        const bg = v > 0 ? `rgba(34,197,94,${intensity * 0.5})` : v < 0 ? `rgba(239,68,68,${intensity * 0.5})` : 'transparent';
                        return <td key={f} className="py-1 px-1 text-center" style={{ background: bg }}>{v.toFixed(2)}</td>;
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Features table */}
      {latestFeatures.length > 0 && (
        <motion.div variants={anim}>
          <Card title="Latest Features Table" subtitle={`${latestFeatures.length} features`}>
            <div className="overflow-auto max-h-96">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-border text-text-muted">
                  <th className="py-2 px-3 text-left">Feature</th><th className="py-2 px-3 text-left">Source</th>
                  <th className="py-2 px-3 text-right">Raw</th><th className="py-2 px-3 text-right">Z-Score</th>
                  <th className="py-2 px-3 text-right">Confidence</th><th className="py-2 px-3 text-right">Decay</th>
                </tr></thead>
                <tbody>{latestFeatures.map((f, i) => (
                  <tr key={i} className="border-b border-border/50 hover:bg-bg-elevated/50">
                    <td className="py-1.5 px-3 font-medium">{featureDisplayName(f.feature_name)}</td>
                    <td className="py-1.5 px-3 text-text-muted">{f.source}</td>
                    <td className="py-1.5 px-3 text-right">{formatNumber(f.raw_value, 4)}</td>
                    <td className={`py-1.5 px-3 text-right font-bold ${f.standardized_value > 0 ? 'text-accent-green' : f.standardized_value < 0 ? 'text-accent-red' : ''}`}>{formatNumber(f.standardized_value, 4)}</td>
                    <td className="py-1.5 px-3 text-right text-text-muted">{formatNumber(f.confidence, 2)}</td>
                    <td className="py-1.5 px-3 text-right text-text-muted">{formatNumber(f.decay, 2)}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </Card>
        </motion.div>
      )}
    </motion.div>
  );
}
