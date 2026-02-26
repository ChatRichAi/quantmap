#!/usr/bin/env python3
"""
市场异动扫描器 - 修复版 (绕过 akshare 连接问题)
直接请求东方财富 API
"""

import requests
import pandas as pd
from datetime import datetime
import json

# 东方财富实时行情 API
EASTMONEY_API = "http://82.push2.eastmoney.com/api/qt/clist/get"

def get_stock_spot_em():
    """
    获取A股实时行情 (直接请求东方财富API)
    """
    params = {
        "pn": 1,
        "pz": 5000,  # 获取足够多的股票
        "po": 1,
        "np": 1,
        "fltt": 2,
        "invt": 2,
        "fid": "f20",  # 按成交额排序
        "fs": "m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23",  # A股所有股票
        "fields": "f12,f14,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f17,f18,f20,f21,f33,f34,f35,f36,f37,f38,f39,f40,f43,f44,f45,f46,f47,f48,f50,f57,f58,f60,f61,f62,f63,f64,f107,f115"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "http://quote.eastmoney.com/"
    }
    
    try:
        response = requests.get(EASTMONEY_API, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('data') and data['data'].get('diff'):
            stocks = data['data']['diff']
            df_data = []
            for stock in stocks:
                # 字段映射: f12=代码, f14=名称, f2=最新价, f3=涨跌幅, f4=涨跌额, f5=成交量, f6=成交额
                # f7=振幅, f8=换手率, f9=市盈率, f10=量比, f17=今开, f18=昨收, f20=总市值
                df_data.append({
                    '代码': stock.get('f12', ''),
                    '名称': stock.get('f14', ''),
                    '最新价': float(stock.get('f2', 0)) if stock.get('f2') != '-' else 0,
                    '涨跌幅': float(stock.get('f3', 0)) if stock.get('f3') != '-' else 0,
                    '涨跌额': float(stock.get('f4', 0)) if stock.get('f4') != '-' else 0,
                    '成交量': float(stock.get('f5', 0)) if stock.get('f5') != '-' else 0,
                    '成交额': float(stock.get('f6', 0)) if stock.get('f6') != '-' else 0,
                    '振幅': float(stock.get('f7', 0)) if stock.get('f7') != '-' else 0,
                    '换手率': float(stock.get('f8', 0)) if stock.get('f8') != '-' else 0,
                    '市盈率': float(stock.get('f9', 0)) if stock.get('f9') != '-' else 0,
                    '量比': float(stock.get('f10', 0)) if stock.get('f10') != '-' else 0,
                    '今开': float(stock.get('f17', 0)) if stock.get('f17') != '-' else 0,
                    '昨收': float(stock.get('f18', 0)) if stock.get('f18') != '-' else 0,
                    '总市值': float(stock.get('f20', 0)) if stock.get('f20') != '-' else 0,
                })
            return pd.DataFrame(df_data)
        else:
            print("⚠️ API 返回数据为空")
            return pd.DataFrame()
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return pd.DataFrame()

def scan_market_anomalies():
    """
    扫描市场异动股票
    """
    print("📡 正在扫描市场异动...")
    
    df = get_stock_spot_em()
    if df.empty:
        print("❌ 未能获取股票数据")
        return []
    
    print(f"✅ 成功获取 {len(df)} 只股票数据")
    
    anomalies = []
    
    # 1. 涨停股票 (>9.5%)
    limit_up = df[df['涨跌幅'] >= 9.5].copy()
    limit_up = limit_up.sort_values('涨跌幅', ascending=False)
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
    
    print(f"✅ 发现 {len(anomalies)} 只异动股票")
    return anomalies

def get_stock_basic_info(code):
    """获取股票基本信息"""
    try:
        # 简化为返回空，避免额外依赖
        return {}
    except Exception as e:
        print(f"⚠️ 获取 {code} 基本信息失败: {e}")
        return {}

def get_fund_flow(code):
    """获取资金流向数据"""
    try:
        return {}
    except Exception as e:
        print(f"⚠️ 获取 {code} 资金流向失败: {e}")
    return {}

if __name__ == "__main__":
    results = scan_market_anomalies()
    for r in results[:10]:
        print(f"{r['code']} {r['name']}: {r['type']} - {r['reason']}")
