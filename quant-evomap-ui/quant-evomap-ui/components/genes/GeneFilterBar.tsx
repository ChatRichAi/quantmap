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
            className={`px-3 py-1.5 text-xs rounded-lg border transition-all duration-200 ${
              status === s.value
                ? 'bg-[rgba(102,126,234,0.15)] border-[#667eea]/30 text-white shadow-glow-xs'
                : 'bg-white/[0.03] border-white/[0.08] text-white/50 hover:text-white hover:bg-white/[0.06]'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}
