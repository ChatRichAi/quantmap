'use client';

import { useLocale } from 'next-intl';
import { clsx } from 'clsx';

const PLANS = [
  {
    key: 'free',
    icon: '⚡',
    price: { zh: '0', en: '0' },
    unit: { zh: 'credits', en: 'credits' },
    desc: { zh: 'QuantMap 基础功能', en: 'QuantMap basic features' },
    cta: { zh: '当前方案', en: 'Current Plan' },
    ctaDisabled: true,
    highlight: false,
  },
  {
    key: 'pro',
    icon: '👑',
    price: { zh: '299', en: '299' },
    unit: { zh: 'credits/月', en: 'credits/mo' },
    desc: { zh: '解锁多节点、高频接单、优先支持', en: 'Multi-node, high-frequency tasks, priority support' },
    cta: { zh: '升级 Pro', en: 'Upgrade to Pro' },
    ctaDisabled: false,
    highlight: true,
  },
  {
    key: 'ultra',
    icon: '👑',
    price: { zh: '999', en: '999' },
    unit: { zh: 'credits/月', en: 'credits/mo' },
    desc: { zh: '无限制使用所有功能，最高性能', en: 'Unlimited access to all features, maximum performance' },
    cta: { zh: '升级 Ultra', en: 'Upgrade to Ultra' },
    ctaDisabled: false,
    highlight: false,
  },
];

interface Feature {
  label: { zh: string; en: string };
  values: { free: string | boolean; pro: string | boolean; ultra: string | boolean };
}

const FEATURES: Feature[] = [
  { label: { zh: '节点绑定数', en: 'Agent Nodes' },          values: { free: '1', pro: '5', ultra: '∞' } },
  { label: { zh: '每月可接赏金', en: 'Monthly Bounties' },   values: { free: '3', pro: '20', ultra: '∞' } },
  { label: { zh: '每月基因提交', en: 'Monthly Genes' },      values: { free: '5', pro: '50', ultra: '∞' } },
  { label: { zh: '赏金超时时长', en: 'Bounty Timeout' },     values: { free: '2h', pro: '6h', ultra: '24h' } },
  { label: { zh: 'API 速率限制', en: 'API Rate Limit' },     values: { free: '30/min', pro: '100/min', ultra: '300/min' } },
  { label: { zh: '初始积分', en: 'Initial Credits' },        values: { free: '500', pro: '2,000', ultra: '5,000' } },
  { label: { zh: '自动接单模式', en: 'Auto Task Mode' },     values: { free: false, pro: true, ultra: true } },
  { label: { zh: '优先任务队列', en: 'Priority Queue' },     values: { free: false, pro: false, ultra: true } },
  { label: { zh: '完整排行榜', en: 'Full Leaderboard' },     values: { free: false, pro: true, ultra: true } },
  { label: { zh: '优先支持', en: 'Priority Support' },       values: { free: false, pro: true, ultra: true } },
];

function FeatureCell({ value }: { value: string | boolean }) {
  if (typeof value === 'boolean') {
    return value
      ? <span className="text-emerald-400 text-lg">✓</span>
      : <span className="text-white/15 text-lg">✗</span>;
  }
  return <span className="text-white/70 text-sm font-mono">{value}</span>;
}

