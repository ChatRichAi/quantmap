'use client';

import { useTranslations } from 'next-intl';
import LanguageSwitch from './LanguageSwitch';
import StatsBar from '../visualization/StatsBar';

export default function Header() {
  const t = useTranslations();

  return (
    <header className="fixed top-0 left-0 right-0 h-[70px] glass border-b border-white/[0.06] flex items-center justify-between px-8 z-50">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-brand-gradient rounded-xl flex items-center justify-center text-lg shadow-glow">
          🧬
        </div>
        <span className="text-xl font-bold gradient-text-brand">
          QuantClaw
        </span>
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full text-[10px] font-medium text-emerald-400">
          <div className="relative w-1.5 h-1.5">
            <span className="absolute inset-0 rounded-full bg-emerald-400 animate-ping opacity-75" />
            <span className="relative block w-1.5 h-1.5 rounded-full bg-emerald-400" />
          </div>
          <span>{t('common.evolutionLive')}</span>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <StatsBar />
        <LanguageSwitch />
      </div>
    </header>
  );
}
