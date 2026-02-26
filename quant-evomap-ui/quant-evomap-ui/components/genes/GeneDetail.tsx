'use client';

import Badge from '@/components/ui/Badge';
import Card from '@/components/ui/Card';
import type { Gene } from '@/lib/types';

interface GeneDetailProps {
  gene: Gene;
}

export default function GeneDetail({ gene }: GeneDetailProps) {
  const v = gene.validation;
  return (
    <div className="grid grid-cols-2 gap-6">
      <Card title="基本信息">
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between"><dt className="text-text-secondary">ID</dt><dd className="font-mono text-xs text-text-primary">{gene.gene_id}</dd></div>
          <div className="flex justify-between"><dt className="text-text-secondary">来源</dt><dd className="text-text-primary">{gene.source || gene.meta?.source || '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-text-secondary">创建者</dt><dd className="text-text-primary">{gene.author || gene.meta?.author || '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-text-secondary">世代</dt><dd className="text-text-primary">G{gene.generation}</dd></div>
          <div><dt className="text-text-secondary mb-1">公式</dt><dd><code className="text-xs text-info bg-info/10 px-2 py-1 rounded break-all block">{gene.formula}</code></dd></div>
          {gene.parameters && Object.keys(gene.parameters).length > 0 && (
            <div><dt className="text-text-secondary mb-1">参数</dt><dd><pre className="text-xs bg-bg-dark p-2 rounded overflow-auto">{JSON.stringify(gene.parameters, null, 2)}</pre></dd></div>
          )}
        </dl>
      </Card>
      <Card title="验证结果">
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between"><dt className="text-text-secondary">状态</dt><dd><Badge variant={v?.status === 'validated' ? 'success' : v?.status === 'rejected' ? 'danger' : 'neutral'}>{v?.status ?? 'pending'}</Badge></dd></div>
          <div className="flex justify-between"><dt className="text-text-secondary">夏普比率</dt><dd className="text-success font-medium">{v?.sharpe_ratio?.toFixed(3) ?? '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-text-secondary">最大回撤</dt><dd className="text-danger">{v?.max_drawdown != null ? `${(v.max_drawdown * 100).toFixed(1)}%` : '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-text-secondary">胜率</dt><dd className="text-text-primary">{v?.win_rate != null ? `${(v.win_rate * 100).toFixed(1)}%` : '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-text-secondary">测试标的</dt><dd className="text-text-primary">{v?.test_symbols?.join(', ') ?? '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-text-secondary">测试区间</dt><dd className="text-text-primary text-xs">{v?.test_period ?? '—'}</dd></div>
        </dl>
      </Card>
      {gene.lineage && (
        <Card title="谱系信息" className="col-span-2">
          <div className="flex gap-6 text-sm">
            <div><span className="text-text-secondary">变异类型: </span><span className="text-text-primary">{gene.lineage.mutation_type}</span></div>
            <div><span className="text-text-secondary">父基因: </span><span className="font-mono text-xs text-info">{gene.lineage.parent_ids?.join(', ') || '—'}</span></div>
          </div>
        </Card>
      )}
    </div>
  );
}
