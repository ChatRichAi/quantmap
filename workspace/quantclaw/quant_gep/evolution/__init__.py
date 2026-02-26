"""
Quant-GEP Evolution - GEP 进化算法主实现
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from ..core.gene_ast import GeneExpression, IndicatorType, IndicatorNode
from ..operators import (
    GEPConfig, PointMutation, SubtreeMutation,
    OnePointCrossover, TranspositionOperator, InversionOperator,
    SelectionOperator, RandomTreeGenerator
)


@dataclass
class FitnessResult:
    """适应度评估结果"""
    fitness: float
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    annual_return: float = 0.0
    win_rate: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass  
class EvolutionStats:
    """进化统计"""
    generation: int
    best_fitness: float
    avg_fitness: float
    worst_fitness: float
    diversity: float  # 种群多样性指数
    best_gene: Optional[GeneExpression] = None


class GEPAlgorithm:
    """
    标准 GEP 进化算法
    
    实现完整的基因表达式编程进化流程
    """
    
    def __init__(self, config: Optional[GEPConfig] = None):
        self.config = config or GEPConfig()
        
        # 初始化算子
        self.point_mutation = PointMutation(self.config)
        self.subtree_mutation = SubtreeMutation(self.config)
        self.crossover = OnePointCrossover(self.config)
        self.transposition = TranspositionOperator(self.config)
        self.inversion = InversionOperator(self.config)
        self.selection = SelectionOperator(self.config)
        self.generator = RandomTreeGenerator()
        
        # 统计信息
        self.stats_history: List[EvolutionStats] = []
        self.best_individuals: List[GeneExpression] = []
    
    def evolve(
        self,
        population: List[GeneExpression],
        fitness_fn: Callable[[GeneExpression], FitnessResult],
        generations: int = 50,
        target_fitness: Optional[float] = None,
        callback: Optional[Callable[[EvolutionStats], None]] = None
    ) -> Tuple[List[GeneExpression], List[EvolutionStats]]:
        """
        执行进化
        
        Args:
            population: 初始种群
            fitness_fn: 适应度评估函数
            generations: 进化代数
            target_fitness: 目标适应度 (达到则提前停止)
            callback: 每代回调函数
        
        Returns:
            (最终种群, 统计历史)
        """
        current_pop = [g.clone() for g in population]
        
        for gen in range(generations):
            # 评估适应度
            fitness_results = [fitness_fn(g) for g in current_pop]
            fitness_scores = [r.fitness for r in fitness_results]
            
            # 记录统计
            stats = self._compute_stats(gen, current_pop, fitness_scores, fitness_results)
            self.stats_history.append(stats)
            
            # 回调
            if callback:
                callback(stats)
            
            # 检查终止条件
            if target_fitness and stats.best_fitness >= target_fitness:
                print(f"Target fitness reached at generation {gen}")
                break
            
            # 生成新一代
            current_pop = self._create_next_generation(
                current_pop, fitness_scores, fitness_results
            )
        
        # 最终评估
        final_fitness = [fitness_fn(g).fitness for g in current_pop]
        final_stats = self._compute_stats(
            generations, current_pop, final_fitness,
            [fitness_fn(g) for g in current_pop]
        )
        self.stats_history.append(final_stats)
        
        return current_pop, self.stats_history
    
    def _create_next_generation(
        self,
        population: List[GeneExpression],
        fitness_scores: List[float],
        fitness_results: List[FitnessResult]
    ) -> List[GeneExpression]:
        """创建下一代"""
        new_population: List[GeneExpression] = []
        pop_size = len(population)
        
        # 1. 精英保留
        elites = self.selection.elitism_selection(
            population, fitness_scores, self.config.elitism_count
        )
        new_population.extend(elites)
        
        # 2. 生成剩余个体
        while len(new_population) < pop_size:
            # 选择父代
            parent1 = self.selection.tournament_selection(population, fitness_scores)
            parent2 = self.selection.tournament_selection(population, fitness_scores)
            
            # 交叉
            child1, child2 = self.crossover.crossover(parent1, parent2)
            
            # 变异
            child1 = self._apply_mutations(child1)
            child2 = self._apply_mutations(child2)
            
            # 添加到新种群
            new_population.append(child1)
            if len(new_population) < pop_size:
                new_population.append(child2)
        
        return new_population[:pop_size]
    
    def _apply_mutations(self, gene: GeneExpression) -> GeneExpression:
        """应用所有变异算子"""
        gene = self.point_mutation.mutate(gene)
        gene = self.subtree_mutation.mutate(gene)
        gene = self.transposition.is_transposition(gene)
        gene = self.transposition.ris_transposition(gene)
        gene = self.inversion.invert(gene)
        return gene
    
    def _compute_stats(
        self,
        generation: int,
        population: List[GeneExpression],
        fitness_scores: List[float],
        fitness_results: List[FitnessResult]
    ) -> EvolutionStats:
        """计算统计信息"""
        best_idx = fitness_scores.index(max(fitness_scores))
        
        return EvolutionStats(
            generation=generation,
            best_fitness=max(fitness_scores),
            avg_fitness=sum(fitness_scores) / len(fitness_scores),
            worst_fitness=min(fitness_scores),
            diversity=self._compute_diversity(population),
            best_gene=population[best_idx].clone()
        )
    
    def _compute_diversity(self, population: List[GeneExpression]) -> float:
        """
        计算种群多样性
        
        基于基因的结构差异
        """
        if len(population) < 2:
            return 0.0
        
        # 计算所有基因对的差异
        differences = []
        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                diff = self._gene_difference(population[i], population[j])
                differences.append(diff)
        
        return sum(differences) / len(differences) if differences else 0.0
    
    def _gene_difference(self, gene1: GeneExpression, gene2: GeneExpression) -> float:
        """计算两个基因的差异度 (0-1)"""
        nodes1 = gene1.root.traverse()
        nodes2 = gene2.root.traverse()
        
        # 基于节点类型的差异
        types1 = [type(n).__name__ for n in nodes1]
        types2 = [type(n).__name__ for n in nodes2]
        
        # 使用编辑距离或简单比较
        common = sum(1 for t1, t2 in zip(types1, types2) if t1 == t2)
        max_len = max(len(types1), len(types2))
        
        return 1 - (common / max_len) if max_len > 0 else 0.0
    
    def initialize_population(
        self,
        size: int,
        seed_genes: Optional[List[GeneExpression]] = None
    ) -> List[GeneExpression]:
        """
        初始化种群
        
        Args:
            size: 种群大小
            seed_genes: 种子基因 (可选)
        """
        population = []
        
        # 添加种子基因
        if seed_genes:
            population.extend([g.clone() for g in seed_genes])
        
        # 随机生成剩余个体
        while len(population) < size:
            tree = self.generator.generate_tree(
                max_depth=random.randint(3, self.config.max_depth)
            )
            gene = GeneExpression(root=tree)
            population.append(gene)
        
        return population[:size]
    
    def get_convergence_report(self) -> Dict:
        """获取收敛报告"""
        if not self.stats_history:
            return {"error": "No evolution history"}
        
        fitness_trend = [s.best_fitness for s in self.stats_history]
        
        return {
            "total_generations": len(self.stats_history),
            "final_best_fitness": fitness_trend[-1],
            "initial_best_fitness": fitness_trend[0],
            "improvement": fitness_trend[-1] - fitness_trend[0],
            "fitness_trend": fitness_trend,
            "diversity_trend": [s.diversity for s in self.stats_history],
            "converged": self._check_convergence()
        }
    
    def _check_convergence(self, window: int = 10, threshold: float = 0.01) -> bool:
        """检查是否收敛"""
        if len(self.stats_history) < window:
            return False
        
        recent = self.stats_history[-window:]
        fitness_range = max(s.best_fitness for s in recent) - min(s.best_fitness for s in recent)
        
        return fitness_range < threshold


class MultiObjectiveGEP(GEPAlgorithm):
    """
    多目标 GEP
    
    同时优化多个目标 (如收益、风险、稳定性)
    """
    
    def evolve(
        self,
        population: List[GeneExpression],
        fitness_fns: Dict[str, Callable[[GeneExpression], float]],
        generations: int = 50,
        weights: Optional[Dict[str, float]] = None
    ) -> Tuple[List[GeneExpression], List[EvolutionStats]]:
        """
        多目标进化
        
        Args:
            fitness_fns: 多个适应度函数字典
            weights: 目标权重
        """
        if weights is None:
            weights = {k: 1.0 / len(fitness_fns) for k in fitness_fns}
        
        def combined_fitness(gene: GeneExpression) -> FitnessResult:
            scores = {}
            for name, fn in fitness_fns.items():
                scores[name] = fn(gene)
            
            combined = sum(scores[k] * weights.get(k, 1.0) for k in scores)
            
            return FitnessResult(
                fitness=combined,
                metadata=scores
            )
        
        return super().evolve(population, combined_fitness, generations)


# 便捷函数
def quick_evolve(
    seed_gene: GeneExpression,
    fitness_fn: Callable[[GeneExpression], FitnessResult],
    pop_size: int = 50,
    generations: int = 30
) -> Tuple[GeneExpression, List[EvolutionStats]]:
    """
    快速进化一个种子基因
    
    Example:
        >>> best_gene, stats = quick_evolve(
        ...     seed_gene=my_gene,
        ...     fitness_fn=my_fitness,
        ...     pop_size=50,
        ...     generations=30
        ... )
    """
    config = GEPConfig()
    algo = GEPAlgorithm(config)
    
    population = algo.initialize_population(pop_size, [seed_gene])
    final_pop, history = algo.evolve(population, fitness_fn, generations)
    
    # 返回最优个体
    final_fitness = [fitness_fn(g).fitness for g in final_pop]
    best_idx = final_fitness.index(max(final_fitness))
    
    return final_pop[best_idx], history
