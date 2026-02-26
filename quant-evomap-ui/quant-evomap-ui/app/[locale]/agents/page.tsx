'use client';

import PageHeader from '@/components/layout/PageHeader';
import Card from '@/components/ui/Card';
import AgentLeaderboard from '@/components/agents/AgentLeaderboard';
import StatCard from '@/components/ui/StatCard';
import { useApiQuery } from '@/lib/hooks';
import { fetchMetrics } from '@/lib/api';

export default function AgentsPage() {
  const { data, loading } = useApiQuery(() => fetchMetrics(), []);
  const agents = data?.trust?.top_agents ?? [];

  return (
    <div className="p-8">
      <PageHeader title="Agent 监控" subtitle="节点声誉排行榜" />
      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatCard label="活跃Agent" value={agents.length} icon="🤖" />
        <StatCard label="最高评分" value={agents[0]?.score?.toFixed(1) ?? '—'} icon="🏆" />
        <StatCard label="总提交数" value={agents.reduce((s, a) => s + a.submissions, 0)} icon="📤" />
      </div>
      <Card title="排行榜">
        <AgentLeaderboard agents={agents} loading={loading} />
      </Card>
    </div>
  );
}
