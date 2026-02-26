'use client';

import { useRouter, usePathname } from 'next/navigation';
import { useLocale } from 'next-intl';
import Table, { Column } from '@/components/ui/Table';
import Badge from '@/components/ui/Badge';
import type { Gene } from '@/lib/types';

const statusVariant = (status?: string) => {
  if (status === 'validated') return 'success';
  if (status === 'rejected') return 'danger';
  return 'neutral';
};

interface GeneTableProps {
  data: Gene[];
  loading: boolean;
}

export default function GeneTable({ data, loading }: GeneTableProps) {
  const router = useRouter();
  const locale = useLocale();

  const columns: Column<Gene>[] = [
    { key: 'name', header: '名称', render: (g) => <span className="font-medium text-text-primary">{g.name}</span> },
    { key: 'formula', header: '公式', render: (g) => <code className="text-xs text-info bg-info/10 px-2 py-0.5 rounded">{g.formula?.slice(0, 40)}{(g.formula?.length ?? 0) > 40 ? '…' : ''}</code> },
    { key: 'generation', header: '世代', render: (g) => <span className="text-text-secondary">G{g.generation}</span> },
    { key: 'sharpe', header: '夏普', render: (g) => <span className={g.validation?.sharpe_ratio ? 'text-success' : 'text-text-secondary'}>{g.validation?.sharpe_ratio?.toFixed(2) ?? '—'}</span> },
    { key: 'status', header: '状态', render: (g) => <Badge variant={statusVariant(g.validation?.status)}>{g.validation?.status ?? 'pending'}</Badge> },
    { key: 'author', header: '来源', render: (g) => <span className="text-xs text-text-secondary">{g.author || g.meta?.author || '—'}</span> },
  ];

  return (
    <Table
      columns={columns}
      data={data}
      loading={loading}
      emptyMessage="暂无基因数据"
      rowKey={(g) => g.gene_id}
      onRowClick={(g) => router.push(`/${locale}/genes/${g.gene_id}`)}
    />
  );
}
