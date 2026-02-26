#!/usr/bin/env python3
"""
DataSourceExpansion - 数据源无限扩展模块

不设上限，持续挖掘：
- 学术论文 (arXiv, SSRN, RePEc)
- 开源代码 (GitHub, GitLab)
- 市场数据 (价格、成交量、情绪)
- 新闻舆情 (财经新闻、社交媒体)
- 宏观经济 (指标、政策)
- 链上数据 (Crypto)
- 历史回测档案
"""

import os
import re
import json
import time
import random
import sqlite3
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Generator
from urllib.parse import quote_plus
from dataclasses import dataclass


@dataclass
class RawMaterial:
    """原始素材统一格式"""
    source: str
    source_id: str
    content_type: str  # 'text', 'code', 'data', 'formula'
    title: str
    content: str
    metadata: Dict
    extracted_at: str
    quality_score: float  # 0-1


class ArxivExpander:
    """arXiv 扩展挖掘器 - 更深更广"""
    
    DEEP_QUERIES = [
        # 经典策略
        ('cat:q-fin.TR', 'trading'),
        ('cat:q-fin.PM', 'portfolio'),
        ('cat:q-fin.ST', 'statistical'),
        ('cat:q-fin.CP', 'computational'),
        
        # 技术指标
        ('momentum', 'momentum'),
        ('mean reversion', 'mean_reversion'),
        ('trend following', 'trend'),
        ('breakout', 'breakout'),
        ('volatility', 'volatility'),
        ('RSI MACD', 'technical'),
        
        # 统计方法
        ('cointegration', 'cointegration'),
        ('Kalman filter', 'kalman'),
        ('hidden markov', 'hmm'),
        ('regime switching', 'regime'),
        
        # 机器学习
        ('LSTM trading', 'lstm'),
        ('reinforcement learning trading', 'rl'),
        ('random forest', 'rf'),
        ('XGBoost', 'xgboost'),
        ('transformer', 'transformer'),
        
        # 风险管理
        ('risk parity', 'risk_parity'),
        ('Kelly criterion', 'kelly'),
        ('drawdown control', 'drawdown'),
        ('position sizing', 'sizing'),
        
        # 市场微观结构
        ('order flow', 'order_flow'),
        ('market making', 'mm'),
        ('latency arbitrage', 'latency'),
        ('tick data', 'tick'),
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'QuantResearch/1.0 (Academic Study)'
        })
        self.rate_limit_delay = 3  # 秒
    
    def deep_mine(self, max_per_query: int = 20) -> Generator[RawMaterial, None, None]:
        """深度挖掘所有查询"""
        print(f"\n📚 ArXiv Deep Mining ({len(self.DEEP_QUERIES)} queries)...")
        
        for query, category in self.DEEP_QUERIES:
            try:
                materials = self._fetch_query(query, category, max_per_query)
                for m in materials:
                    yield m
                
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                print(f"   ⚠️  {category}: {e}")
                continue
    
    def _fetch_query(self, query: str, category: str, limit: int) -> List[RawMaterial]:
        """获取单个查询"""
        url = f"http://export.arxiv.org/api/query?search_query={quote_plus(query)}&start=0&max_results={limit}&sortBy=submittedDate&sortOrder=descending"
        
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)
        
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        materials = []
        
        for entry in root.findall('atom:entry', ns):
            paper_id = entry.find('atom:id', ns)
            title = entry.find('atom:title', ns)
            summary = entry.find('atom:summary', ns)
            published = entry.find('atom:published', ns)
            
            if paper_id is not None and title is not None:
                materials.append(RawMaterial(
                    source='arxiv',
                    source_id=paper_id.text.split('/')[-1],
                    content_type='text',
                    title=title.text.strip() if title.text else '',
                    content=summary.text.strip() if summary is not None and summary.text else '',
                    metadata={
                        'category': category,
                        'query': query,
                        'published': published.text if published is not None else '',
                        'authors': [author.find('atom:name', ns).text 
                                   for author in entry.findall('atom:author', ns)
                                   if author.find('atom:name', ns) is not None]
                    },
                    extracted_at=datetime.now().isoformat(),
                    quality_score=self._assess_quality(title.text if title.text else '', 
                                                       summary.text if summary is not None and summary.text else '')
                ))
        
        print(f"   {category}: {len(materials)} papers")
        return materials
    
    def _assess_quality(self, title: str, summary: str) -> float:
        """评估论文质量"""
        score = 0.5
        text = (title + ' ' + summary).lower()
        
        # 高质量信号
        quality_signals = [
            'empirical', 'backtest', 'out-of-sample', 'robust',
            'transaction costs', 'risk-adjusted', 'sharpe',
            'implementation', 'live trading'
        ]
        
        for signal in quality_signals:
            if signal in text:
                score += 0.05
        
        # 负面信号
        red_flags = ['theoretical', 'simulation only', 'no empirical']
        for flag in red_flags:
            if flag in text:
                score -= 0.1
        
        return min(1.0, max(0.0, score))


