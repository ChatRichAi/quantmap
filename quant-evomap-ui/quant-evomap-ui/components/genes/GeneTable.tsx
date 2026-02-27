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
    { key: 'name', header: '名称', render: (g) => <span className="font-medium text-white">{g.name}</span> },
    { key: 'formula', header: '公式', render: (g) => <code className="text-[11px] text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-md font-mono">{g.formula?.slice(0, 40)}{(g.formula?.length ?? 0) > 40 ? '…' : ''}</code> },
    { key: 'generation', header: '世代', render: (g) => <span className="text-white/50 font-mono text-xs">G{g.generation}</span> },
    { key: 'sharpe', header: '夏普', render: (g) => <span className={g.validation?.sharpe_ratio ? 'text-emerald-400 font-mono' : 'text-white/40'}>{g.validation?.sharpe_ratio?.toFixed(2) ?? '—'}</span> },
    { key: 'status', header: '状态', render: (g) => <Badge variant={statusVariant(g.validation?.status)}>{g.validation?.status ?? 'pending'}</Badge> },
    { key: 'author', header: '来源', render: (g) => <span className="text-[11px] text-white/40">{g.author || g.meta?.author || '—'}</span> },
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
