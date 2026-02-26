'use client';

import { useApiQuery } from '@/lib/hooks';
import { fetchEvolverStatus } from '@/lib/api';
import StatusDot from '@/components/ui/StatusDot';
import Skeleton from '@/components/ui/Skeleton';

export default function SystemHealth() {
  const { data, loading } = useApiQuery(() => fetchEvolverStatus(), []);

  if (loading) return <Skeleton lines={3} className="h-6 w-full" />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-text-secondary">进化守护进程</span>
        <StatusDot status={data?.running ? 'running' : 'stopped'} label={data?.running ? '运行中' : '已停止'} />
      </div>
      {data?.pid && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-text-secondary">进程ID</span>
          <span className="text-sm font-mono text-text-primary">{data.pid}</span>
        </div>
      )}
      <div className="flex items-center justify-between">
        <span className="text-sm text-text-secondary">API 服务</span>
        <StatusDot status="running" label=":8889" />
      </div>
    </div>
  );
}
