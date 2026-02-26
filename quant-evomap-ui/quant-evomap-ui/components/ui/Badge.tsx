import { clsx } from 'clsx';

type BadgeVariant = 'success' | 'danger' | 'warning' | 'info' | 'neutral' | 'primary';

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  success: 'bg-success/20 text-success border-success/30',
  danger: 'bg-danger/20 text-danger border-danger/30',
  warning: 'bg-warning/20 text-warning border-warning/30',
  info: 'bg-info/20 text-info border-info/30',
  neutral: 'bg-white/10 text-text-secondary border-border',
  primary: 'bg-primary/20 text-primary border-primary/30',
};

export default function Badge({ variant = 'neutral', children, className }: BadgeProps) {
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
      variantStyles[variant],
      className
    )}>
      {children}
    </span>
  );
}
