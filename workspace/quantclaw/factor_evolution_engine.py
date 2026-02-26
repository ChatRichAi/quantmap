#!/usr/bin/env python3
"""
QuantClaw Factor Evolution Engine
因子自动进化引擎 - 运行遗传编程生成新因子
"""

import sys
import random
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Tuple

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from evolution_ecosystem import QuantClawEvolutionHub, Gene, TaskStatus


class FactorEvolutionEngine:
    """
    因子进化引擎
    
    使用遗传编程原理:
    1. 选择: 从基因池选择优秀父代
    2. 交叉: 组合两个父代基因
    3. 变异: 随机修改参数或算子
    4. 评估: 计算适应度
    5. 迭代: 保留优秀后代进入下一代
    """
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.hub = QuantClawEvolutionHub(db_path)
        self.generation = 0
        
        # 进化算子
        self.operators = ['AND', 'OR', 'NOT', '>', '<', '==', '+', '-', '*', '/']
        self.parameters_pool = {
            'period': [5, 10, 14, 20, 21, 50, 100, 200],
            'threshold': [20, 25, 30, 35, 70, 75, 80],
            'std': [1.5, 2.0, 2.5, 3.0],
            'm': [2, 3, 4],
            'r': [0.1, 0.15, 0.2, 0.25, 0.3],
            'order': [2, 3, 4, 5],
            'delay': [1, 2, 3]
        }
        
    def load_gene_pool(self) -> List[Gene]:
        """加载当前基因池中的所有基因"""
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
    
    def _extract_name_core(self, name: str) -> str:
        """提取名称核心部分"""
        for suffix in ['_Mod', '_Lag', '_G', '_M', '∧', '∨', '_Enhanced', '_Variant']:
            if suffix in name:
                name = name.split(suffix)[0]
        return name[:8].rstrip('_')
    
    def crossover(self, parent1: Gene, parent2: Gene) -> Gene:
        """交叉操作 - 组合两个父代基因"""
        cross_type = random.choice(['formula_combine', 'param_merge', 'operator_swap'])
        gen = max(parent1.generation, parent2.generation) + 1
        p1_core = self._extract_name_core(parent1.name)
        p2_core = self._extract_name_core(parent2.name)
        
        if cross_type == 'formula_combine':
            operator = random.choice(['AND', 'OR'])
            new_formula = f"({parent1.formula}) {operator} ({parent2.formula})"
            op_abbr = '∧' if operator == 'AND' else '∨'
            new_name = f"{p1_core}{op_abbr}{p2_core}_G{gen}"
            
        elif cross_type == 'param_merge':
            new_formula = parent1.formula
            new_params = {**parent1.parameters, **parent2.parameters}
            new_params = {k: v for k, v in new_params.items() if k in parent1.parameters}
            parent1.parameters = new_params
            new_name = f"{p1_core}⊕{p2_core}_G{gen}"  # ⊕ = merge
            
        else:  # operator_swap
            new_formula = parent1.formula.replace('<', '>').replace('AND', 'OR') if random.random() > 0.5 else parent1.formula
            new_name = f"{p1_core}↔_G{gen}"  # ↔ = swap
        
        child = Gene(
            gene_id=f"g_{hashlib.sha256(new_formula.encode()).hexdigest()[:8]}",
            name=new_name[:40],
            description=f"Crossover of {parent1.name} and {parent2.name}",
            formula=new_formula,
            parameters=parent1.parameters.copy(),
            source=f"evolution:crossover:{parent1.gene_id}+{parent2.gene_id}",
            author="evolution_engine",
            created_at=datetime.now(),
            parent_gene_id=f"{parent1.gene_id}+{parent2.gene_id}",
            generation=max(parent1.generation, parent2.generation) + 1
        )
        return child
    
    def mutate(self, parent: Gene) -> Gene:
        """变异操作 - 修改父代基因"""
        mutation_type = random.choice(['param', 'formula', 'structure'])
        gen = parent.generation + 1
        parent_core = self._extract_name_core(parent.name)
        
        if mutation_type == 'param':
            new_params = parent.parameters.copy()
            if new_params:
                param_to_mutate = random.choice(list(new_params.keys()))
                if param_to_mutate in self.parameters_pool:
                    new_params[param_to_mutate] = random.choice(self.parameters_pool[param_to_mutate])
            
            new_formula = parent.formula
            import re
            for key, val in new_params.items():
                new_formula = re.sub(rf'{key}=\d+\.?\d*', f'{key}={val}', new_formula)
                new_formula = re.sub(rf'{key}=\d+', f'{key}={val}', new_formula)
            
            new_name = f"{parent_core}·p_G{gen}"
            
        elif mutation_type == 'formula':
            modifier = random.choice([
                'MA(', 'EMA(', 'STD(', 'ZSCORE(',
                'Rank(', 'Decay(', 'SignedPower('
            ])
            modifier_abbr = {'MA(': 'Ma', 'EMA(': 'Em', 'STD(': 'Sd', 'ZSCORE(': 'Z',
                           'Rank(': 'Rk', 'Decay(': 'Dc', 'SignedPower(': 'Sp'}
            new_formula = f"{modifier}{parent.formula})"
            new_name = f"{parent_core}·{modifier_abbr[modifier]}_G{gen}"
            new_params = parent.parameters.copy()
            
        else:  # structure
            offset = random.choice([1, 2, 3, 5])
            new_formula = f"Delay({parent.formula}, {offset})"
            new_name = f"{parent_core}·L{offset}_G{gen}"
            new_params = {**parent.parameters, 'lag': offset}
        
        child = Gene(
            gene_id=f"g_{hashlib.sha256(new_formula.encode()).hexdigest()[:8]}",
            name=new_name[:40],
            description=f"Mutation of {parent.name} ({mutation_type})",
            formula=new_formula,
            parameters=new_params if 'new_params' in dir() else parent.parameters.copy(),
            source=f"evolution:mutation:{parent.gene_id}",
            author="evolution_engine",
            created_at=datetime.now(),
            parent_gene_id=parent.gene_id,
            generation=parent.generation + 1
        )
        return child
    
    def evaluate_fitness(self, gene: Gene) -> float:
        """
        评估基因适应度 (模拟)
        实际应运行回测，这里使用启发式评分
        """
        score = 50.0  # 基础分
        
        # 公式复杂度加分 (适度复杂)
        complexity = len(gene.formula.split())
        if 3 <= complexity <= 10:
            score += 10
        
        # 多因子组合加分
        if 'AND' in gene.formula or 'OR' in gene.formula:
            score += 15
        
        # 跨域组合加分 (学术特征 + 技术指标)
        academic_terms = ['SampEn', 'Hurst', 'PermEn', 'Fractal']
        tech_terms = ['RSI', 'MACD', 'BB', 'MA', 'EMA']
        has_academic = any(term in gene.formula for term in academic_terms)
        has_tech = any(term in gene.formula for term in tech_terms)
        if has_academic and has_tech:
            score += 20  # 跨域创新
        
        # 代数奖励 (新基因有探索奖励)
        score += gene.generation * 2
        
        # 随机噪声 (模拟真实回测波动)
        score += random.gauss(0, 10)
        
        return max(0, min(100, score))
    
    def evolve_generation(self, population_size: int = 10) -> List[Gene]:
        """进化一代"""
        print(f"\n🧬 Generation {self.generation} Evolution")
        print("-" * 60)
        
        # 加载当前基因池
        current_genes = self.load_gene_pool()
        print(f"   Current pool: {len(current_genes)} genes")
        
        if len(current_genes) < 2:
            print("   ⚠️ Not enough genes for evolution")
            return []
        
        # 评估适应度
        scored_genes = [(g, self.evaluate_fitness(g)) for g in current_genes]
        scored_genes.sort(key=lambda x: x[1], reverse=True)
        
        print(f"   Top fitness: {scored_genes[0][1]:.1f} ({scored_genes[0][0].name})")
        
        # 选择精英 (前30%)
        elite_count = max(2, len(scored_genes) // 3)
        elites = [g for g, _ in scored_genes[:elite_count]]
        
        # 生成新后代
        new_genes = []
        
        # 交叉产生后代
        for _ in range(population_size // 2):
            parents = random.sample(elites, 2)
            child = self.crossover(parents[0], parents[1])
            fitness = self.evaluate_fitness(child)
            if fitness > 60:  # 只有高适应度才保留
                new_genes.append((child, fitness))
                print(f"   ✚ Crossover: {child.name} (fitness: {fitness:.1f})")
        
        # 变异产生后代
        for _ in range(population_size // 2):
            parent = random.choice(elites)
            child = self.mutate(parent)
            fitness = self.evaluate_fitness(child)
            if fitness > 60:
                new_genes.append((child, fitness))
                print(f"   ✚ Mutation: {child.name} (fitness: {fitness:.1f})")
        
        # 发布新基因到基因池
        published = []
        for gene, fitness in new_genes:
            # 检查是否已存在
            existing = [g for g in current_genes if g.formula == gene.formula]
            if not existing:
                self.hub.publish_gene(gene)
                published.append(gene)
        
        self.generation += 1
        print(f"\n   ✅ Published {len(published)} new genes")
        print(f"   📊 Total pool: {len(current_genes) + len(published)} genes")
        
        return published
    
    def run_evolution(self, generations: int = 5, population_size: int = 10):
        """运行多代进化"""
        print("=" * 80)
        print("🚀 QuantClaw Factor Evolution Engine")
        print("=" * 80)
        print(f"   Target: {generations} generations")
        print(f"   Population: {population_size} per generation")
        print()
        
        all_new_genes = []
        for gen in range(generations):
            new_genes = self.evolve_generation(population_size)
            all_new_genes.extend(new_genes)
            print()
        
        print("=" * 80)
        print(f"🎉 Evolution Complete!")
        print(f"   Total new genes: {len(all_new_genes)}")
        print(f"   Final pool size: {len(self.load_gene_pool())}")
        print("=" * 80)
        
        return all_new_genes


def main():
    """主函数 - 运行因子进化"""
    engine = FactorEvolutionEngine()
    
    # 运行5代进化，每代生成10个新基因
    new_genes = engine.run_evolution(generations=5, population_size=10)
    
    # 显示优秀基因
    print("\n🏆 Top New Genes:")
    print("-" * 80)
    for i, gene in enumerate(new_genes[:10], 1):
        print(f"{i}. {gene.name}")
        print(f"   Formula: {gene.formula}")
        print(f"   Gen: {gene.generation} | Parent: {gene.parent_gene_id}")
        print()


if __name__ == "__main__":
    main()
