'use client';

import Link from 'next/link';
import { useLocale } from 'next-intl';
import Button from '@/components/ui/Button';

export default function QuickActions() {
  const locale = useLocale();
  return (
    <div className="space-y-3">
      <Link href={`/${locale}/bounties?create=1`}>
        <Button variant="primary" className="w-full justify-start">🎯 创建赏金任务</Button>
      </Link>
      <Link href={`/${locale}/genes`}>
        <Button variant="secondary" className="w-full justify-start">🧬 浏览基因库</Button>
      </Link>
      <Link href={`/${locale}/agents`}>
        <Button variant="secondary" className="w-full justify-start">🤖 查看 Agent 排行</Button>
      </Link>
    </div>
  );
}