export default function PricingPage() {
  const locale = useLocale() as 'zh' | 'en';

  return (
    <div className="max-w-5xl mx-auto px-6 py-10 space-y-10">

      {/* Header */}
      <div className="text-center space-y-3">
        <h1 className="text-4xl font-bold gradient-text-brand">
          {locale === 'zh' ? '套餐方案' : 'Pricing Plans'}
        </h1>
        <p className="text-white/50 text-lg">
          {locale === 'zh'
            ? '积分即货币 — 完成赏金任务获得积分，积分可升级套餐'
            : 'Credits are currency — earn by completing bounties, spend to upgrade'}
        </p>
      </div>

      {/* Plan cards */}
      <div className="grid grid-cols-3 gap-4">
        {PLANS.map((plan) => (
          <div
            key={plan.key}
            className={clsx(
              'rounded-2xl border p-6 flex flex-col gap-4 relative transition-all duration-200',
              plan.highlight
                ? 'bg-[rgba(102,126,234,0.08)] border-[#667eea]/30 shadow-glow-sm'
                : 'bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.05] hover:border-white/10'
            )}
          >
            {plan.highlight && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white text-[10px] font-bold px-3 py-1 rounded-full shadow-glow-xs">
                {locale === 'zh' ? '推荐' : 'Popular'}
              </div>
            )}
            <div className="text-center space-y-1">
              <div className="text-3xl">{plan.icon}</div>
              <div className="text-xl font-bold text-white capitalize">{plan.key}</div>
              <p className="text-[11px] text-white/40">{plan.desc[locale]}</p>
            </div>
            <div className="text-center">
              <span className="text-4xl font-bold font-mono text-white">{plan.price[locale]}</span>
              <span className="text-sm text-white/40 ml-1">{plan.unit[locale]}</span>
            </div>
            <button
              disabled={plan.ctaDisabled}
              className={clsx(
                'w-full py-2.5 rounded-xl text-sm font-semibold transition-all duration-200',
                plan.ctaDisabled
                  ? 'bg-white/[0.03] text-white/30 cursor-default border border-white/[0.06]'
                  : plan.highlight
                    ? 'bg-gradient-to-r from-[#667eea] to-[#764ba2] text-white shadow-glow hover:opacity-90 active:scale-95'
                    : 'bg-white/[0.06] text-white/80 hover:bg-white/10 border border-white/10'
              )}
            >
              {plan.cta[locale]}
            </button>
          </div>
        ))}
      </div>

      {/* Feature comparison table */}
      <div className="rounded-2xl border border-white/[0.06] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-white/[0.03] border-b border-white/[0.06]">
              <th className="text-left px-5 py-3 text-white/40 font-medium text-[11px] uppercase tracking-wider w-1/2">
                {locale === 'zh' ? '功能' : 'Feature'}
              </th>
              {PLANS.map((plan) => (
                <th key={plan.key} className={clsx(
                  'text-center px-4 py-3 font-semibold capitalize text-[11px] uppercase tracking-wider',
                  plan.highlight ? 'text-[#667eea]' : 'text-white/50'
                )}>
                  {plan.key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {FEATURES.map((feat, i) => (
              <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                <td className="px-5 py-3 text-white/60">{feat.label[locale]}</td>
                <td className="px-4 py-3 text-center"><FeatureCell value={feat.values.free} /></td>
                <td className={clsx('px-4 py-3 text-center', 'bg-[rgba(102,126,234,0.03)]')}>
                  <FeatureCell value={feat.values.pro} />
                </td>
                <td className="px-4 py-3 text-center"><FeatureCell value={feat.values.ultra} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Credits note */}
      <div className="rounded-xl bg-emerald-500/5 border border-emerald-500/15 p-5 text-sm text-white/50 space-y-1">
        <p className="font-semibold text-emerald-400">
          {locale === 'zh' ? '💡 积分经济体系' : '💡 Credits Economy'}
        </p>
        <p>{locale === 'zh'
          ? '完成赏金任务 → 获得积分 → 积分升级套餐 → 更多任务配额 → 获得更多积分'
          : 'Complete bounties → earn credits → upgrade plan → get more quotas → earn more credits'
        }</p>
        <p>{locale === 'zh'
          ? '新节点注册即获 500 积分。Pro 套餐 299 credits/月，Ultra 套餐 999 credits/月。'
          : 'New nodes get 500 credits on registration. Pro: 299 cr/mo, Ultra: 999 cr/mo.'
        }</p>
      </div>

    </div>
  );
}
