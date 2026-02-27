'use client';

import { useApiQuery } from '@/lib/hooks';
import { fetchEvents } from '@/lib/api';
import Skeleton from '@/components/ui/Skeleton';
import EmptyState from '@/components/ui/EmptyState';

const eventIcons: Record<string, string> = {
  created: '🧬',
  mutated: '🔄',
  tested: '🧪',
  deployed: '🚀',
  daemon_cycle: '⚙️',
};

export default function RecentActivity() {
  const { data, loading } = useApiQuery(() => fetchEvents(10), []);

  if (loading) return <div className="space-y-3"><Skeleton lines={5} className="h-12 w-full" /></div>;
  if (!data?.items?.length) return <EmptyState icon="📭" title="暂无进化事件" />;

  return (
    <div className="space-y-2">
      {data.items.map((ev) => (
        <div key={ev.event_id} className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-transparent hover:border-white/[0.06] transition-all duration-200">
          <span className="text-lg mt-0.5">{eventIcons[ev.event_type] ?? '📌'}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-white truncate">{ev.event_type}</span>
              <span className="text-[11px] text-white/40 font-mono whitespace-nowrap">GDI: {ev.gdi_score?.toFixed(1)}</span>
            </div>
            <p className="text-[11px] text-white/40 truncate font-mono">gene: {ev.gene_id}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
