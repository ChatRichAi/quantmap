'use client';

import { useTranslations } from 'next-intl';

const legendItems = [
  { color: '#10b981', key: 'passed' },
  { color: '#667eea', key: 'survived' },
  { color: '#ef4444', key: 'eliminated' },
  { color: '#f59e0b', key: 'newOffspring' },
];

export default function Legend() {
  const t = useTranslations('legend');

  return (
    <div className="absolute bottom-6 left-6 glass rounded-xl p-4 border border-white/[0.08]">
      <div className="text-[10px] font-semibold text-white/40 uppercase tracking-wider mb-3">
        {t('title')}
      </div>
      {legendItems.map((item) => (
        <div key={item.key} className="flex items-center gap-2.5 my-2 text-xs text-white/70">
          <div
            className="w-3 h-3 rounded-full"
            style={{
              backgroundColor: item.color,
              boxShadow: `0 0 6px ${item.color}60`,
            }}
          />
          <span>{t(item.key as any)}</span>
        </div>
      ))}
    </div>
  );
}
