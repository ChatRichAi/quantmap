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
    <div className="p-4 bg-bg-dark rounded-lg border border-border mt-2 space-y-4">
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div><span className="text-text-secondary">夏普比率: </span><span className="text-success font-medium">{listing.sharpe_ratio?.toFixed(3)}</span></div>
        <div><span className="text-text-secondary">最大回撤: </span><span className="text-danger">{listing.max_drawdown != null ? `${(listing.max_drawdown*100).toFixed(1)}%` : '—'}</span></div>
        <div><span className="text-text-secondary">年化收益: </span><span className="text-info">{listing.annual_return != null ? `${(listing.annual_return*100).toFixed(1)}%` : '—'}</span></div>
        <div><span className="text-text-secondary">胜率: </span><span className="text-text-primary">{listing.win_rate != null ? `${(listing.win_rate*100).toFixed(1)}%` : '—'}</span></div>
        <div><span className="text-text-secondary">回测区间: </span><span className="text-text-primary text-xs">{listing.backtest_period}</span></div>
        <div><span className="text-text-secondary">验证次数: </span><span className="text-text-primary">{listing.validation_count}</span></div>
        <div><span className="text-text-secondary">许可类型: </span><Badge variant="info">{licenseLabel[listing.license_type] ?? listing.license_type}</Badge></div>
        <div><span className="text-text-secondary">卖家: </span><span className="font-mono text-xs text-text-primary">{listing.seller_id}</span></div>
      </div>
      {listing.description && <p className="text-sm text-text-secondary">{listing.description}</p>}
      <div className="flex gap-2 items-end">
        <div className="flex-1"><label className="text-xs text-text-secondary">交易者 ID</label><input className="w-full mt-1 bg-bg-card border border-border rounded px-2 py-1.5 text-sm text-text-primary focus:outline-none focus:border-primary" value={traderId} onChange={(e) => setTraderId(e.target.value)} placeholder="your_trader_id" /></div>
        <Button variant="primary" size="sm" loading={loading} onClick={handleBuy}>购买 {listing.price} 积分</Button>
      </div>
    </div>
  );
}
