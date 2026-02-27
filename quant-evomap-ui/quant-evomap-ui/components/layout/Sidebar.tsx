'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale, useTranslations } from 'next-intl';
import { clsx } from 'clsx';

const navItems = [
  { icon: '📊', key: 'dashboard', href: '/dashboard' },
  { icon: '🧬', key: 'genes', href: '/genes' },
  { icon: '🎯', key: 'bounties', href: '/bounties' },
  { icon: '🤖', key: 'agents', href: '/agents' },
  { icon: '🌐', key: 'evomap', href: '/evomap' },
  { icon: '🏪', key: 'marketplace', href: '/marketplace' },
];

const bottomNavItems = [
  { icon: '🚀', key: 'onboarding', href: '/onboarding' },
  { icon: '💻', key: 'cliGuide', href: '/cli-guide' },
  { icon: '💎', key: 'pricing', href: '/pricing' },
];

export default function Sidebar() {
  const t = useTranslations('nav');
  const locale = useLocale();
  const pathname = usePathname();

  const isActive = (href: string) => {
    const current = pathname.replace(`/${locale}`, '') || '/';
    return current === href || current.startsWith(href + '/');
  };

  return (
    <aside className="fixed left-0 top-[70px] bottom-0 w-[220px] bg-bg-root border-r border-white/[0.06] flex flex-col z-40">
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.key}
            href={`/${locale}${item.href}`}
            className={clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
              isActive(item.href)
                ? 'bg-[rgba(102,126,234,0.15)] text-white border border-[#667eea]/30 shadow-glow-xs'
                : 'text-white/60 hover:bg-white/[0.05] hover:text-white border border-transparent'
            )}
          >
            <span className="text-base">{item.icon}</span>
            <span>{t(item.key as any)}</span>
          </Link>
        ))}
      </nav>
      <div className="p-3 space-y-1">
        <div className="h-px divider-gradient mb-3" />
        {bottomNavItems.map((item) => (
          <Link
            key={item.key}
            href={`/${locale}${item.href}`}
            className={clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
              isActive(item.href)
                ? 'bg-[rgba(102,126,234,0.15)] text-white border border-[#667eea]/30 shadow-glow-xs'
                : 'text-white/60 hover:bg-white/[0.05] hover:text-white border border-transparent'
            )}
          >
            <span className="text-base">{item.icon}</span>
            <span>{t(item.key as any)}</span>
          </Link>
        ))}
        <div className="text-[10px] text-white/30 text-center pt-3 font-mono tracking-wider">
          QuantClaw QGEP v1.0
        </div>
      </div>
    </aside>
  );
}
