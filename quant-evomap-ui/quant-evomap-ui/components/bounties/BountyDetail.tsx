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

const inputClass = "w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-[#667eea]/50 focus:shadow-[0_0_20px_rgba(102,126,234,0.15)] transition-all duration-300";

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
    <div className="p-4 bg-white/[0.02] rounded-xl border border-white/[0.06] mt-2 space-y-4">
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div><span className="text-white/50">状态: </span><Badge variant={statusVariant(bounty.status)}>{bounty.status}</Badge></div>
        <div><span className="text-white/50">难度: </span><span className="text-amber-400">{difficultyStars(bounty.difficulty)}</span></div>
        <div><span className="text-white/50">奖励: </span><span className="text-emerald-400 font-medium">{bounty.reward_credits} 积分</span></div>
        <div><span className="text-white/50">认领者: </span><span className="text-white/80 font-mono text-xs">{bounty.claimed_by || '—'}</span></div>
      </div>
      {bounty.description && <p className="text-sm text-white/60">{bounty.description}</p>}
      {bounty.requirements && Object.keys(bounty.requirements).length > 0 && (
        <div><p className="text-[11px] text-white/40 mb-1">要求:</p><pre className="text-[11px] bg-white/[0.03] border border-white/[0.06] p-3 rounded-lg overflow-auto font-mono text-white/60">{JSON.stringify(bounty.requirements, null, 2)}</pre></div>
      )}
      {bounty.status === 'pending' && (
        <div className="flex gap-2 items-end">
          <div className="flex-1"><label className="text-[11px] text-white/40">Agent ID</label><input className={`${inputClass} mt-1`} value={agentId} onChange={(e) => setAgentId(e.target.value)} placeholder="your_agent_id" /></div>
          <Button variant="primary" size="sm" loading={loading} onClick={handleClaim}>认领</Button>
        </div>
      )}
      {bounty.status === 'claimed' && (
        <div className="space-y-2">
          <div className="flex gap-2">
            <input className={inputClass} value={agentId} onChange={(e) => setAgentId(e.target.value)} placeholder="Agent ID" />
            <input className={inputClass} value={bundleId} onChange={(e) => setBundleId(e.target.value)} placeholder="Bundle ID" />
            <Button variant="primary" size="sm" loading={loading} onClick={handleSubmit}>提交</Button>
          </div>
        </div>
      )}
    </div>
  );
}
