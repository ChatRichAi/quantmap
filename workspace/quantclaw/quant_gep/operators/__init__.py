"""
Quant-GEP Operators - GEP 进化算子实现

包含:
- Mutation: 单点变异、子树变异
- Crossover: 单点交叉、双点交叉、均匀交叉
- Transposition: IS转位、RIS转位、基因转位
- Selection: 轮盘赌、锦标赛、精英保留
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Type

from ..core.gene_ast import (
    GeneASTNode, GeneExpression, Operator, OperatorNode,
    IndicatorNode, IndicatorType, ConstantNode, VariableNode
)


@dataclass
class GEPConfig:
    """GEP算法配置"""
    # 变异概率
    mutation_rate: float = 0.1
    subtree_mutation_rate: float = 0.05
    
    # 交叉概率
    crossover_rate: float = 0.7
    
    # 转位概率
    is_transposition_rate: float = 0.1
    ris_transposition_rate: float = 0.1
    gene_transposition_rate: float = 0.05
    
    # 反转概率
    inversion_rate: float = 0.1
    
    # 选择参数
    tournament_size: int = 3
    elitism_count: int = 2
    
    # 约束
    max_depth: int = 10
    max_nodes: int = 50


class MutationOperator(ABC):
    """变异算子基类"""
    
    def __init__(self, config: GEPConfig):
        self.config = config
    
    @abstractmethod
    def mutate(self, gene: GeneExpression) -> GeneExpression:
        """执行变异"""
        pass
    
    def _clone_gene(self, gene: GeneExpression) -> GeneExpression:
        """深拷贝基因"""
        return gene.clone()


class PointMutation(MutationOperator):
    """
    单点变异
    
    随机选择一个节点，将其替换为同类型的另一个节点
    """
    
    def mutate(self, gene: GeneExpression) -> GeneExpression:
        if random.random() > self.config.mutation_rate:
            return gene
        
        new_gene = self._clone_gene(gene)
        nodes = new_gene.root.traverse()
        
        if not nodes:
            return gene
        
        # 随机选择一个节点
        target_node = random.choice(nodes)
        
        # 根据节点类型进行变异
        if isinstance(target_node, ConstantNode):
            # 常数变异: 添加随机扰动
            new_value = target_node.value * (1 + random.uniform(-0.2, 0.2))
            mutated = ConstantNode(new_value)
        
        elif isinstance(target_node, VariableNode):
            # 变量变异: 切换到另一个变量
            variables = list(VariableNode.VALID_VARIABLES)
            new_var = random.choice([v for v in variables if v != target_node.name])
            mutated = VariableNode(new_var)
        
        elif isinstance(target_node, IndicatorNode):
            # 指标变异: 改变参数或指标类型
            if random.random() < 0.5 and target_node.parameters:
                # 修改参数
                mutated = target_node.clone()
                for key in mutated.parameters:
                    if isinstance(mutated.parameters[key], (int, float)):
                        mutated.parameters[key] = max(1, int(mutated.parameters[key] * 
                            random.uniform(0.8, 1.2)))
            else:
                # 改变指标类型
                indicators = list(IndicatorType)
                new_indicator = random.choice([i for i in indicators if i != target_node.indicator])
                mutated = IndicatorNode(new_indicator, target_node.parameters.copy())
        
        elif isinstance(target_node, OperatorNode):
            # 运算符变异
            if target_node.operator in [Operator.AND, Operator.OR, Operator.NOT]:
                operators = [Operator.AND, Operator.OR]
                new_op = random.choice([o for o in operators if o != target_node.operator])
                mutated = OperatorNode(new_op)
            elif target_node.operator in [Operator.GT, Operator.LT, Operator.GE, Operator.LE]:
                operators = [Operator.GT, Operator.LT, Operator.GE, Operator.LE]
                new_op = random.choice([o for o in operators if o != target_node.operator])
                mutated = OperatorNode(new_op)
            else:
                return gene
        else:
            return gene
        
        # 替换节点
        if target_node.parent:
            target_node.parent.replace_child(target_node, mutated)
        else:
            # 根节点被替换
            new_gene.root = mutated
        
        new_gene.generation += 1
        return new_gene


class SubtreeMutation(MutationOperator):
    """
    子树变异
    
    随机选择一个节点，将其替换为一棵随机生成的子树
    """
    
    def __init__(self, config: GEPConfig):
        super().__init__(config)
        self.generator = RandomTreeGenerator()
    
    def mutate(self, gene: GeneExpression) -> GeneExpression:
        if random.random() > self.config.subtree_mutation_rate:
            return gene
        
        new_gene = self._clone_gene(gene)
        nodes = new_gene.root.traverse()
        
        if not nodes:
            return gene
        
        # 随机选择一个非根节点进行子树替换
        valid_nodes = [n for n in nodes if n.parent is not None]
        if not valid_nodes:
            return gene
        
        target_node = random.choice(valid_nodes)
        
        # 生成随机子树
        max_depth = max(2, self.config.max_depth - target_node.get_depth())
        new_subtree = self.generator.generate_tree(max_depth=max_depth)
        
        # 替换
        target_node.parent.replace_child(target_node, new_subtree)
        
        new_gene.generation += 1
        return new_gene


class CrossoverOperator(ABC):
    """交叉算子基类"""
    
    def __init__(self, config: GEPConfig):
        self.config = config
    
    @abstractmethod
    def crossover(self, parent1: GeneExpression, parent2: GeneExpression) -> Tuple[GeneExpression, GeneExpression]:
        """执行交叉，返回两个子代"""
        pass


class OnePointCrossover(CrossoverOperator):
    """
    单点交叉
    
    在两个父代的AST中随机选择两个节点，交换以它们为根的子树
    """
    
    def crossover(self, parent1: GeneExpression, parent2: GeneExpression) -> Tuple[GeneExpression, GeneExpression]:
        if random.random() > self.config.crossover_rate:
            return parent1.clone(), parent2.clone()
        
        child1 = parent1.clone()
        child2 = parent2.clone()
        
        # 获取所有可交换的节点 (非根节点)
        nodes1 = [n for n in child1.root.traverse() if n.parent is not None]
        nodes2 = [n for n in child2.root.traverse() if n.parent is not None]
        
        if not nodes1 or not nodes2:
            return child1, child2
        
        # 随机选择交换点
        node1 = random.choice(nodes1)
        node2 = random.choice(nodes2)
        
        # 检查交换后不会超出限制
        if (child1.root.get_node_count() - node1.get_node_count() + node2.get_node_count() > 
            self.config.max_nodes):
            return child1, child2
        
        if (child2.root.get_node_count() - node2.get_node_count() + node1.get_node_count() > 
            self.config.max_nodes):
            return child1, child2
        
        # 获取父节点
        parent1_node = node1.parent
        parent2_node = node2.parent
        
        # 执行交换
        # 先克隆要交换的子树
        subtree1 = node1.clone()
        subtree2 = node2.clone()
        
        # 替换
        parent1_node.replace_child(node1, subtree2)
        parent2_node.replace_child(node2, subtree1)
        
        child1.generation = max(parent1.generation, parent2.generation) + 1
        child2.generation = max(parent1.generation, parent2.generation) + 1
        
        return child1, child2


class UniformCrossover(CrossoverOperator):
    """
    均匀交叉
    
    逐节点比较两个父代，以50%概率选择来自父代1或父代2的节点
    """
    
    def crossover(self, parent1: GeneExpression, parent2: GeneExpression) -> Tuple[GeneExpression, GeneExpression]:
        if random.random() > self.config.crossover_rate:
            return parent1.clone(), parent2.clone()
        
        # 简化为随机选择一个父代的结构，填充另一个父代的节点值
        if random.random() < 0.5:
            structure = parent1.clone()
            values = parent2
        else:
            structure = parent2.clone()
            values = parent1
        
        # 将values中的常数值混合到structure中
        struct_constants = structure.root.find_nodes(lambda n: isinstance(n, ConstantNode))
        value_constants = values.root.find_nodes(lambda n: isinstance(n, ConstantNode))
        
        for i, node in enumerate(struct_constants):
            if i < len(value_constants) and random.random() < 0.5:
                node.value = value_constants[i].value
        
        structure.generation = max(parent1.generation, parent2.generation) + 1
        
        # 返回两个相同的子代 (可以改进为产生不同子代)
        return structure.clone(), structure.clone()


class TranspositionOperator:
    """
    转位算子
    
    模拟生物基因转位现象
    """
    
    def __init__(self, config: GEPConfig):
        self.config = config
    
    def is_transposition(self, gene: GeneExpression) -> GeneExpression:
        """
        IS转位 (Insertion Sequence)
        
        随机选择一段序列，插入到另一个位置
        """
        if random.random() > self.config.is_transposition_rate:
            return gene
        
        new_gene = gene.clone()
        nodes = new_gene.root.traverse()
        
        if len(nodes) < 3:
            return gene
        
        # 随机选择源节点和目标节点
        source = random.choice(nodes)
        target = random.choice([n for n in nodes if n != source])
        
        # 克隆源子树并添加到目标
        cloned = source.clone()
        if len(target.children) < 2:  # 确保不超出arity限制
            target.add_child(cloned)
        
        new_gene.generation += 1
        return new_gene
    
    def ris_transposition(self, gene: GeneExpression) -> GeneExpression:
        """
        RIS转位 (Root Insertion Sequence)
        
        将一段序列插入到根节点附近
        """
        if random.random() > self.config.ris_transposition_rate:
            return gene
        
        new_gene = gene.clone()
        nodes = new_gene.root.traverse()
        
        if len(nodes) < 2:
            return gene
        
        # 选择一个节点提升到根附近
        source = random.choice([n for n in nodes if n.parent is not None])
        
        # 创建新的根运算符
        new_root = OperatorNode(random.choice([Operator.AND, Operator.OR]))
        new_root.add_child(source.clone())
        new_root.add_child(new_gene.root)
        
        new_gene.root = new_root
        new_gene.generation += 1
        
        return new_gene


class InversionOperator:
    """
    反转算子
    
    反转一段基因序列的顺序
    """
    
    def __init__(self, config: GEPConfig):
        self.config = config
    
    def invert(self, gene: GeneExpression) -> GeneExpression:
        if random.random() > self.config.inversion_rate:
            return gene
        
        new_gene = gene.clone()
        
        # 找到有多个子节点的运算符节点
        candidates = [n for n in new_gene.root.traverse() 
                     if isinstance(n, OperatorNode) and len(n.children) >= 2]
        
        if not candidates:
            return gene
        
        target = random.choice(candidates)
        
        # 反转子节点顺序
        target.children.reverse()
        
        new_gene.generation += 1
        return new_gene


class SelectionOperator:
    """选择算子"""
    
    def __init__(self, config: GEPConfig):
        self.config = config
    
    def tournament_selection(
        self, 
        population: List[GeneExpression], 
        fitness_scores: List[float]
    ) -> GeneExpression:
        """
        锦标赛选择
        
        随机选择k个个体，返回其中最优的
        """
        tournament_size = min(self.config.tournament_size, len(population))
        
        selected_indices = random.sample(range(len(population)), tournament_size)
        selected_fitness = [fitness_scores[i] for i in selected_indices]
        
        winner_idx = selected_indices[selected_fitness.index(max(selected_fitness))]
        return population[winner_idx]
    
    def roulette_selection(
        self,
        population: List[GeneExpression],
        fitness_scores: List[float]
    ) -> GeneExpression:
        """
        轮盘赌选择
        
        根据适应度比例选择个体
        """
        total_fitness = sum(fitness_scores)
        if total_fitness == 0:
            return random.choice(population)
        
        pick = random.uniform(0, total_fitness)
        current = 0
        for gene, fitness in zip(population, fitness_scores):
            current += fitness
            if current >= pick:
                return gene
        
        return population[-1]
    
    def elitism_selection(
        self,
        population: List[GeneExpression],
        fitness_scores: List[float],
        count: int
    ) -> List[GeneExpression]:
        """
        精英保留
        
        选择适应度最高的n个个体直接进入下一代
        """
        indexed_scores = list(enumerate(fitness_scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        elite_indices = [idx for idx, _ in indexed_scores[:count]]
        return [population[i].clone() for i in elite_indices]


class RandomTreeGenerator:
    """随机树生成器"""
    
    def __init__(self):
        self.operators = [Operator.AND, Operator.OR, Operator.GT, Operator.LT]
        self.indicators = [IndicatorType.SMA, IndicatorType.RSI, IndicatorType.ATR]
        self.variables = ["close", "volume"]
    
    def generate_tree(self, max_depth: int = 5, current_depth: int = 0) -> GeneASTNode:
        """递归生成随机树"""
        
        # 达到一定深度后生成叶节点
        if current_depth >= max_depth - 1:
            return self._generate_terminal()
        
        # 随机选择节点类型
        r = random.random()
        
        if r < 0.3:  # 运算符
            op = random.choice(self.operators)
            node = OperatorNode(op)
            arity = 1 if op == Operator.NOT else 2
            for _ in range(arity):
                child = self.generate_tree(max_depth, current_depth + 1)
                node.add_child(child)
            return node
        
        elif r < 0.6:  # 指标
            indicator = random.choice(self.indicators)
            period = random.choice([5, 10, 14, 20, 50])
            return IndicatorNode(indicator, {"period": period})
        
        else:  # 变量或常数
            return self._generate_terminal()
    
    def _generate_terminal(self) -> GeneASTNode:
        """生成叶节点"""
        if random.random() < 0.5:
            return VariableNode(random.choice(self.variables))
        else:
            return ConstantNode(random.uniform(-100, 100))


# 便捷函数
def apply_all_mutations(gene: GeneExpression, config: GEPConfig) -> GeneExpression:
    """应用所有变异算子"""
    point_mut = PointMutation(config)
    subtree_mut = SubtreeMutation(config)
    
    gene = point_mut.mutate(gene)
    gene = subtree_mut.mutate(gene)
    
    return gene


def apply_all_crossovers(
    parent1: GeneExpression,
    parent2: GeneExpression,
    config: GEPConfig
) -> Tuple[GeneExpression, GeneExpression]:
    """应用所有交叉算子"""
    one_point = OnePointCrossover(config)
    return one_point.crossover(parent1, parent2)
