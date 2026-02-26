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
        <div key={agent.agent_id} className="flex items-center gap-4 px-4 py-3 border-b border-border/50 hover:bg-white/5 transition-colors">
          <span className="text-xl w-8 text-center">{rankMedal(i)}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-sm text-text-primary">{agent.agent_id}</span>
              <Badge variant="primary">{agent.score.toFixed(1)} 分</Badge>
            </div>
            <div className="flex gap-4 text-xs text-text-secondary">
              <span>提交 {agent.submissions}</span>
              <span>通过 {agent.accepted}</span>
              <span>验证 {agent.validations}</span>
              <span>准确率 {(agent.accuracy * 100).toFixed(1)}%</span>
            </div>
          </div>
          <div className="w-24">
            <div className="h-1.5 bg-border rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full" style={{ width: `${Math.min(100, agent.score)}%` }} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
