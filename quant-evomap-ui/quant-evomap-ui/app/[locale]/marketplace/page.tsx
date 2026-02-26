'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import EmptyState from '@/components/ui/EmptyState';
import Skeleton from '@/components/ui/Skeleton';
import SearchInput from '@/components/ui/SearchInput';
import ListingDetail from '@/components/marketplace/ListingDetail';
import { useApiQuery, useDebounce } from '@/lib/hooks';
import { fetchMarketListings } from '@/lib/api';
import type { StrategyListing } from '@/lib/types';

export default function MarketplacePage() {
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('score');
  const [expanded, setExpanded] = useState<string | null>(null);
  const debouncedSearch = useDebounce(search, 300);

  const { data, loading } = useApiQuery(() => fetchMarketListings({ sort_by: sortBy }), [sortBy]);

  const items: StrategyListing[] = (data?.items ?? []).filter((l) =>
    !debouncedSearch || l.title?.toLowerCase().includes(debouncedSearch.toLowerCase()) || l.strategy_type?.toLowerCase().includes(debouncedSearch.toLowerCase())
  );

  return (
    <div className="p-8">
      <PageHeader title="策略市场" subtitle={`${data?.count ?? 0} 个策略上架`} />
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 max-w-sm"><SearchInput value={search} onChange={setSearch} placeholder="搜索策略..." /></div>
        <select className="bg-bg-card border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-primary"
          value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
          <option value="score">按评分</option>
          <option value="sharpe">按夏普</option>
          <option value="price">按价格</option>
        </select>
      </div>
      <Card>
        {loading ? (
          <div className="p-4 space-y-3">{Array.from({length:5}).map((_,i)=><Skeleton key={i} className="h-14 w-full"/>)}</div>
        ) : items.length === 0 ? (
          <EmptyState icon="🏪" title="暂无策略上架" />
        ) : (
          <div>
            {items.map((l) => (
              <div key={l.listing_id} className="border-b border-border/50 last:border-0">
                <button
                  className="w-full flex items-center gap-4 px-4 py-3 hover:bg-white/5 transition-colors text-left"
                  onClick={() => setExpanded(expanded === l.listing_id ? null : l.listing_id)}
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-text-primary truncate">{l.title}</span>
                      <Badge variant="info">{l.strategy_type}</Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-text-secondary">
                      <span className="text-success">夏普 {l.sharpe_ratio?.toFixed(2)}</span>
                      <span className="text-warning">{l.price} 积分</span>
                      <span>{l.license_type}</span>
                      {l.score != null && <span className="text-primary">评分 {l.score.toFixed(0)}</span>}
                    </div>
                  </div>
                  <span className="text-text-secondary">{expanded === l.listing_id ? '▲' : '▼'}</span>
                </button>
                {expanded === l.listing_id && <div className="px-4 pb-3"><ListingDetail listing={l} /></div>}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
