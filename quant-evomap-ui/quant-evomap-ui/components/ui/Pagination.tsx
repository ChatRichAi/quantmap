import Button from './Button';

interface PaginationProps {
  currentPage: number;
  hasNext: boolean;
  onNext: () => void;
  onPrev: () => void;
}

export default function Pagination({ currentPage, hasNext, onNext, onPrev }: PaginationProps) {
  return (
    <div className="flex items-center justify-between px-2 py-3 border-t border-white/[0.06]">
      <Button size="sm" onClick={onPrev} disabled={currentPage <= 1}>← 上一页</Button>
      <span className="text-xs text-white/40 font-mono">第 {currentPage} 页</span>
      <Button size="sm" onClick={onNext} disabled={!hasNext}>下一页 →</Button>
    </div>
  );
}
