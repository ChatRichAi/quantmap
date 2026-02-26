'use client';

import SearchInput from '@/components/ui/SearchInput';

interface GeneFilterBarProps {
  search: string;
  onSearch: (v: string) => void;
  status: string;
  onStatus: (v: string) => void;
}

const statuses = [
  { value: '', label: '全部' },
  { value: 'validated', label: '已验证' },
  { value: 'pending', label: '待验证' },
  { value: 'rejected', label: '已拒绝' },
];

export default function GeneFilterBar({ search, onSearch, status, onStatus }: GeneFilterBarProps) {
  return (
    <div className="flex items-center gap-4 mb-6">
      <div className="flex-1 max-w-sm">
        <SearchInput value={search} onChange={onSearch} placeholder="搜索基因名称..." />
      </div>
      <div className="flex gap-1">
        {statuses.map((s) => (
          <button
            key={s.value}
            onClick={() => onStatus(s.value)}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-all ${
              status === s.value
                ? 'bg-primary/20 border-primary/40 text-text-primary'
                : 'bg-white/5 border-border text-text-secondary hover:text-text-primary'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
