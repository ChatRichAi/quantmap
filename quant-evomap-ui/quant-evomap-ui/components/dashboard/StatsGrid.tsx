'use client';

import StatCard from '@/components/ui/StatCard';
import Skeleton from '@/components/ui/Skeleton';
import { useApiQuery } from '@/lib/hooks';
import { fetchMetrics, fetchBounties } from '@/lib/api';

export default function StatsGrid() {
  const { data: metrics, loading: ml } = useApiQuery(() => fetchMetrics(), []);
  const { data: bounties, loading: bl } = useApiQuery(() => fetchBounties('pending'), []);

  if (ml || bl) return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {Array.from({length: 6}).map((_,i) => <div key={i} className="bg-bg-card border border-border rounded-xl p-5"><Skeleton className="h-8 w-24 mb-2" /><Skeleton className="h-4 w-16" /></div>)}
    </div>
  );

  const activeBounties = bounties?.items?.length ?? 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      <StatCard label="基因总数" value={metrics?.totals?.genes ?? 0} icon="🧬" />
      <StatCard label="事件总数" value={metrics?.totals?.events ?? 0} icon="⚡" />
      <StatCard label="活跃赏金" value={activeBounties} icon="🎯" />
      <StatCard label="最高Agent评分" value={metrics?.trust?.top_agents?.[0]?.score?.toFixed(1) ?? '—'} icon="🤖" />
      <StatCard label="Negentropy 节省" value={metrics?.negentropy?.saved_compute?.toFixed(0) ?? 0} icon="♻️" />
      <StatCard label="多样性指数" value={metrics?.negentropy?.shannon_diversity?.toFixed(2) ?? '—'} icon="🌈" />
    </div>
  );
}
