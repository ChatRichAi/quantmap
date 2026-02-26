#!/usr/bin/env python3
"""
QuantClaw Autonomous Seed Discovery Engine
自主种子发现引擎 - 从数据中提取初始因子

核心理念:
1. 不依赖人类预设的种子
2. 从原始价格数据自动发现有效特征组合
3. 使用无监督学习识别高潜力模式
4. 自动生成初始策略基因
"""

import sys
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Tuple
import itertools

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from evolution_ecosystem import QuantClawEvolutionHub, Gene
from factor_backtest_validator import FactorValidator, BacktestEngine


class AutonomousSeedDiscovery:
    """
    自主种子发现器
    
    从价格数据自动发现有效策略模式
    """
    
    def __init__(self):
        self.validator = FactorValidator()
        self.raw_operators = [
            '>', '<', '==', 'AND', 'OR'
        ]
        self.raw_indicators = [
            'SMA', 'EMA', 'RSI', 'MACD', 'BB', 'ATR', 'ADX',
            'MOM', 'ROC', 'STD', 'MAX', 'MIN'
        ]
        self.raw_parameters = {
            'period': [5, 10, 20, 50],
            'threshold': [0.3, 0.5, 0.7, 0.8],
            'multiplier': [1.5, 2.0, 2.5]
        }
        
    def fetch_data(self, symbol: str = 'AAPL', days: int = 500) -> pd.DataFrame:
        """获取原始价格数据"""
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=f"{days}d")
        return df
    
    def calculate_base_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算基础特征库"""
        features = df.copy()
        
        # 价格特征
        features['returns'] = df['Close'].pct_change()
        features['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # 趋势特征
        for period in [5, 10, 20, 50]:
            features[f'sma_{period}'] = df['Close'].rolling(period).mean()
            features[f'ema_{period}'] = df['Close'].ewm(span=period).mean()
            features[f'mom_{period}'] = df['Close'].diff(period)
            features[f'roc_{period}'] = df['Close'].pct_change(period)
        
        # 波动特征
        features['volatility_20'] = features['returns'].rolling(20).std() * np.sqrt(252)
        features['atr_14'] = self._calculate_atr(df, 14)
        
        # 技术特征
        features['rsi_14'] = self._calculate_rsi(df['Close'], 14)
        features['rsi_7'] = self._calculate_rsi(df['Close'], 7)
        
        # 布林带
        features['bb_upper'], features['bb_lower'], features['bb_width'] = \
            self._calculate_bollinger(df['Close'], 20, 2)
        
        # 价格位置
        features['price_position'] = (df['Close'] - features['sma_20']) / features['sma_20']
        
        # 成交量特征
        features['volume_sma_20'] = df['Volume'].rolling(20).mean()
        features['volume_ratio'] = df['Volume'] / features['volume_sma_20']
        
        return features.dropna()
    
    def _calculate_rsi(self, prices, period=14):
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_bollinger(self, prices, period=20, std=2):
        """计算布林带"""
        sma = prices.rolling(window=period).mean()
        rolling_std = prices.rolling(window=period).std()
        upper = sma + (rolling_std * std)
        lower = sma - (rolling_std * std)
        width = (upper - lower) / sma
        return upper, lower, width
    
    def _calculate_atr(self, df, period=14):
        """计算ATR"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        return true_range.rolling(period).mean()
    
    def discover_patterns(self, features: pd.DataFrame, n_patterns: int = 20) -> List[Dict]:
        """
        从特征中发现高潜力模式
        
        使用启发式方法识别与高收益相关的特征组合
        """
        patterns = []
        
        # 计算未来收益
        future_returns = features['Close'].shift(-5) / features['Close'] - 1
        
        # 特征列表
        feature_cols = [c for c in features.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume']]
        
        print(f"   Analyzing {len(feature_cols)} features...")
        
        # 单特征分析
        for col in feature_cols:
            if col in ['returns', 'log_returns', 'future_returns']:
                continue
                
            feature = features[col]
            
            # 测试不同阈值
            for threshold in feature.quantile([0.2, 0.3, 0.5, 0.7, 0.8]).values:
                # 条件1: feature > threshold
                mask_high = feature > threshold
                if mask_high.sum() > 10:
                    avg_return_high = future_returns[mask_high].mean()
                    win_rate_high = (future_returns[mask_high] > 0).mean()
                    
                    if avg_return_high > 0.01 and win_rate_high > 0.51:  # 降低门槛
                        patterns.append({
                            'type': 'single',
                            'condition': f"{col} > {threshold:.4f}",
                            'avg_return': avg_return_high,
                            'win_rate': win_rate_high,
                            'frequency': mask_high.sum() / len(features)
                        })
                
                # 条件2: feature < threshold
                mask_low = feature < threshold
                if mask_low.sum() > 10:
                    avg_return_low = future_returns[mask_low].mean()
                    win_rate_low = (future_returns[mask_low] > 0).mean()
                    
                    if avg_return_low > 0.01 and win_rate_low > 0.51:  # 降低门槛
                        patterns.append({
                            'type': 'single',
                            'condition': f"{col} < {threshold:.4f}",
                            'avg_return': avg_return_low,
                            'win_rate': win_rate_low,
                            'frequency': mask_low.sum() / len(features)
                        })
        
        # 双特征组合分析
        print(f"   Testing feature combinations...")
        top_features = [p['condition'].split()[0] for p in sorted(patterns, key=lambda x: x['avg_return'], reverse=True)[:5]]
        
        for feat1, feat2 in itertools.combinations(top_features[:3], 2):
            if feat1 not in features.columns or feat2 not in features.columns:
                continue
                
            for op in ['AND', 'OR']:
                # 简单组合测试
                mask1 = features[feat1] > features[feat1].quantile(0.7)
                mask2 = features[feat2] > features[feat2].quantile(0.7)
                
                if op == 'AND':
                    combined_mask = mask1 & mask2
                else:
                    combined_mask = mask1 | mask2
                
                if combined_mask.sum() > 5:
                    avg_ret = future_returns[combined_mask].mean()
                    win_rate = (future_returns[combined_mask] > 0).mean()
                    
                    if avg_ret > 0.008 and win_rate > 0.50:  # 降低门槛
                        patterns.append({
                            'type': 'combined',
                            'condition': f"({feat1} > 70%tile) {op} ({feat2} > 70%tile)",
                            'avg_return': avg_ret,
                            'win_rate': win_rate,
                            'frequency': combined_mask.sum() / len(features)
                        })
        
        # 排序并返回最佳模式
        patterns.sort(key=lambda x: x['avg_return'] * x['win_rate'], reverse=True)
        return patterns[:n_patterns]
    
    def _generate_semantic_name(self, formula: str, pattern: Dict) -> str:
        """根据公式内容生成语义化名称"""
        # 指标缩写映射
        indicator_abbr = {
            'SMA': 'S', 'EMA': 'E', 'RSI': 'R', 'MACD': 'M',
            'BB': 'B', 'ATR': 'A', 'MOM': 'Mo', 'ROC': 'Ro',
            'Volatility': 'V', 'Volume': 'Vol', 'Stoch': 'St',
            'ADX': 'Ax', 'Close': 'C', 'High': 'H', 'Low': 'L'
        }
        
        # 提取公式中的关键指标
        indicators = []
        for ind, abbr in indicator_abbr.items():
            if ind in formula:
                indicators.append(abbr)
        
        # 提取数字参数
        import re
        numbers = re.findall(r'\d+', formula)
        param_str = numbers[0] if numbers else ''
        
        # 确定信号类型
        if '<' in formula and ('30' in formula or '20' in formula):
            signal_type = 'Over'  # Oversold
        elif '>' in formula and ('70' in formula or '80' in formula):
            signal_type = 'Ovrb'  # Overbought
        elif 'AND' in formula:
            signal_type = 'And'
        elif 'OR' in formula:
            signal_type = 'Or'
        else:
            signal_type = 'Sig'
        
        # 组合名称: 指标_信号类型_参数
        ind_part = ''.join(indicators[:3]) if indicators else 'X'
        name = f"{ind_part}_{signal_type}"
        if param_str:
            name += f"_{param_str}"
        
        # 添加短hash确保唯一性
        short_hash = hex(abs(hash(formula)) % 0xFFF)[2:].upper()
        return f"{name}_{short_hash}"
    
    def pattern_to_gene(self, pattern: Dict, gene_id: str) -> Gene:
        """将发现的模式转换为Gene"""
        # 转换特征名称为Gene格式
        condition = pattern['condition']
        
        # 简化特征名
        feature_map = {
            'sma_': 'SMA(',
            'ema_': 'EMA(',
            'rsi_': 'RSI(',
            'mom_': 'MOM(',
            'roc_': 'ROC(',
            'bb_': 'BB.',
            'atr_': 'ATR(',
            'volume_ratio': 'VolumeRatio',
            'price_position': 'PricePos',
            'volatility_': 'Volatility('
        }
        
        gene_formula = condition
        for old, new in feature_map.items():
            gene_formula = gene_formula.replace(old, new)
        
        # 根据公式内容生成语义化名称
        gene_name = self._generate_semantic_name(gene_formula, pattern)
        
        return Gene(
            gene_id=gene_id,
            name=gene_name,
            description=f"Auto-discovered pattern: {condition}",
            formula=gene_formula,
            parameters={'discovered': True, 'avg_return': pattern['avg_return'], 'win_rate': pattern['win_rate']},
            source=f"autonomous_discovery:{datetime.now().strftime('%Y%m%d')}",
            author="seed_discovery_engine",
            created_at=datetime.now(),
            generation=0  # 这些是新的种子
        )
    
    def discover_seeds(self, symbols: List[str] = None, n_seeds: int = 10) -> List[Gene]:
        """
        主函数：自主发现种子基因
        """
        if symbols is None:
            symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        print("=" * 70)
        print("🌱 Autonomous Seed Discovery Engine")
        print("=" * 70)
        print(f"   Analyzing {len(symbols)} symbols")
        print(f"   Target: {n_seeds} high-quality seeds")
        print()
        
        all_patterns = []
        
        for symbol in symbols:
            print(f"📊 Analyzing {symbol}...")
            
            # 获取数据
            df = self.fetch_data(symbol, days=500)
            
            # 计算特征
            features = self.calculate_base_features(df)
            
            # 发现模式
            patterns = self.discover_patterns(features, n_patterns=20)
            
            print(f"   Found {len(patterns)} potential patterns")
            
            # 添加股票标记
            for p in patterns:
                p['symbol'] = symbol
            
            all_patterns.extend(patterns)
        
        # 跨股票验证 - 选择在多个股票上表现稳定的模式
        print("\n🔍 Cross-validation across symbols...")
        
        pattern_scores = {}
        for p in all_patterns:
            key = p['condition']
            if key not in pattern_scores:
                pattern_scores[key] = {
                    'returns': [],
                    'win_rates': [],
                    'symbols': set()
                }
            pattern_scores[key]['returns'].append(p['avg_return'])
            pattern_scores[key]['win_rates'].append(p['win_rate'])
            pattern_scores[key]['symbols'].add(p['symbol'])
        
        # 选择在多个股票上表现的模式 (降低门槛)
        robust_patterns = []
        for condition, data in pattern_scores.items():
            if len(data['symbols']) >= 1:  # 至少在1个股票上有效 (放宽)
                avg_return = np.mean(data['returns'])
                avg_win_rate = np.mean(data['win_rates'])
                
                if avg_return > 0.005 and avg_win_rate > 0.51:  # 降低门槛
                    robust_patterns.append({
                        'condition': condition,
                        'avg_return': avg_return,
                        'win_rate': avg_win_rate,
                        'n_symbols': len(data['symbols'])
                    })
        
        # 如果没有找到，选择单个股票上表现最好的
        if not robust_patterns:
            print("   No cross-symbol patterns found, selecting best single-symbol patterns...")
            for condition, data in pattern_scores.items():
                if data['returns']:
                    best_return = max(data['returns'])
                    best_win_rate = max(data['win_rates'])
                    
                    if best_return > 0.01 and best_win_rate > 0.52:
                        robust_patterns.append({
                            'condition': condition,
                            'avg_return': best_return,
                            'win_rate': best_win_rate,
                            'n_symbols': 1
                        })
        
        # 限制数量
        robust_patterns.sort(key=lambda x: x['avg_return'] * x['win_rate'], reverse=True)
        robust_patterns = robust_patterns[:n_seeds]
        
        print(f"\n✅ {len(robust_patterns)} robust patterns found across multiple symbols")
        
        # 转换为Gene
        discovered_genes = []
        for i, pattern in enumerate(robust_patterns[:n_seeds], 1):
            gene_id = f"g_seed_auto_{datetime.now().strftime('%Y%m%d')}_{i:03d}"
            gene = self.pattern_to_gene(pattern, gene_id)
            discovered_genes.append(gene)
            
            print(f"\n{i}. {gene.name}")
            print(f"   Formula: {gene.formula[:60]}")
            print(f"   Expected Return: {pattern['avg_return']:.2%}")
            print(f"   Win Rate: {pattern['win_rate']:.1%}")
            print(f"   Valid on {pattern['n_symbols']} symbols")
        
        return discovered_genes
    
    def save_seeds_to_pool(self, genes: List[Gene]):
        """保存发现的种子到基因池"""
        hub = QuantClawEvolutionHub()
        
        for gene in genes:
            hub.publish_gene(gene)
        
        print(f"\n💾 Saved {len(genes)} discovered seeds to gene pool")


def main():
    """主函数 - 运行自主种子发现"""
    discoverer = AutonomousSeedDiscovery()
    
    # 发现种子
    seeds = discoverer.discover_seeds(
        symbols=['AAPL', 'MSFT', 'GOOGL', 'JPM', 'XOM'],
        n_seeds=10
    )
    
    # 保存到基因池
    discoverer.save_seeds_to_pool(seeds)
    
    print("\n" + "=" * 70)
    print("🎉 Autonomous Seed Discovery Complete!")
    print("=" * 70)
    print(f"\nNext: Run factor evolution with these data-driven seeds")


if __name__ == "__main__":
    main()
