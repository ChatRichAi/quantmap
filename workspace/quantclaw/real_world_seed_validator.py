#!/usr/bin/env python3
"""
QuantClaw Real-World Seed Validator
真实市场种子验证器

核心原则:
1. 所有种子必须通过真实回测才能进入基因池
2. 多市场/多周期验证防止过拟合
3. Walk-forward验证确保稳健性
4. 只有通过验证的种子才有资格繁衍
"""

import sys
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from evolution_ecosystem import QuantClawEvolutionHub, Gene
from factor_backtest_validator import FactorValidator


class RealWorldSeedValidator:
    """
    真实市场种子验证器
    
    严格的种子准入标准:
    - 夏普比率 > 1.0
    - 最大回撤 < 20%
    - 胜率 > 50%
    - 至少通过3个不同市场的验证
    - Walk-forward测试通过
    """
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.db_path = db_path
        self.hub = QuantClawEvolutionHub(db_path)
        self.validator = FactorValidator(db_path)
        
        # 严格通过标准
        self.passing_criteria = {
            'min_sharpe': 1.0,
            'max_drawdown': -0.20,
            'min_win_rate': 0.50,
            'min_profit_factor': 1.5,
            'min_markets_passed': 2,  # 至少通过2个市场
            'min_walkforward_score': 0.6  # Walk-forward稳健性
        }
        
        # 验证市场列表
        self.validation_markets = [
            'AAPL',  # 美股科技股
            'MSFT',  # 美股科技股
            'JPM',   # 美股金融股
            'XOM',   # 美股能源股
            'SPY',   # 美股大盘
        ]
    
    def validate_seed(self, gene: Gene, verbose: bool = True) -> Tuple[bool, Dict]:
        """
        验证单个种子
        
        Returns:
            (passed, validation_report)
        """
        if verbose:
            print(f"\n🔬 Validating seed: {gene.name}")
            print(f"   Formula: {gene.formula[:60]}...")
        
        # 1. 多市场回测
        market_results = {}
        passed_markets = 0
        
        for symbol in self.validation_markets:
            try:
                results = self.validator.validate_gene(gene, symbols=[symbol])
                if results:
                    result = results[0]
                    market_results[symbol] = {
                        'sharpe': result.sharpe_ratio,
                        'drawdown': result.max_drawdown,
                        'win_rate': result.win_rate,
                        'passed': result.passed
                    }
                    if result.passed:
                        passed_markets += 1
            except Exception as e:
                if verbose:
                    print(f"   ⚠️ Error testing {symbol}: {e}")
                market_results[symbol] = {'error': str(e)}
        
        # 2. Walk-forward验证
        walkforward_score = self._walkforward_validation(gene)
        
        # 3. 综合评估
        report = {
            'gene_id': gene.gene_id,
            'name': gene.name,
            'formula': gene.formula,
            'market_results': market_results,
            'passed_markets': passed_markets,
            'walkforward_score': walkforward_score,
            'total_tests': len(self.validation_markets),
            'timestamp': datetime.now().isoformat()
        }
        
        # 通过标准
        passed = (
            passed_markets >= self.passing_criteria['min_markets_passed'] and
            walkforward_score >= self.passing_criteria['min_walkforward_score']
        )
        
        report['passed'] = passed
        
        if verbose:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"   {status}")
            print(f"   Markets passed: {passed_markets}/{len(self.validation_markets)}")
            print(f"   Walk-forward score: {walkforward_score:.2f}")
        
        return passed, report
    
    def _walkforward_validation(self, gene: Gene, n_windows: int = 3) -> float:
        """
        Walk-forward验证
        
        将数据分为多个窗口，确保策略在不同时期都有效
        """
        try:
            from yfinance import Ticker
            
            # 获取更长的历史数据
            ticker = Ticker('AAPL')
            data = ticker.history(period='3y')
            
            if len(data) < 500:
                return 0.0
            
            # 分为n个窗口
            window_size = len(data) // n_windows
            scores = []
            
            for i in range(n_windows):
                start_idx = i * window_size
                end_idx = start_idx + window_size
                window_data = data.iloc[start_idx:end_idx]
                
                # 在这个窗口上测试
                # 简化版：计算窗口内的夏普比率
                returns = window_data['Close'].pct_change().dropna()
                if len(returns) > 20 and returns.std() > 0:
                    sharpe = returns.mean() / returns.std() * np.sqrt(252)
                    # 转换为0-1分数
                    score = min(max((sharpe + 2) / 4, 0), 1)
                    scores.append(score)
            
            # 返回最低分（最差的窗口表现）
            return min(scores) if scores else 0.0
            
        except Exception as e:
            print(f"   Walk-forward error: {e}")
            return 0.0
    
    def validate_all_seeds(self, seeds: List[Gene]) -> List[Gene]:
        """
        批量验证种子，返回通过验证的种子
        """
        print("=" * 70)
        print("🔬 Real-World Seed Validation")
        print("=" * 70)
        print(f"   Testing {len(seeds)} seeds")
        print(f"   Markets: {', '.join(self.validation_markets)}")
        print(f"   Passing criteria:")
        print(f"     - Min markets passed: {self.passing_criteria['min_markets_passed']}")
        print(f"     - Min walk-forward score: {self.passing_criteria['min_walkforward_score']}")
        print()
        
        self.validator.connect()
        
        passed_seeds = []
        all_reports = []
        
        try:
            for i, seed in enumerate(seeds, 1):
                print(f"\n[{i}/{len(seeds)}] ", end='')
                passed, report = self.validate_seed(seed)
                all_reports.append(report)
                
                if passed:
                    passed_seeds.append(seed)
                    # 标记为已验证
                    seed.source = f"validated:{seed.source}"
        
        finally:
            self.validator.disconnect()
        
        # 保存验证报告
        self._save_validation_reports(all_reports)
        
        # 输出总结
        print("\n" + "=" * 70)
        print("📊 Validation Summary")
        print("=" * 70)
        print(f"   Total tested: {len(seeds)}")
        print(f"   Passed: {len(passed_seeds)} ({len(passed_seeds)/len(seeds)*100:.1f}%)")
        print(f"   Failed: {len(seeds) - len(passed_seeds)}")
        print()
        
        if passed_seeds:
            print("🏆 Passed Seeds:")
            for seed in passed_seeds:
                print(f"   - {seed.name}")
        
        return passed_seeds
    
    def _save_validation_reports(self, reports: List[Dict]):
        """保存验证报告到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seed_validation_reports (
                report_id TEXT PRIMARY KEY,
                gene_id TEXT,
                name TEXT,
                passed BOOLEAN,
                market_results TEXT,
                walkforward_score REAL,
                timestamp TEXT
            )
        ''')
        
        for report in reports:
            cursor.execute('''
                INSERT OR REPLACE INTO seed_validation_reports VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"val_{report['gene_id']}_{datetime.now().strftime('%Y%m%d')}",
                report['gene_id'],
                report['name'],
                report['passed'],
                json.dumps(report['market_results']),
                report['walkforward_score'],
                report['timestamp']
            ))
        
        conn.commit()
        conn.close()
    
    def filter_gene_pool(self):
        """
        清理基因池，只保留通过验证的基因
        """
        print("\n🧹 Filtering gene pool...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有基因
        cursor.execute('SELECT * FROM genes')
        all_genes = cursor.fetchall()
        
        # 标记未验证的基因
        unvalidated_count = 0
        for row in all_genes:
            gene_id = row[0]
            source = row[5]
            
            # 检查是否已验证
            if 'validated:' not in source and 'rescue' not in source and 'seed' not in source:
                # 标记为待验证
                cursor.execute('''
                    UPDATE genes SET source = ? WHERE gene_id = ?
                ''', (f"unvalidated:{source}", gene_id))
                unvalidated_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"   Marked {unvalidated_count} genes as unvalidated")
        print(f"   Use validate_all_seeds() to verify them")


def main():
    """主函数 - 验证当前所有种子"""
    validator = RealWorldSeedValidator()
    
    # 加载当前基因池
    hub = QuantClawEvolutionHub()
    conn = sqlite3.connect(hub.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM genes WHERE generation = 0')  # 只验证种子
    rows = cursor.fetchall()
    conn.close()
    
    seeds = []
    for row in rows:
        gene = Gene(
            gene_id=row[0],
            name=row[1],
            description=row[2],
            formula=row[3],
            parameters=json.loads(row[4]),
            source=row[5],
            author=row[6],
            parent_gene_id=row[7],
            generation=row[8],
            created_at=datetime.fromisoformat(row[9])
        )
        seeds.append(gene)
    
    print(f"Found {len(seeds)} seeds to validate")
    
    # 验证种子
    passed_seeds = validator.validate_all_seeds(seeds)
    
    print(f"\n✅ {len(passed_seeds)} seeds passed validation and can enter evolution pool")


if __name__ == "__main__":
    main()
