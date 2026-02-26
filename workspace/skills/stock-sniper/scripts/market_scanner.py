#!/usr/bin/env python3
"""
市场异动扫描器 - 检测当日A股市场异动股票
"""

import akshare as ak
import pandas as pd
from datetime import datetime

def scan_market_anomalies():
    """
    扫描市场异动股票
    返回: list of dict 包含异动股票信息
    """
    print("📡 正在扫描市场异动...")
    
    # 获取实时行情
    df = ak.stock_zh_a_spot_em()
    
    anomalies = []
    
    # 1. 涨停股票
    limit_up = df[df['涨跌幅'] >= 9.5].copy()
    for _, row in limit_up.head(20).iterrows():
        anomalies.append({
            'code': row['代码'],
            'name': row['名称'],
            'price': row['最新价'],
            'change_pct': row['涨跌幅'],
            'volume': row['成交量'],
            'amount': row['成交额'],
            'type': '涨停',
            'reason': f"涨幅 {row['涨跌幅']:.2f}%"
        })
    
    # 2. 大幅放量 (>5倍均量)
    high_volume = df[df['量比'] >= 5].copy()
    for _, row in high_volume.head(10).iterrows():
        if row['代码'] not in [a['code'] for a in anomalies]:
            anomalies.append({
                'code': row['代码'],
                'name': row['名称'],
                'price': row['最新价'],
                'change_pct': row['涨跌幅'],
                'volume': row['成交量'],
                'amount': row['成交额'],
                'type': '放量异动',
                'reason': f"量比 {row['量比']:.2f}"
            })
    
    # 3. 急速拉升 (>3%且分时强势)
    surge = df[(df['涨跌幅'] >= 3) & (df['涨跌幅'] < 9.5)].copy()
    surge = surge.sort_values('涨跌幅', ascending=False)
    for _, row in surge.head(15).iterrows():
        if row['代码'] not in [a['code'] for a in anomalies]:
            anomalies.append({
                'code': row['代码'],
                'name': row['名称'],
                'price': row['最新价'],
                'change_pct': row['涨跌幅'],
                'volume': row['成交量'],
                'amount': row['成交额'],
                'type': '快速拉升',
                'reason': f"上涨 {row['涨跌幅']:.2f}%"
            })
    
    # 4. 连板股票（从涨停中筛选）
    # 需要额外的连板数据获取
    
    print(f"✅ 发现 {len(anomalies)} 只异动股票")
    return anomalies

def get_stock_basic_info(code):
    """获取股票基本信息"""
    try:
        df = ak.stock_individual_info_em(symbol=code)
        info = dict(zip(df['item'], df['value']))
        return info
    except Exception as e:
        print(f"⚠️ 获取 {code} 基本信息失败: {e}")
        return {}

def get_fund_flow(code):
    """获取资金流向数据"""
    try:
        df = ak.stock_individual_fund_flow(stock=code, market="sh" if code.startswith('6') else "sz")
        if not df.empty:
            latest = df.iloc[0]
            return {
                'main_inflow': latest.get('主力净流入', 0),
                'retail_inflow': latest.get('散户净流入', 0),
                'main_pct': latest.get('主力净流入占比', 0),
            }
    except Exception as e:
        print(f"⚠️ 获取 {code} 资金流向失败: {e}")
    return {}

if __name__ == "__main__":
    results = scan_market_anomalies()
    for r in results[:10]:
        print(f"{r['code']} {r['name']}: {r['type']} - {r['reason']}")
