#!/usr/bin/env python3
"""
QuantClaw Factor Evolution Engine v2 - 带止损和分级筛选
"""

import sys
import random
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Tuple

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from evolution_ecosystem import QuantClawEvolutionHub, Gene
from factor_backtest_validator import FactorValidator


class SmartFactorEvolutionEngine:
    """
    智能因子进化引擎 v2
    
    改进:
    1. 分级通过标准 (Tier 1/2/3)
    2. 添加止损逻辑到策略
    3. 回测验证后优胜劣汰
    4. 自动保存优秀因子
    """
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.hub = QuantClawEvolutionHub(db_path)
        self.validator = FactorValidator(db_path)
        self.generation = 0
        
        # 分级通过标准
        self.passing_criteria = {
            'tier_1': {  # 精英 - 可直接用于实盘
                'min_sharpe': 1.2,
                'max_drawdown': -0.15,
                'min_win_rate': 0.55,
                'min_annual_return': 0.15
            },
            'tier_2': {  # 优秀 - 进入基因池继续进化
                'min_sharpe': 0.8,
                'max_drawdown': -0.25,
                'min_win_rate': 0.50,
                'min_annual_return': 0.10
            },
            'tier_3': {  # 合格 - 保留观察
                'min_sharpe': 0.5,
                'max_drawdown': -0.35,
                'min_win_rate': 0.45,
                'min_annual_return': 0.05
            }
        }
        
    def add_stop_loss_to_strategy(self, gene: Gene, stop_loss: float = 0.05) -> Gene:
        """
        给策略添加止损逻辑
        
        Args:
            gene: 原始基因
            stop_loss: 止损比例 (默认5%)
        """
        # 修改公式添加止损条件
        original_formula = gene.formula
        
        # 添加止损保护
        new_formula = f"({original_formula}) AND (Drawdown < {stop_loss})"
        
        stop_loss_gene = Gene(
            gene_id=f"g_sl_{gene.gene_id}_{int(stop_loss*100)}",
            name=f"{gene.name}_SL{int(stop_loss*100)}",
            description=f"{gene.description} with {int(stop_loss*100)}% stop loss",
            formula=new_formula,
            parameters={**gene.parameters, 'stop_loss': stop_loss},
            source=f"evolution:stop_loss:{gene.gene_id}",
            author="smart_evolution_engine",
            created_at=datetime.now(),
            parent_gene_id=gene.gene_id,
            generation=gene.generation
        )
        
        return stop_loss_gene
    
    def evaluate_with_backtest(self, gene: Gene, symbols: List[str] = None) -> Dict:
        """
        使用真实回测评估基因
        """
        if symbols is None:
            symbols = ['AAPL', 'MSFT']
        
        # 先添加止损逻辑
        sl_gene = self.add_stop_loss_to_strategy(gene, stop_loss=0.05)
        
        # 运行回测验证
        print(f"\n🔬 回测验证: {sl_gene.name}")
        results = self.validator.validate_gene(sl_gene, symbols=symbols)
        
        if not results:
            return {'tier': 'failed', 'score': 0, 'results': []}
        
        # 计算平均表现
        avg_sharpe = sum(r.sharpe_ratio for r in results) / len(results)
        avg_drawdown = sum(r.max_drawdown for r in results) / len(results)
        avg_return = sum(r.annual_return for r in results) / len(results)
        avg_win_rate = sum(r.win_rate for r in results) / len(results)
        
        # 分级评估
        tier = self._classify_tier(avg_sharpe, avg_drawdown, avg_win_rate, avg_return)
        
        score = (
            avg_sharpe * 30 +
            (1 - abs(avg_drawdown) / 0.5) * 25 +
            avg_win_rate * 20 +
            max(avg_return, 0) / 0.5 * 25
        )
        
        return {
            'tier': tier,
            'score': score,
            'avg_sharpe': avg_sharpe,
            'avg_drawdown': avg_drawdown,
            'avg_return': avg_return,
            'avg_win_rate': avg_win_rate,
            'results': results,
            'gene': sl_gene
        }
    
    def _classify_tier(self, sharpe: float, drawdown: float, 
                       win_rate: float, annual_return: float) -> str:
        """分级分类"""
        t1 = self.passing_criteria['tier_1']
        t2 = self.passing_criteria['tier_2']
        
        if (sharpe >= t1['min_sharpe'] and 
            drawdown >= t1['max_drawdown'] and
            win_rate >= t1['min_win_rate'] and
            annual_return >= t1['min_annual_return']):
            return 'tier_1'
        
        elif (sharpe >= t2['min_sharpe'] and 
              drawdown >= t2['max_drawdown'] and
              win_rate >= t2['min_win_rate'] and
              annual_return >= t2['min_annual_return']):
            return 'tier_2'
        
        else:
            return 'tier_3'
    
    def evolve_generation_v2(self, population_size: int = 10) -> Dict[str, List[Gene]]:
        """进化一代 (v2版本)"""
        print(f"\n🧬 Generation {self.generation} Smart Evolution")
        print("=" * 70)
        
        # 加载当前基因池
        current_genes = self.load_gene_pool()
        print(f"   Current pool: {len(current_genes)} genes")
        
        if len(current_genes) < 2:
            print("   ⚠️ Not enough genes for evolution")
            return {'tier_1': [], 'tier_2': [], 'tier_3': [], 'failed': []}
        
        # 选择精英
        scored_genes = [(g, self.quick_fitness(g)) for g in current_genes]
        scored_genes.sort(key=lambda x: x[1], reverse=True)
        
        elites = [g for g, _ in scored_genes[:max(2, len(scored_genes)//3)]]
        
        # 生成新后代
        new_genes = []
        for _ in range(population_size // 2):
            parents = random.sample(elites, 2)
            child = self.crossover(parents[0], parents[1])
            new_genes.append(child)
        
        for _ in range(population_size // 2):
            parent = random.choice(elites)
            child = self.mutate(parent)
            new_genes.append(child)
        
        # 回测验证每个新基因
        print("\n📊 开始回测验证...")
        tiered_results = {'tier_1': [], 'tier_2': [], 'tier_3': [], 'failed': []}
        
        for gene in new_genes:
            eval_result = self.evaluate_with_backtest(gene)
            tier = eval_result['tier']
            
            if tier in tiered_results:
                tiered_results[tier].append(eval_result['gene'])
                print(f"   ✅ {gene.name} → {tier} (score: {eval_result['score']:.1f})")
            else:
                tiered_results['failed'].append(gene)
                print(f"   ❌ {gene.name} → failed")
        
        # 保存通过验证的基因
        for tier, genes in tiered_results.items():
            if tier != 'failed':
                for gene in genes:
                    self.hub.publish_gene(gene)
        
        self.generation += 1
        
        # 报告
        print(f"\n📈 Generation {self.generation} Results:")
        print(f"   Tier 1 (Elite): {len(tiered_results['tier_1'])}")
        print(f"   Tier 2 (Good): {len(tiered_results['tier_2'])}")
        print(f"   Tier 3 (OK): {len(tiered_results['tier_3'])}")
        print(f"   Failed: {len(tiered_results['failed'])}")
        
        return tiered_results
    
    def quick_fitness(self, gene: Gene) -> float:
        """快速适应度评估 (用于精英选择)"""
        score = 50.0
        
        # 复杂度
        complexity = len(gene.formula.split())
        if 3 <= complexity <= 10:
            score += 10
        
        # 组合创新
        if 'AND' in gene.formula or 'OR' in gene.formula:
            score += 15
        
        # 跨域创新
        academic_terms = ['SampEn', 'Hurst', 'PermEn', 'Fractal']
        tech_terms = ['RSI', 'MACD', 'BB', 'MA']
        has_academic = any(t in gene.formula for t in academic_terms)
        has_tech = any(t in gene.formula for t in tech_terms)
        if has_academic and has_tech:
            score += 20
        
        # 代数奖励
        score += gene.generation * 2
        
        return max(0, min(100, score + random.gauss(0, 5)))
    
    def crossover(self, parent1: Gene, parent2: Gene) -> Gene:
        """交叉操作"""
        operator = random.choice(['AND', 'OR'])
        new_formula = f"({parent1.formula}) {operator} ({parent2.formula})"
        new_name = f"{parent1.name}_{operator}_{parent2.name}"[:50]
        
        child = Gene(
            gene_id=f"g_{hashlib.sha256(new_formula.encode()).hexdigest()[:8]}",
            name=new_name,
            description=f"Crossover of {parent1.name} and {parent2.name}",
            formula=new_formula,
            parameters={**parent1.parameters, **parent2.parameters},
            source=f"evolution:crossover:{parent1.gene_id}+{parent2.gene_id}",
            author="smart_evolution_engine",
            created_at=datetime.now(),
            parent_gene_id=f"{parent1.gene_id}+{parent2.gene_id}",
            generation=max(parent1.generation, parent2.generation) + 1
        )
        return child
    
    def mutate(self, parent: Gene) -> Gene:
        """变异操作"""
        mutation_type = random.choice(['param', 'formula', 'structure'])
        
        if mutation_type == 'param':
            new_params = parent.parameters.copy()
            if new_params:
                param_to_mutate = random.choice(list(new_params.keys()))
                if isinstance(new_params[param_to_mutate], (int, float)):
                    new_params[param_to_mutate] *= random.uniform(0.8, 1.2)
            new_formula = parent.formula
            new_name = f"{parent.name}_M{random.randint(1,99)}"
            
        elif mutation_type == 'formula':
            modifier = random.choice(['ZSCORE(', 'Rank(', 'Decay('])
            new_formula = f"{modifier}{parent.formula})"
            new_name = f"{parent.name}_Mod"
            new_params = parent.parameters.copy()
            
        else:
            offset = random.choice([1, 2, 3])
            new_formula = f"Delay({parent.formula}, {offset})"
            new_name = f"{parent.name}_Lag{offset}"
            new_params = {**parent.parameters, 'lag': offset}
        
        child = Gene(
            gene_id=f"g_{hashlib.sha256(new_formula.encode()).hexdigest()[:8]}",
            name=new_name[:50],
            description=f"Mutation of {parent.name} ({mutation_type})",
            formula=new_formula,
            parameters=new_params if 'new_params' in dir() else parent.parameters.copy(),
            source=f"evolution:mutation:{parent.gene_id}",
            author="smart_evolution_engine",
            created_at=datetime.now(),
            parent_gene_id=parent.gene_id,
            generation=parent.generation + 1
        )
        return child
    
    def load_gene_pool(self) -> List[Gene]:
        """加载基因池"""
        import sqlite3
        conn = sqlite3.connect(self.hub.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM genes')
        rows = cursor.fetchall()
        conn.close()
        
        genes = []
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
            genes.append(gene)
        return genes
    
    def run_smart_evolution(self, generations: int = 3, population_size: int = 6):
        """运行智能进化"""
        print("=" * 70)
        print("🚀 QuantClaw Smart Factor Evolution Engine v2")
        print("=" * 70)
        print(f"   Target: {generations} generations")
        print(f"   Population: {population_size} per generation")
        print(f"   With: Stop-loss protection + Tier-based selection")
        print()
        
        all_results = {'tier_1': [], 'tier_2': [], 'tier_3': [], 'failed': []}
        
        for gen in range(generations):
            results = self.evolve_generation_v2(population_size)
            for tier, genes in results.items():
                all_results[tier].extend(genes)
            print()
        
        print("=" * 70)
        print("🎉 Smart Evolution Complete!")
        print("=" * 70)
        print(f"   Tier 1 (Elite): {len(all_results['tier_1'])}")
        print(f"   Tier 2 (Good): {len(all_results['tier_2'])}")
        print(f"   Tier 3 (OK): {len(all_results['tier_3'])}")
        print(f"   Failed: {len(all_results['failed'])}")
        print()
        
        if all_results['tier_1']:
            print("🏆 Elite Genes:")
            for g in all_results['tier_1'][:3]:
                print(f"   - {g.name}: {g.formula[:50]}")
        
        return all_results


def main():
    """主函数"""
    engine = SmartFactorEvolutionEngine()
    engine.validator.connect()  # 连接数据
    
    try:
        results = engine.run_smart_evolution(generations=2, population_size=6)
    finally:
        engine.validator.disconnect()


if __name__ == "__main__":
    main()
