import { clsx } from 'clsx';

interface StatusDotProps {
  status: 'running' | 'stopped' | 'warning' | 'pending';
  label?: string;
}

const dotColors = {
  running: 'bg-emerald-400',
  stopped: 'bg-red-400',
  warning: 'bg-amber-400',
  pending: 'bg-white/40',
};

export default function StatusDot({ status, label }: StatusDotProps) {
  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        {status === 'running' && (
          <span className={clsx('absolute inset-0 rounded-full animate-ping opacity-75', dotColors[status])} />
        )}
        <span className={clsx(
          'relative block w-2 h-2 rounded-full',
          dotColors[status],
          status === 'running' && 'shadow-[0_0_6px_rgba(52,211,153,0.6)]'
        )} />
      </div>
      {label && <span className="text-sm text-white/60">{label}</span>}
    </div>
  );
}
