import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  className?: string;
  action?: React.ReactNode;
}

export default function Card({ children, title, className, action }: CardProps) {
  return (
    <div className={clsx(
      'rounded-xl border border-white/[0.06] bg-white/[0.03] overflow-hidden',
      className
    )}>
      {(title || action) && (
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.06]">
          {title && (
            <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider">{title}</h3>
          )}
          {action && <div>{action}</div>}
        </div>
      )}
      <div className="p-5">
        {children}
      </div>
    </div>
  );
}
