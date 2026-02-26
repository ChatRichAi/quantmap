import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
  action?: React.ReactNode;
}

export default function Card({ children, title, className, action }: CardProps) {
  return (
    <div className={clsx('bg-bg-card border border-border rounded-xl p-6', className)}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4">
          {title && <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">{title}</h3>}
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
}
