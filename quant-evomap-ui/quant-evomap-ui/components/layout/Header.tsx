'use client';

import { useTranslations } from 'next-intl';
import LanguageSwitch from './LanguageSwitch';
import StatsBar from '../visualization/StatsBar';

export default function Header() {
  const t = useTranslations();

  return (
    <header className="fixed top-0 left-0 right-0 h-[70px] bg-bg-dark/95 backdrop-blur-xl border-b border-border flex items-center justify-between px-8 z-50">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-gradient-to-br from-primary to-primary-dark rounded-xl flex items-center justify-center text-lg">
          🧬
        </div>
        <span className="text-xl font-bold bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
          QuantClaw
        </span>
        <div className="flex items-center gap-2 bg-success/10 border border-success/30 px-3 py-1 rounded-full text-xs text-success">
          <div className="w-1.5 h-1.5 bg-success rounded-full animate-pulse" />
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
