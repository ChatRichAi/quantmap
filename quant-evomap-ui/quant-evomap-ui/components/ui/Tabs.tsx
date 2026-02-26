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
    <div className="flex gap-1 border-b border-border">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={clsx(
            'px-4 py-2 text-sm font-medium transition-all border-b-2 -mb-px',
            active === tab.key
              ? 'border-primary text-text-primary'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          )}
        >
          {tab.label}
          {tab.count != null && (
            <span className={clsx(
              'ml-1.5 px-1.5 py-0.5 rounded-full text-xs',
              active === tab.key ? 'bg-primary/20 text-primary' : 'bg-white/10 text-text-secondary'
            )}>{tab.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}
