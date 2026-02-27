'use client';

import { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import ForceGraph, { type ForceGraphHandle } from '@/components/visualization/ForceGraph';
import GeneCard from '@/components/visualization/GeneCard';
import Legend from '@/components/visualization/Legend';
import {
  fetchEcosystemData,
  type EcosystemNode,
  type EcosystemLink,
} from '@/lib/api';

export default function EvoMapPage() {
  const t = useTranslations('evomap');
  const graphRef = useRef<ForceGraphHandle>(null);
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
        <div className="flex items-center gap-3 text-white/40">
          <div className="w-5 h-5 border-2 border-[#667eea]/30 border-t-[#667eea] rounded-full animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center" style={{ height: 'calc(100vh - 70px)' }}>
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  return (
    <div className="flex" style={{ height: 'calc(100vh - 70px)' }}>
      <aside className="w-[280px] bg-bg-root border-r border-white/[0.06] p-6 overflow-y-auto flex-shrink-0">
        <div className="mb-7">
          <h2 className="text-[11px] font-semibold text-white/40 uppercase tracking-wider mb-4">
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
                onClick={() => graphRef.current?.focusNode(gene.id)}
              />
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-[11px] font-semibold text-white/40 uppercase tracking-wider mb-4">
            {t('evolutionLog')}
          </h2>
          <div className="text-[11px] text-white/40 space-y-1.5 font-mono">
            <div>Gen 0: 5 initial seeds</div>
            <div>Gen 1: 3 survivors, 2 eliminated</div>
          </div>
        </div>
      </aside>

      <div className="flex-1 relative bg-[radial-gradient(circle_at_50%_50%,#1a1a24_0%,#0a0a0f_100%)]">
        <ForceGraph ref={graphRef} nodes={nodes} links={links} />
        <Legend />

        <div className="absolute bottom-6 right-6 flex gap-3">
          <button
            onClick={handleResetView}
            className="flex items-center gap-2 px-5 py-3 rounded-xl text-[13px] font-semibold transition-all duration-200 bg-white/[0.05] border border-white/[0.08] text-white/80 hover:bg-white/[0.08] hover:border-white/10 hover:-translate-y-0.5"
          >
            🔍 {t('resetView')}
          </button>
          <button
            onClick={handleRunEvolution}
            className="flex items-center gap-2 px-5 py-3 rounded-xl text-[13px] font-semibold transition-all duration-200 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white shadow-glow hover:opacity-90 hover:-translate-y-0.5 active:scale-95"
          >
            🔄 {t('runEvolution')}
          </button>
        </div>
      </div>
    </div>
  );
}
