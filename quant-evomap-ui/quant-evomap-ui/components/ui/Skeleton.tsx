import { clsx } from 'clsx';

interface SkeletonProps {
  className?: string;
  lines?: number;
}

export default function Skeleton({ className, lines = 1 }: SkeletonProps) {
  return (
    <>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={clsx(
            'rounded-lg animate-pulse bg-white/[0.06]',
            i < lines - 1 ? 'mb-2' : '',
            className ?? 'h-4 w-full'
          )}
        />
      ))}
    </>
  );
}
