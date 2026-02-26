'use client';

import { useState } from 'react';
import PageHeader from '@/components/layout/PageHeader';
import Card from '@/components/ui/Card';
import Pagination from '@/components/ui/Pagination';
import GeneFilterBar from '@/components/genes/GeneFilterBar';
import GeneTable from '@/components/genes/GeneTable';
import { useApiQuery, useDebounce, usePagination } from '@/lib/hooks';
import { fetchGenes } from '@/lib/api';
import type { Gene } from '@/lib/types';

export default function GenesPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const { offset, limit, currentPage, nextPage, prevPage } = usePagination(50);

  const { data, loading } = useApiQuery(
    () => fetchGenes(limit, offset),
    [offset, limit]
  );

  const filtered: Gene[] = (data?.items ?? []).filter((g) => {
    const matchSearch = !debouncedSearch || g.name?.toLowerCase().includes(debouncedSearch.toLowerCase()) || g.formula?.toLowerCase().includes(debouncedSearch.toLowerCase());
    const matchStatus = !statusFilter || g.validation?.status === statusFilter;
    return matchSearch && matchStatus;
  });

  return (
    <div className="p-8">
      <PageHeader title="基因浏览器" subtitle={`共 ${data?.count ?? 0} 个基因`} />
      <GeneFilterBar search={search} onSearch={setSearch} status={statusFilter} onStatus={setStatusFilter} />
      <Card>
        <GeneTable data={filtered} loading={loading} />
        <Pagination currentPage={currentPage} hasNext={(data?.count ?? 0) > offset + limit} onNext={nextPage} onPrev={prevPage} />
      </Card>
    </div>
  );
}
