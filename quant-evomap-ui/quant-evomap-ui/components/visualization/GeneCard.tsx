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
      className={`rounded-xl p-3.5 cursor-pointer transition-all duration-200 border ${
        passed
          ? 'bg-emerald-500/10 border-emerald-500/20 hover:bg-emerald-500/15 hover:border-emerald-500/30 hover:shadow-glow-green'
          : 'bg-[rgba(102,126,234,0.08)] border-[#667eea]/15 hover:bg-[rgba(102,126,234,0.12)] hover:border-[#667eea]/30 hover:shadow-glow-xs'
      } hover:translate-x-1`}
    >
      <div className="text-[13px] font-semibold text-white mb-1.5 truncate">
        {name}
      </div>
      <div className="text-[11px] text-white/40 font-mono truncate">
        {formula}
      </div>
      <div className="flex items-center gap-2 mt-2">
        <span
          className={`text-[10px] px-2 py-0.5 rounded-md font-semibold font-mono ${
            score > 1.0
              ? 'bg-emerald-500/15 text-emerald-400'
              : 'bg-red-500/15 text-red-400'
          }`}
        >
          Sharpe: {formatNumber(score)}
        </span>
        <span className="text-[10px] text-white/30 font-mono">
          {t('gen')} {generation}
        </span>
      </div>
    </div>
  );
}
