import { clsx } from 'clsx';

interface Tab {
  key: string;
  label: string;
  count?: number;
}

interface TabsProps {
  tabs: Tab[];
  active: string;
  onChange: (key: string) => void;
}

export default function Tabs({ tabs, active, onChange }: TabsProps) {
  return (
    <div className="flex gap-1 border-b border-white/[0.06]">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={clsx(
            'px-4 py-2.5 text-sm font-medium transition-all duration-200 border-b-2 -mb-px',
            active === tab.key
              ? 'border-[#667eea] text-white'
              : 'border-transparent text-white/50 hover:text-white/80'
          )}
        >
          {tab.label}
          {tab.count != null && (
            <span className={clsx(
              'ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] font-mono',
              active === tab.key ? 'bg-[rgba(102,126,234,0.15)] text-[#667eea]' : 'bg-white/[0.05] text-white/40'
            )}>{tab.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}
