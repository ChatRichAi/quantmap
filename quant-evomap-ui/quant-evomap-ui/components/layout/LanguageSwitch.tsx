'use client';

import { useLocale, useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';

export default function LanguageSwitch() {
  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();
  const t = useTranslations('language');

  const switchLocale = () => {
    const newLocale = locale === 'en' ? 'zh' : 'en';
    const newPath = pathname.replace(`/${locale}`, `/${newLocale}`);
    router.push(newPath);
  };

  return (
    <button
      onClick={switchLocale}
      className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-bg-card hover:bg-white/5 transition-all text-sm font-medium text-text-secondary hover:text-text-primary"
    >
      <span className="text-base">{locale === 'en' ? '🇨🇳' : '🇺🇸'}</span>
      <span>{t('switch')}</span>
    </button>
  );
}
