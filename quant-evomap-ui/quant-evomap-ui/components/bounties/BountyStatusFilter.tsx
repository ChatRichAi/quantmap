'use client';

import Tabs from '@/components/ui/Tabs';
import type { BountyStatus } from '@/lib/types';

interface BountyStatusFilterProps {
  active: string;
  onChange: (v: string) => void;
  counts?: Record<string, number>;
}

const tabs = [
  { key: '', label: '全部' },
  { key: 'pending', label: '待认领' },
  { key: 'claimed', label: '已认领' },
  { key: 'completed', label: '已完成' },
  { key: 'failed', label: '失败' },
  { key: 'expired', label: '已过期' },
];

export default function BountyStatusFilter({ active, onChange, counts }: BountyStatusFilterProps) {
  const tabsWithCount = tabs.map((t) => ({
    ...t,
    count: counts?.[t.key],
  }));
  return <Tabs tabs={tabsWithCount} active={active} onChange={onChange} />;
}
