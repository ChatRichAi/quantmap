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
          <div className="flex justify-between"><dt className="text-white/50">ID</dt><dd className="font-mono text-[11px] text-white/80">{gene.gene_id}</dd></div>
          <div className="flex justify-between"><dt className="text-white/50">来源</dt><dd className="text-white/80">{gene.source || gene.meta?.source || '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-white/50">创建者</dt><dd className="text-white/80">{gene.author || gene.meta?.author || '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-white/50">世代</dt><dd className="text-white/80">G{gene.generation}</dd></div>
          <div><dt className="text-white/50 mb-1">公式</dt><dd><code className="text-[11px] text-blue-400 bg-blue-500/10 px-2 py-1 rounded-md break-all block font-mono">{gene.formula}</code></dd></div>
          {gene.parameters && Object.keys(gene.parameters).length > 0 && (
            <div><dt className="text-white/50 mb-1">参数</dt><dd><pre className="text-[11px] bg-white/[0.03] border border-white/[0.06] p-3 rounded-lg overflow-auto font-mono text-white/70">{JSON.stringify(gene.parameters, null, 2)}</pre></dd></div>
          )}
        </dl>
      </Card>
      <Card title="验证结果">
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between"><dt className="text-white/50">状态</dt><dd><Badge variant={v?.status === 'validated' ? 'success' : v?.status === 'rejected' ? 'danger' : 'neutral'}>{v?.status ?? 'pending'}</Badge></dd></div>
          <div className="flex justify-between"><dt className="text-white/50">夏普比率</dt><dd className="text-emerald-400 font-medium font-mono">{v?.sharpe_ratio?.toFixed(3) ?? '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-white/50">最大回撤</dt><dd className="text-red-400 font-mono">{v?.max_drawdown != null ? `${(v.max_drawdown * 100).toFixed(1)}%` : '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-white/50">胜率</dt><dd className="text-white/80 font-mono">{v?.win_rate != null ? `${(v.win_rate * 100).toFixed(1)}%` : '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-white/50">测试标的</dt><dd className="text-white/80">{v?.test_symbols?.join(', ') ?? '—'}</dd></div>
          <div className="flex justify-between"><dt className="text-white/50">测试区间</dt><dd className="text-white/80 text-xs">{v?.test_period ?? '—'}</dd></div>
        </dl>
      </Card>
      {gene.lineage && (
        <Card title="谱系信息" className="col-span-2">
          <div className="flex gap-6 text-sm">
            <div><span className="text-white/50">变异类型: </span><span className="text-white/80">{gene.lineage.mutation_type}</span></div>
            <div><span className="text-white/50">父基因: </span><span className="font-mono text-[11px] text-blue-400">{gene.lineage.parent_ids?.join(', ') || '—'}</span></div>
          </div>
        </Card>
      )}
    </div>
  );
}
