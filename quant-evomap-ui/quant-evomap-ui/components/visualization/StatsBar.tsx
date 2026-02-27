'use client';

import { useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';
import { fetchEcosystemData, type EcosystemStats } from '@/lib/api';
import { formatNumber } from '@/lib/utils';

export default function StatsBar() {
  const t = useTranslations('common');
  const [stats, setStats] = useState<EcosystemStats | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchEcosystemData();
        setStats(data.stats);
      } catch (e) {
        console.error('Failed to load stats:', e);
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) {
    return (
      <div className="flex gap-8">
        {['genes', 'generation', 'avgSharpe'].map((key) => (
          <div key={key} className="text-center">
            <div className="text-2xl font-bold font-mono text-white/30">-</div>
            <div className="text-[10px] text-white/40 uppercase tracking-wider mt-0.5">
              {t(key as any)}
            </div>
          </div>
        ))}
      </div>
    );
  }

  const survivalRate =
    stats.total_genes > 0
      ? Math.round(
          ((stats.total_genes - Math.floor(stats.total_genes * 0.3)) /
            stats.total_genes) *
            100
        )
      : 0;

  return (
    <div className="flex gap-8">
      <div className="text-center">
        <div className="text-2xl font-bold font-mono text-white">
          {stats.total_genes}
        </div>
        <div className="text-[10px] text-white/40 uppercase tracking-wider mt-0.5">
          {t('genes')}
        </div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold font-mono text-white">
          {stats.max_generation}
        </div>
        <div className="text-[10px] text-white/40 uppercase tracking-wider mt-0.5">
          {t('generation')}
        </div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold font-mono text-emerald-400">
          {survivalRate}%
        </div>
        <div className="text-[10px] text-white/40 uppercase tracking-wider mt-0.5">
          {t('survivalRate')}
        </div>
      </div>
      <div className="text-center">
        <div className="text-2xl font-bold font-mono text-white">
          {formatNumber(stats.avg_sharpe)}
        </div>
        <div className="text-[10px] text-white/40 uppercase tracking-wider mt-0.5">
          {t('avgSharpe')}
        </div>
      </div>
      {stats.negentropy_saved_compute !== undefined && (
        <div className="text-center">
          <div className="text-2xl font-bold font-mono text-emerald-400">
            {formatNumber(stats.negentropy_saved_compute)}
          </div>
          <div className="text-[10px] text-white/40 uppercase tracking-wider mt-0.5">
            {t('negentropy')}
          </div>
        </div>
      )}
    </div>
  );
}
