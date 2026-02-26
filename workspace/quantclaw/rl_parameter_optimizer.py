#!/usr/bin/env python3
"""
QuantClaw RL Parameter Optimizer
强化学习参数优化器 - 自动优化最佳因子参数

针对 Hurst Exponent (表现最佳: 夏普0.88, 收益28.3%) 进行专项优化
"""

import sys
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple
import random

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from factor_backtest_validator import FactorValidator, BacktestEngine
from evolution_ecosystem import QuantClawEvolutionHub, Gene


class RLParameterOptimizer:
    """
    强化学习参数优化器
    
    使用策略梯度方法优化因子参数
    """
    
    def __init__(self, base_gene: Gene):
        self.base_gene = base_gene
        self.validator = FactorValidator()
        
        # 参数空间
        self.param_space = {
            'period': [50, 100, 150, 200],
            'threshold_long': [0.55, 0.6, 0.65, 0.7],
            'threshold_short': [0.3, 0.35, 0.4, 0.45],
            'stop_loss': [0.03, 0.05, 0.07, 0.10]
        }
        
        # 策略网络 (简化版：参数概率分布)
        self.policy = {k: {v: 1.0/len(vs) for v in vs} 
                       for k, vs in self.param_space.items()}
        
        # 学习率
        self.lr = 0.1
        
    def sample_parameters(self) -> Dict:
        """根据当前策略采样参数"""
        params = {}
        for param_name, probs in self.policy.items():
            values = list(probs.keys())
            probabilities = list(probs.values())
            params[param_name] = np.random.choice(values, p=probabilities)
        return params
    
    def create_variant_gene(self, params: Dict) -> Gene:
        """创建参数变体基因"""
        variant_id = f"{self.base_gene.gene_id}_rl_{hash(str(params)) % 10000}"
        
        # 根据参数修改公式
        formula = f"Hurst(period={params['period']}) > {params['threshold_long']}"
        
        return Gene(
            gene_id=variant_id,
            name=f"{self.base_gene.name}_RL",
            description=f"RL optimized Hurst: period={params['period']}, "
                       f"long={params['threshold_long']}, "
                       f"short={params['threshold_short']}, "
                       f"SL={params['stop_loss']}",
            formula=formula,
            parameters=params,
            source=f"rl_optimization:{self.base_gene.gene_id}",
            author="rl_optimizer",
            created_at=datetime.now(),
            parent_gene_id=self.base_gene.gene_id,
            generation=self.base_gene.generation + 1
        )
    
    def evaluate_variant(self, gene: Gene, symbol: str = 'AAPL') -> Tuple[float, Dict]:
        """评估参数变体"""
        results = self.validator.validate_gene(gene, symbols=[symbol])
        
        if not results:
            return -100, {}
        
        result = results[0]
        
        # 计算奖励 (多目标)
        reward = (
            result.sharpe_ratio * 30 +           # 夏普权重
            (1 - abs(result.max_drawdown) / 0.5) * 25 +  # 回撤控制
            result.win_rate * 20 +                # 胜率
            max(result.annual_return, 0) / 0.5 * 25   # 收益
        )
        
        metrics = {
            'sharpe': result.sharpe_ratio,
            'drawdown': result.max_drawdown,
            'return': result.annual_return,
            'win_rate': result.win_rate
        }
        
        return reward, metrics
    
    def update_policy(self, params: Dict, reward: float):
        """根据奖励更新策略"""
        # 简化版策略梯度：增加高奖励参数的概率
        for param_name, param_value in params.items():
            if reward > 0:
                # 增加该参数的概率
                self.policy[param_name][param_value] += self.lr * reward / 100
                
                # 归一化
                total = sum(self.policy[param_name].values())
                for k in self.policy[param_name]:
                    self.policy[param_name][k] /= total
    
    def optimize(self, iterations: int = 20) -> List[Tuple[Gene, float, Dict]]:
        """
        运行优化
        
        Args:
            iterations: 优化迭代次数
            
        Returns:
            优化后的基因列表 [(gene, reward, metrics), ...]
        """
        print("=" * 70)
        print("🚀 RL Parameter Optimizer")
        print(f"   Target: {self.base_gene.name}")
        print(f"   Iterations: {iterations}")
        print("=" * 70)
        
        self.validator.connect()
        
        best_results = []
        
        try:
            for i in range(iterations):
                print(f"\n📊 Iteration {i+1}/{iterations}")
                
                # 采样参数
                params = self.sample_parameters()
                print(f"   Params: {params}")
                
                # 创建变体
                variant = self.create_variant_gene(params)
                
                # 评估
                reward, metrics = self.evaluate_variant(variant)
                print(f"   Reward: {reward:.2f} | Sharpe: {metrics.get('sharpe', 0):.2f}")
                
                # 保存结果
                best_results.append((variant, reward, metrics))
                
                # 更新策略
                self.update_policy(params, reward)
                
                # 如果表现优秀，保存到基因池
                if reward > 60:
                    hub = QuantClawEvolutionHub()
                    hub.publish_gene(variant)
                    print(f"   ✅ Saved to gene pool!")
            
        finally:
            self.validator.disconnect()
        
        # 排序并返回最佳结果
        best_results.sort(key=lambda x: x[1], reverse=True)
        
        print("\n" + "=" * 70)
        print("🎉 Optimization Complete!")
        print("=" * 70)
        
        # 显示Top 5
        print("\n🏆 Top 5 Variants:")
        for i, (gene, reward, metrics) in enumerate(best_results[:5], 1):
            print(f"{i}. {gene.name}")
            print(f"   Reward: {reward:.2f}")
            print(f"   Sharpe: {metrics.get('sharpe', 0):.2f}")
            print(f"   Return: {metrics.get('return', 0):.1%}")
            print(f"   MaxDD: {metrics.get('drawdown', 0):.1%}")
            print()
        
        return best_results


def main():
    """主函数 - 优化Hurst Exponent"""
    
    # 创建基础Hurst基因
    base_hurst = Gene(
        gene_id='g_hurst_base',
        name='Hurst Exponent Base',
        description='Trend persistence measure',
        formula='Hurst(close, 100)',
        parameters={'period': 100},
        source='optimization_target',
        author='system',
        created_at=datetime.now()
    )
    
    # 运行优化
    optimizer = RLParameterOptimizer(base_hurst)
    results = optimizer.optimize(iterations=15)
    
    # 保存最佳结果到文件
    with open('rl_optimization_results.json', 'w') as f:
        json.dump([{
            'gene_id': g.gene_id,
            'name': g.name,
            'formula': g.formula,
            'parameters': g.parameters,
            'reward': r,
            'metrics': m
        } for g, r, m in results[:10]], f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: rl_optimization_results.json")


if __name__ == "__main__":
    main()
