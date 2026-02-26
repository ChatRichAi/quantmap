'use client';

import { useState } from 'react';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import { claimBounty, submitBountyResult } from '@/lib/api';
import type { BountyTask } from '@/lib/types';

interface BountyDetailProps {
  bounty: BountyTask;
  onRefresh: () => void;
}

const difficultyStars = (d: number) => '★'.repeat(d) + '☆'.repeat(5 - d);

const statusVariant = (s: string) => {
  if (s === 'completed') return 'success';
  if (s === 'failed' || s === 'expired') return 'danger';
  if (s === 'claimed') return 'warning';
  return 'neutral';
};

export default function BountyDetail({ bounty, onRefresh }: BountyDetailProps) {
  const [agentId, setAgentId] = useState('');
  const [bundleId, setBundleId] = useState('');
  const [loading, setLoading] = useState(false);

  const handleClaim = async () => {
    if (!agentId) return alert('请输入 Agent ID');
    setLoading(true);
    try { await claimBounty(bounty.task_id, agentId); onRefresh(); } 
    catch (e) { alert((e instanceof Error ? e.message : '认领失败')); }
    finally { setLoading(false); }
  };

  const handleSubmit = async () => {
    if (!agentId || !bundleId) return alert('请输入 Agent ID 和 Bundle ID');
    setLoading(true);
    try { await submitBountyResult(bounty.task_id, agentId, bundleId); onRefresh(); }
    catch (e) { alert((e instanceof Error ? e.message : '提交失败')); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-4 bg-bg-dark rounded-lg border border-border mt-2 space-y-4">
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div><span className="text-text-secondary">状态: </span><Badge variant={statusVariant(bounty.status)}>{bounty.status}</Badge></div>
        <div><span className="text-text-secondary">难度: </span><span className="text-warning">{difficultyStars(bounty.difficulty)}</span></div>
        <div><span className="text-text-secondary">奖励: </span><span className="text-success font-medium">{bounty.reward_credits} 积分</span></div>
        <div><span className="text-text-secondary">认领者: </span><span className="text-text-primary font-mono text-xs">{bounty.claimed_by || '—'}</span></div>
      </div>
      {bounty.description && <p className="text-sm text-text-secondary">{bounty.description}</p>}
      {bounty.requirements && Object.keys(bounty.requirements).length > 0 && (
        <div><p className="text-xs text-text-secondary mb-1">要求:</p><pre className="text-xs bg-bg-card p-2 rounded overflow-auto">{JSON.stringify(bounty.requirements, null, 2)}</pre></div>
      )}
      {bounty.status === 'pending' && (
        <div className="flex gap-2 items-end">
          <div className="flex-1"><label className="text-xs text-text-secondary">Agent ID</label><input className="w-full mt-1 bg-bg-card border border-border rounded px-2 py-1.5 text-sm text-text-primary focus:outline-none focus:border-primary" value={agentId} onChange={(e) => setAgentId(e.target.value)} placeholder="your_agent_id" /></div>
          <Button variant="primary" size="sm" loading={loading} onClick={handleClaim}>认领</Button>
        </div>
      )}
      {bounty.status === 'claimed' && (
        <div className="space-y-2">
          <div className="flex gap-2">
            <input className="flex-1 bg-bg-card border border-border rounded px-2 py-1.5 text-sm text-text-primary focus:outline-none focus:border-primary" value={agentId} onChange={(e) => setAgentId(e.target.value)} placeholder="Agent ID" />
            <input className="flex-1 bg-bg-card border border-border rounded px-2 py-1.5 text-sm text-text-primary focus:outline-none focus:border-primary" value={bundleId} onChange={(e) => setBundleId(e.target.value)} placeholder="Bundle ID" />
            <Button variant="primary" size="sm" loading={loading} onClick={handleSubmit}>提交</Button>
          </div>
        </div>
      )}
    </div>
  );
}
