'use client';

import { useState } from 'react';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { createOrder } from '@/lib/api';
import type { StrategyListing } from '@/lib/types';

interface ListingDetailProps {
  listing: StrategyListing;
}

const licenseLabel: Record<string, string> = {
  one_time: '一次性购买',
  subscription: '订阅',
  royalty: '版税分成',
};

const inputClass = "w-full bg-white/[0.03] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-[#667eea]/50 focus:shadow-[0_0_20px_rgba(102,126,234,0.15)] transition-all duration-300";

export default function ListingDetail({ listing }: ListingDetailProps) {
  const [traderId, setTraderId] = useState('');
  const [loading, setLoading] = useState(false);

  const handleBuy = async () => {
    if (!traderId) return alert('请输入交易者 ID');
    setLoading(true);
    try {
      await createOrder({ order_type: 'buy', trader_id: traderId, listing_id: listing.listing_id, price: listing.price });
      alert('下单成功！');
    } catch (e) { alert((e instanceof Error ? e.message : '下单失败')); }
    finally { setLoading(false); }
  };

  return (
    <div className="p-4 bg-white/[0.02] rounded-xl border border-white/[0.06] mt-2 space-y-4">
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div><span className="text-white/50">夏普比率: </span><span className="text-emerald-400 font-medium font-mono">{listing.sharpe_ratio?.toFixed(3)}</span></div>
        <div><span className="text-white/50">最大回撤: </span><span className="text-red-400 font-mono">{listing.max_drawdown != null ? `${(listing.max_drawdown*100).toFixed(1)}%` : '—'}</span></div>
        <div><span className="text-white/50">年化收益: </span><span className="text-blue-400 font-mono">{listing.annual_return != null ? `${(listing.annual_return*100).toFixed(1)}%` : '—'}</span></div>
        <div><span className="text-white/50">胜率: </span><span className="text-white/80 font-mono">{listing.win_rate != null ? `${(listing.win_rate*100).toFixed(1)}%` : '—'}</span></div>
        <div><span className="text-white/50">回测区间: </span><span className="text-white/80 text-xs">{listing.backtest_period}</span></div>
        <div><span className="text-white/50">验证次数: </span><span className="text-white/80">{listing.validation_count}</span></div>
        <div><span className="text-white/50">许可类型: </span><Badge variant="info">{licenseLabel[listing.license_type] ?? listing.license_type}</Badge></div>
        <div><span className="text-white/50">卖家: </span><span className="font-mono text-[11px] text-white/80">{listing.seller_id}</span></div>
      </div>
      {listing.description && <p className="text-sm text-white/60">{listing.description}</p>}
      <div className="flex gap-2 items-end">
        <div className="flex-1"><label className="text-[11px] text-white/40">交易者 ID</label><input className={`${inputClass} mt-1`} value={traderId} onChange={(e) => setTraderId(e.target.value)} placeholder="your_trader_id" /></div>
        <Button variant="primary" size="sm" loading={loading} onClick={handleBuy}>购买 {listing.price} 积分</Button>
      </div>
    </div>
  );
}
