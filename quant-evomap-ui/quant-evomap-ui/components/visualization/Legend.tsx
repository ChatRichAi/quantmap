'use client';

import { useTranslations } from 'next-intl';

const legendItems = [
  { color: '#10b981', key: 'passed' },
  { color: '#6366f1', key: 'survived' },
  { color: '#ef4444', key: 'eliminated' },
  { color: '#f59e0b', key: 'newOffspring' },
];

export default function Legend() {
  const t = useTranslations('legend');

  return (
    <div className="absolute bottom-6 left-6 bg-bg-card/90 backdrop-blur-xl border border-border rounded-xl p-4">
      <div className="text-[11px] font-semibold text-text-secondary uppercase tracking-wide mb-3">
        {t('title')}
      </div>
      {legendItems.map((item) => (
        <div key={item.key} className="flex items-center gap-2.5 my-2 text-xs text-text-primary">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: item.color }}
          />
          <span>{t(item.key as any)}</span>
        </div>
      ))}
    </div>
  );
}
