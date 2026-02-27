'use client';

import Badge from '@/components/ui/Badge';
import Skeleton from '@/components/ui/Skeleton';
import EmptyState from '@/components/ui/EmptyState';
import type { AgentReputation } from '@/lib/types';

interface AgentLeaderboardProps {
  agents: AgentReputation[];
  loading: boolean;
}

const rankMedal = (i: number) => ['🥇','🥈','🥉'][i] ?? `#${i+1}`;

export default function AgentLeaderboard({ agents, loading }: AgentLeaderboardProps) {
  if (loading) return <div className="space-y-3">{Array.from({length:5}).map((_,i)=><Skeleton key={i} className="h-14 w-full"/>)}</div>;
  if (!agents.length) return <EmptyState icon="🤖" title="暂无Agent数据" />;

  return (
    <div>
      {agents.map((agent, i) => (
        <div key={agent.agent_id} className="flex items-center gap-4 px-4 py-3 border-b border-white/[0.04] hover:bg-white/[0.03] transition-all duration-200">
          <span className="text-xl w-8 text-center">{rankMedal(i)}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-sm text-white">{agent.agent_id}</span>
              <Badge variant="primary">{agent.score.toFixed(1)} 分</Badge>
            </div>
            <div className="flex gap-4 text-[11px] text-white/40">
              <span>提交 {agent.submissions}</span>
              <span>通过 {agent.accepted}</span>
              <span>验证 {agent.validations}</span>
              <span>准确率 {(agent.accuracy * 100).toFixed(1)}%</span>
            </div>
          </div>
          <div className="w-24">
            <div className="relative h-1 rounded-full bg-white/10 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-[#667eea]/20 to-[#764ba2]/20" />
              <div className="relative h-full rounded-full bg-gradient-to-r from-[#667eea] to-[#764ba2] shadow-[0_0_8px_rgba(102,126,234,0.4)]" style={{ width: `${Math.min(100, agent.score)}%` }} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