class MarketDataMiner:
    """市场数据挖掘器 - 从价格中提取模式"""
    
    def __init__(self):
        self.patterns = []
    
    def mine_patterns(self, symbols: List[str] = None) -> List[RawMaterial]:
        """从市场数据挖掘模式"""
        print("\n📈 Mining market patterns...")
        
        if symbols is None:
            symbols = ['BTC-USD', 'ETH-USD', 'AAPL', 'SPY']
        
        materials = []
        
        for symbol in symbols:
            try:
                # 获取 OKX 数据
                data = self._fetch_okx(symbol)
                if data:
                    patterns = self._extract_patterns(symbol, data)
                    materials.extend(patterns)
            except Exception as e:
                print(f"   ⚠️  {symbol}: {e}")
        
        print(f"   Extracted {len(materials)} pattern materials")
        return materials
    
    def _fetch_okx(self, symbol: str) -> Optional[List[Dict]]:
        """获取 OKX 数据"""
        # 转换符号格式
        inst_id = symbol.replace('-', '-')
        if '-' not in inst_id:
            inst_id = f"{inst_id}-USD"
        
        url = f"https://www.okx.com/api/v5/market/index-candles?instId={inst_id}&bar=1D&limit=100"
        
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if data.get('data'):
            return [
                {
                    'timestamp': int(c[0]),
                    'open': float(c[1]),
                    'high': float(c[2]),
                    'low': float(c[3]),
                    'close': float(c[4]),
                    'confirmed': c[5] == '1'
                }
                for c in data['data'] if c[5] == '1'  # 只取确认的数据
            ]
        return None
    
    def _extract_patterns(self, symbol: str, data: List[Dict]) -> List[RawMaterial]:
        """从价格数据提取模式"""
        materials = []
        
        closes = [d['close'] for d in data]
        highs = [d['high'] for d in data]
        lows = [d['low'] for d in data]
        
        # 计算统计特征
        returns = [(closes[i] / closes[i-1] - 1) for i in range(1, len(closes))]
        
        # 趋势模式
        sma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else None
        sma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else None
        
        if sma20 and sma50:
            trend = 'uptrend' if sma20 > sma50 else 'downtrend'
            materials.append(RawMaterial(
                source='market_data',
                source_id=f"{symbol}_trend",
                content_type='data',
                title=f"{symbol} Trend Pattern",
                content=f"Current trend: {trend}, SMA20={sma20:.2f}, SMA50={sma50:.2f}",
                metadata={
                    'symbol': symbol,
                    'trend': trend,
                    'sma20': sma20,
                    'sma50': sma50
                },
                extracted_at=datetime.now().isoformat(),
                quality_score=0.7
            ))
        
        # 波动率模式
        if len(returns) >= 20:
            volatility = (sum(r**2 for r in returns[-20:]) / 20) ** 0.5
            vol_regime = 'high_vol' if volatility > 0.03 else 'low_vol'
            
            materials.append(RawMaterial(
                source='market_data',
                source_id=f"{symbol}_volatility",
                content_type='data',
                title=f"{symbol} Volatility Pattern",
                content=f"20-day volatility: {volatility:.4f}, regime: {vol_regime}",
                metadata={
                    'symbol': symbol,
                    'volatility': volatility,
                    'regime': vol_regime
                },
                extracted_at=datetime.now().isoformat(),
                quality_score=0.6
            ))
        
        # 支撑阻力
        if len(highs) >= 20 and len(lows) >= 20:
            recent_high = max(highs[-20:])
            recent_low = min(lows[-20:])
            
            materials.append(RawMaterial(
                source='market_data',
                source_id=f"{symbol}_levels",
                content_type='data',
                title=f"{symbol} Support/Resistance",
                content=f"Recent high: {recent_high:.2f}, Recent low: {recent_low:.2f}",
                metadata={
                    'symbol': symbol,
                    'resistance': recent_high,
                    'support': recent_low
                },
                extracted_at=datetime.now().isoformat(),
                quality_score=0.6
            ))
        
        return materials


