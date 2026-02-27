'use client';

import Link from 'next/link';
import { useLocale } from 'next-intl';
import PageHeader from '@/components/layout/PageHeader';
import GeneDetail from '@/components/genes/GeneDetail';
import Button from '@/components/ui/Button';
import Skeleton from '@/components/ui/Skeleton';
import { useApiQuery } from '@/lib/hooks';
import { fetchGene } from '@/lib/api';

export default function GeneDetailPage({ params }: { params: { gene_id: string; locale: string } }) {
  const locale = useLocale();
  const { data, loading, error } = useApiQuery(() => fetchGene(params.gene_id), [params.gene_id]);

  return (
    <div className="p-8">
      <PageHeader
        title={loading ? '加载中...' : (data?.name ?? '未知基因')}
        subtitle={`Gene ID: ${params.gene_id}`}
        actions={
          <Link href={`/${locale}/genes`}><Button variant="secondary" size="sm">← 返回列表</Button></Link>
        }
      />
      {loading && <div className="space-y-4"><Skeleton lines={4} className="h-12 w-full" /></div>}
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {data && <GeneDetail gene={data} />}
    </div>
  );
}
