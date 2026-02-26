'use client';

import { useEffect, useState } from 'react';
import { useTranslations } from 'next-intl';
import ForceGraph from '@/components/visualization/ForceGraph';
import GeneCard from '@/components/visualization/GeneCard';
import Legend from '@/components/visualization/Legend';
import {
  fetchEcosystemData,
  type EcosystemNode,
  type EcosystemLink,
} from '@/lib/api';

export default function EvoMapPage() {
  const t = useTranslations('evomap');
  const [nodes, setNodes] = useState<EcosystemNode[]>([]);
  const [links, setLinks] = useState<EcosystemLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchEcosystemData();
        setNodes(data.nodes);
        setLinks(data.links);
        setError(null);
      } catch (e) {
        setError('Failed to load ecosystem data');
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const topGenes = [...nodes]
    .sort((a, b) => b.score - a.score)
    .slice(0, 10);

  const handleResetView = () => {
    sessionStorage.removeItem('evomap_animated');
    window.location.reload();
  };

  const handleRunEvolution = async () => {
    alert('Evolution triggered! Check console for results.');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ height: 'calc(100vh - 70px)' }}>
        <div className="text-text-secondary">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center" style={{ height: 'calc(100vh - 70px)' }}>
        <div className="text-danger">{error}</div>
      </div>
    );
  }

  return (
    <div className="flex" style={{ height: 'calc(100vh - 70px)' }}>
      <aside className="w-[280px] bg-bg-card border-r border-border p-6 overflow-y-auto flex-shrink-0">
        <div className="mb-7">
          <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-4">
            {t('topGenes')}
          </h2>
          <div className="flex flex-col gap-2.5">
            {topGenes.map((gene) => (
              <GeneCard
                key={gene.id}
                name={gene.name}
                formula={gene.formula}
                score={gene.score}
                generation={gene.generation}
                passed={gene.score > 1.0}
              />
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-4">
            {t('evolutionLog')}
          </h2>
          <div className="text-xs text-text-secondary space-y-1">
            <div>Gen 0: 5 initial seeds</div>
            <div>Gen 1: 3 survivors, 2 eliminated</div>
          </div>
        </div>
      </aside>

      <div className="flex-1 relative bg-[radial-gradient(circle_at_50%_50%,#1e293b_0%,#0f172a_100%)]">
        <ForceGraph nodes={nodes} links={links} />
        <Legend />

        <div className="absolute bottom-6 right-6 flex gap-3">
          <button
            onClick={handleResetView}
            className="flex items-center gap-2 px-5 py-3 bg-bg-card border border-border text-text-primary rounded-xl text-[13px] font-semibold transition-all hover:bg-white/5 hover:-translate-y-0.5"
          >
            🔍 {t('resetView')}
          </button>
          <button
            onClick={handleRunEvolution}
            className="flex items-center gap-2 px-5 py-3 bg-primary text-white rounded-xl text-[13px] font-semibold transition-all hover:bg-primary-dark hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/30"
          >
            🔄 {t('runEvolution')}
          </button>
        </div>
      </div>
    </div>
  );
}
