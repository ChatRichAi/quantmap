'use client';

import { useTranslations } from 'next-intl';
import { formatNumber } from '@/lib/utils';

interface GeneCardProps {
  name: string;
  formula: string;
  score: number;
  generation: number;
  passed: boolean;
  onClick?: () => void;
}

export default function GeneCard({
  name,
  formula,
  score,
  generation,
  passed,
  onClick,
}: GeneCardProps) {
  const t = useTranslations('evomap');

  return (
    <div
      onClick={onClick}
      className={`rounded-xl p-3.5 cursor-pointer transition-all border ${
        passed
          ? 'bg-success/10 border-success/30 hover:bg-success/15 hover:border-success/50'
          : 'bg-primary/10 border-primary/20 hover:bg-primary/15 hover:border-primary/40'
      } hover:translate-x-1`}
    >
      <div className="text-[13px] font-semibold text-text-primary mb-1.5 truncate">
        {name}
      </div>
      <div className="text-[11px] text-text-secondary font-mono truncate">
        {formula}
      </div>
      <div className="flex items-center gap-2 mt-2">
        <span
          className={`text-[11px] px-2 py-0.5 rounded font-semibold ${
            score > 1.0
              ? 'bg-success/20 text-success'
              : 'bg-danger/20 text-danger'
          }`}
        >
          Sharpe: {formatNumber(score)}
        </span>
        <span className="text-[11px] text-text-secondary">
          {t('gen')} {generation}
        </span>
      </div>
    </div>
  );
}
