import Skeleton from './Skeleton';
import EmptyState from './EmptyState';
import { clsx } from 'clsx';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  className?: string;
}

interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
  rowKey: (item: T) => string;
}

export default function Table<T>({ columns, data, loading, emptyMessage = '暂无数据', onRowClick, rowKey }: TableProps<T>) {
  if (loading) {
    return (
      <div className="p-4 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
      </div>
    );
  }

  if (!data.length) {
    return <EmptyState title={emptyMessage} />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border">
            {columns.map((col) => (
              <th key={col.key} className={clsx('px-4 py-3 text-left text-xs font-semibold text-text-secondary uppercase tracking-wider', col.className)}>
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr
              key={rowKey(item)}
              onClick={() => onRowClick?.(item)}
              className={clsx(
                'border-b border-border/50 transition-colors',
                onRowClick ? 'cursor-pointer hover:bg-white/5' : ''
              )}
            >
              {columns.map((col) => (
                <td key={col.key} className={clsx('px-4 py-3 text-text-primary', col.className)}>
                  {col.render ? col.render(item) : String((item as Record<string, unknown>)[col.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
