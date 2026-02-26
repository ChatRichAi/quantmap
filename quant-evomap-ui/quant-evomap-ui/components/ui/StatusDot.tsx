import { clsx } from 'clsx';

interface StatusDotProps {
  status: 'running' | 'stopped' | 'warning' | 'pending';
  label?: string;
}

const dotColors = {
  running: 'bg-success',
  stopped: 'bg-danger',
  warning: 'bg-warning',
  pending: 'bg-text-secondary',
};

export default function StatusDot({ status, label }: StatusDotProps) {
  return (
    <div className="flex items-center gap-2">
      <div className={clsx(
        'w-2 h-2 rounded-full',
        dotColors[status],
        status === 'running' && 'animate-pulse'
      )} />
      {label && <span className="text-sm text-text-secondary">{label}</span>}
    </div>
  );
}
