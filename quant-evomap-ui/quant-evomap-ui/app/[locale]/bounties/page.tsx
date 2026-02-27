'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import PageHeader from '@/components/layout/PageHeader';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import EmptyState from '@/components/ui/EmptyState';
import Skeleton from '@/components/ui/Skeleton';
import BountyStatusFilter from '@/components/bounties/BountyStatusFilter';
import BountyDetail from '@/components/bounties/BountyDetail';
import CreateBountyModal from '@/components/bounties/CreateBountyModal';
import { useApiQuery } from '@/lib/hooks';
import { fetchBounties } from '@/lib/api';
import type { BountyTask, BountyStatus } from '@/lib/types';

const statusVariant = (s: string) => {
  if (s === 'completed') return 'success';
  if (s === 'failed' || s === 'expired') return 'danger';
  if (s === 'claimed') return 'warning';
  return 'neutral';
};

const taskTypeLabel: Record<string, string> = {
  discover_factor: '发现因子',
  optimize_strategy: '优化策略',
  implement_paper: '实现论文',
};

const difficultyStars = (d: number) => '★'.repeat(d) + '☆'.repeat(5 - d);

export default function BountiesPage() {
  const searchParams = useSearchParams();
  const [statusFilter, setStatusFilter] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(searchParams?.get('create') === '1');

  const { data, loading, refetch } = useApiQuery(
    () => fetchBounties(statusFilter as BountyStatus || undefined),
    [statusFilter]
  );

  const items = data?.items ?? [];

  return (
    <div className="p-8">
      <PageHeader
        title="赏金任务板"
        subtitle={`${items.length} 个任务`}
        actions={<Button variant="primary" onClick={() => setShowCreate(true)}>🎯 创建赏金任务</Button>}
      />
      <div className="mb-6">
        <BountyStatusFilter active={statusFilter} onChange={setStatusFilter} />
      </div>
      <Card>
        {loading ? (
          <div className="p-4 space-y-3">{Array.from({length: 5}).map((_,i) => <Skeleton key={i} className="h-14 w-full" />)}</div>
        ) : items.length === 0 ? (
          <EmptyState icon="🎯" title="暂无赏金任务" description="点击右上角创建第一个任务" />
        ) : (
          <div>
            {items.map((b) => (
              <div key={b.task_id} className="border-b border-white/[0.04] last:border-0">
                <button
                  className="w-full flex items-center gap-4 px-4 py-3 hover:bg-white/[0.03] transition-all duration-200 text-left"
                  onClick={() => setExpanded(expanded === b.task_id ? null : b.task_id)}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-white truncate">{b.title}</span>
                      <Badge variant={statusVariant(b.status)}>{b.status}</Badge>
                    </div>
                    <div className="flex items-center gap-4 text-[11px] text-white/40">
                      <span>{taskTypeLabel[b.task_type] ?? b.task_type}</span>
                      <span className="text-amber-400">{difficultyStars(b.difficulty)}</span>
                      <span className="text-emerald-400">{b.reward_credits} 积分</span>
                      {b.claimed_by && <span>认领者: {b.claimed_by}</span>}
                    </div>
                  </div>
                  <span className={`text-white/30 text-xs transition-transform duration-200 ${expanded === b.task_id ? 'rotate-180' : ''}`}>▼</span>
                </button>
                {expanded === b.task_id && <div className="px-4 pb-3"><BountyDetail bounty={b} onRefresh={refetch} /></div>}
              </div>
            ))}
          </div>
        )}
      </Card>
      <CreateBountyModal open={showCreate} onClose={() => setShowCreate(false)} onCreated={refetch} />
    </div>
  );
}
