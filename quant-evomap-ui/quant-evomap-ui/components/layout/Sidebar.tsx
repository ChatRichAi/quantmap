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

export default function Sidebar() {
  const t = useTranslations('nav');
  const locale = useLocale();
  const pathname = usePathname();

  const isActive = (href: string) => {
    const current = pathname.replace(`/${locale}`, '') || '/';
    return current === href || current.startsWith(href + '/');
  };

  return (
    <aside className="fixed left-0 top-[70px] bottom-0 w-[220px] bg-bg-card border-r border-border flex flex-col z-40">
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.key}
            href={`/${locale}${item.href}`}
            className={clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
              isActive(item.href)
                ? 'bg-primary/20 text-text-primary border border-primary/30'
                : 'text-text-secondary hover:bg-white/5 hover:text-text-primary border border-transparent'
            )}
          >
            <span className="text-base">{item.icon}</span>
            <span>{t(item.key as any)}</span>
          </Link>
        ))}
      </nav>
      <div className="p-4 border-t border-border">
        <div className="text-xs text-text-secondary text-center">QuantClaw QGEP v1.0</div>
      </div>
    </aside>
  );
}