class HistoricalStrategyMiner:
    """历史策略挖掘器 - 从过往记录学习"""
    
    def __init__(self, memory_path: str = '/Users/oneday/.openclaw/workspace/memory'):
        self.memory_path = Path(memory_path)
    
    def mine_historical(self) -> List[RawMaterial]:
        """挖掘历史记录"""
        print("\n📜 Mining historical records...")
        
        materials = []
        
        # 挖掘交易日志
        materials.extend(self._mine_trade_logs())
        
        # 挖掘策略表现
        materials.extend(self._mine_strategy_performance())
        
        # 挖掘回测结果
        materials.extend(self._mine_backtest_results())
        
        print(f"   Historical materials: {len(materials)}")
        return materials
    
    def _mine_trade_logs(self) -> List[RawMaterial]:
        """挖掘交易日志"""
        materials = []
        
        daily_logs = list(self.memory_path.glob('daily/*.md'))
        
        for log_file in daily_logs[-30:]:  # 最近30天
            try:
                content = log_file.read_text(encoding='utf-8')
                
                # 提取交易决策部分
                if '交易' in content or '持仓' in content:
                    materials.append(RawMaterial(
                        source='trade_history',
                        source_id=str(log_file),
                        content_type='text',
                        title=f"Trade Log: {log_file.stem}",
                        content=content[:3000],
                        metadata={
                            'date': log_file.stem,
                            'type': 'daily_log'
                        },
                        extracted_at=datetime.now().isoformat(),
                        quality_score=0.5
                    ))
            except:
                pass
        
        return materials
    
    def _mine_strategy_performance(self) -> List[RawMaterial]:
        """挖掘策略表现记录"""
        materials = []
        
        strategy_files = list(self.memory_path.glob('strategies/*.md'))
        
        for sf in strategy_files:
            try:
                content = sf.read_text(encoding='utf-8')
                materials.append(RawMaterial(
                    source='strategy_performance',
                    source_id=str(sf),
                    content_type='text',
                    title=f"Strategy: {sf.stem}",
                    content=content[:5000],
                    metadata={
                        'strategy': sf.stem,
                        'type': 'performance_review'
                    },
                    extracted_at=datetime.now().isoformat(),
                    quality_score=0.6
                ))
            except:
                pass
        
        return materials
    
    def _mine_backtest_results(self) -> List[RawMaterial]:
        """挖掘回测结果"""
        materials = []
        
        # 查找回测数据库或文件
        backtest_db = self.memory_path / 'backtests'
        if backtest_db.exists():
            for bt_file in backtest_db.glob('*.json'):
                try:
                    with open(bt_file) as f:
                        data = json.load(f)
                    
                    materials.append(RawMaterial(
                        source='backtest_result',
                        source_id=str(bt_file),
                        content_type='data',
                        title=f"Backtest: {bt_file.stem}",
                        content=json.dumps(data, indent=2)[:5000],
                        metadata=data,
                        extracted_at=datetime.now().isoformat(),
                        quality_score=0.7
                    ))
                except:
                    pass
        
        return materials


class UnifiedMaterialAggregator:
    """统一素材聚合器"""
    
    def __init__(self):
        self.arxiv = ArxivExpander()
        self.market = MarketDataMiner()
        self.history = HistoricalStrategyMiner()
    
    def aggregate_all(self) -> List[RawMaterial]:
        """聚合所有数据源"""
        print("\n" + "="*70)
        print("🌐 UNIFIED MATERIAL AGGREGATION")
        print("="*70)
        
        all_materials = []
        
        # 1. ArXiv 深度挖掘
        for material in self.arxiv.deep_mine(max_per_query=10):
            all_materials.append(material)
        
        # 2. 市场数据
        all_materials.extend(self.market.mine_patterns())
        
        # 3. 历史记录
        all_materials.extend(self.history.mine_historical())
        
        # 4. 去重
        seen = set()
        unique = []
        for m in all_materials:
            key = f"{m.source}:{m.source_id}"
            if key not in seen:
                seen.add(key)
                unique.append(m)
        
        # 按质量排序
        unique.sort(key=lambda x: -x.quality_score)
        
        print(f"\n✅ Total unique materials: {len(unique)}")
        print(f"   Source breakdown:")
        
        source_counts = {}
        for m in unique:
            source_counts[m.source] = source_counts.get(m.source, 0) + 1
        
        for source, count in sorted(source_counts.items(), key=lambda x: -x[1]):
            print(f"   - {source}: {count}")
        
        return unique


if __name__ == '__main__':
    aggregator = UnifiedMaterialAggregator()
    materials = aggregator.aggregate_all()
    
    # 保存结果
    output = [{
        'source': m.source,
        'source_id': m.source_id,
        'title': m.title,
        'content': m.content[:500],
        'quality_score': m.quality_score,
        'metadata': m.metadata
    } for m in materials[:50]]
    
    with open('mined_materials.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved top 50 materials to mined_materials.json")
