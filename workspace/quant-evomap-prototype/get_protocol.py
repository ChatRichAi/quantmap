"""
GET Protocol v1.0 - Gene Expression Trading Protocol
基因表达交易协议 - 策略基因编码规范
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import json
import hashlib
from datetime import datetime


class GeneType(Enum):
    """基因类型"""
    SIGNAL = "signal"           # 信号生成基因
    POSITION = "position"       # 仓位管理基因
    RISK = "risk"              # 风险控制基因
    COMBINATION = "combination" # 策略组合基因


class MarketRegime(Enum):
    """市场状态"""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    BREAKOUT = "breakout"
    ANY = "any"


@dataclass
class GeneExpression:
    """基因表达式 - 树形结构"""
    node_type: str  # 'operator', 'terminal', 'constant'
    
    # 操作符节点
    operator: Optional[str] = None  # add, sub, mul, div, gt, lt, if, etc.
    operands: List['GeneExpression'] = field(default_factory=list)
    
    # 终端节点
    terminal: Optional[str] = None  # close, volume, rsi, etc.
    transform: Optional[str] = None  # sma, ema, std, etc.
    period: Optional[int] = None
    
    # 常数节点
    constant: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        result = {'node_type': self.node_type}
        
        if self.node_type == 'operator':
            result['operator'] = self.operator
            result['operands'] = [op.to_dict() for op in self.operands]
        elif self.node_type == 'terminal':
            result['terminal'] = self.terminal
            result['transform'] = self.transform
            result['period'] = self.period
        elif self.node_type == 'constant':
            result['constant'] = self.constant
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'GeneExpression':
        """从字典创建"""
        expr = cls(node_type=data['node_type'])
        
        if expr.node_type == 'operator':
            expr.operator = data['operator']
            expr.operands = [cls.from_dict(op) for op in data['operands']]
        elif expr.node_type == 'terminal':
            expr.terminal = data['terminal']
            expr.transform = data.get('transform')
            expr.period = data.get('period')
        elif expr.node_type == 'constant':
            expr.constant = data['constant']
        
        return expr
    
    def to_code(self) -> str:
        """转换为 Python 代码"""
        if self.node_type == 'constant':
            return str(self.constant)
        
        elif self.node_type == 'terminal':
            if self.transform:
                return f"{self.transform}(data['{self.terminal}'], {self.period})"
            else:
                return f"data['{self.terminal}']"
        
        elif self.node_type == 'operator':
            ops = {
                'add': '+', 'sub': '-', 'mul': '*', 'div': '/',
                'gt': '>', 'lt': '<', 'gte': '>=', 'lte': '<=',
                'eq': '==', 'and': 'and', 'or': 'or'
            }
            
            if self.operator in ['add', 'sub', 'mul', 'div', 'gt', 'lt']:
                op_str = ops.get(self.operator, self.operator)
                return f"({self.operands[0].to_code()} {op_str} {self.operands[1].to_code()})"
            
            elif self.operator == 'if':
                return f"({self.operands[1].to_code()} if {self.operands[0].to_code()} else {self.operands[2].to_code()})"
            
            elif self.operator in ['abs', 'sqrt', 'log', 'exp']:
                return f"{self.operator}({self.operands[0].to_code()})"
            
            else:
                return f"{self.operator}({', '.join(op.to_code() for op in self.operands)})"
        
        return ""


@dataclass
class EvolvableParameter:
    """可进化参数"""
    name: str
    value: float
    min_value: float
    max_value: float
    mutation_rate: float = 0.1
    
    def mutate(self) -> 'EvolvableParameter':
        """变异"""
        import random
        if random.random() < self.mutation_rate:
            # 高斯变异
            new_value = self.value + random.gauss(0, (self.max_value - self.min_value) * 0.1)
            new_value = max(self.min_value, min(self.max_value, new_value))
            return EvolvableParameter(
                name=self.name,
                value=new_value,
                min_value=self.min_value,
                max_value=self.max_value,
                mutation_rate=self.mutation_rate
            )
        return self
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'value': self.value,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'mutation_rate': self.mutation_rate
        }


@dataclass
class StrategyGene:
    """
    策略基因 - GET Protocol 核心数据结构
    """
    # 元数据
    id: str = field(default_factory=lambda: StrategyGene._generate_id())
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    author: str = "anonymous"
    
    # 基因类型
    gene_type: GeneType = GeneType.SIGNAL
    
    # 基因型 - 可进化的编码
    genotype: Dict[str, Any] = field(default_factory=dict)
    
    # 表现型 - 执行参数
    parameters: Dict[str, EvolvableParameter] = field(default_factory=dict)
    
    # 适用条件
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # 验证记录
    validation: Dict[str, Any] = field(default_factory=lambda: {
        'status': 'pending',
        'validators': [],
        'results': []
    })
    
    # 表现统计
    performance: Dict[str, float] = field(default_factory=dict)
    
    # 血统追踪
    lineage: Dict[str, Any] = field(default_factory=lambda: {
        'generation': 0,
        'parents': [],
        'mutations': []
    })
    
    @staticmethod
    def _generate_id() -> str:
        """生成唯一ID"""
        import uuid
        return f"gene_{uuid.uuid4().hex[:12]}"
    
    def get_hash(self) -> str:
        """获取基因哈希"""
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            'id': self.id,
            'version': self.version,
            'created_at': self.created_at,
            'author': self.author,
            'gene_type': self.gene_type.value,
            'genotype': self.genotype,
            'parameters': {k: v.to_dict() for k, v in self.parameters.items()},
            'conditions': self.conditions,
            'validation': self.validation,
            'performance': self.performance,
            'lineage': self.lineage
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyGene':
        """从字典反序列化"""
        gene = cls(
            id=data['id'],
            version=data.get('version', '1.0.0'),
            created_at=data['created_at'],
            author=data.get('author', 'anonymous'),
            gene_type=GeneType(data.get('gene_type', 'signal')),
            genotype=data.get('genotype', {}),
            conditions=data.get('conditions', {}),
            validation=data.get('validation', {'status': 'pending', 'validators': [], 'results': []}),
            performance=data.get('performance', {}),
            lineage=data.get('lineage', {'generation': 0, 'parents': [], 'mutations': []})
        )
        
        # 解析参数
        gene.parameters = {
            k: EvolvableParameter(**v) 
            for k, v in data.get('parameters', {}).items()
        }
        
        return gene
    
    def to_json(self) -> str:
        """序列化为 JSON"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'StrategyGene':
        """从 JSON 反序列化"""
        return cls.from_dict(json.loads(json_str))
    
    def mutate(self, mutation_rate: float = 0.1) -> 'StrategyGene':
        """基因变异"""
        import copy
        import random
        
        new_gene = copy.deepcopy(self)
        new_gene.id = StrategyGene._generate_id()
        new_gene.lineage['parents'] = [self.id]
        new_gene.lineage['generation'] = self.lineage['generation'] + 1
        
        mutations = []
        
        # 参数变异
        for name, param in new_gene.parameters.items():
            if random.random() < mutation_rate:
                old_value = param.value
                new_gene.parameters[name] = param.mutate()
                mutations.append({
                    'type': 'parameter',
                    'name': name,
                    'from': old_value,
                    'to': new_gene.parameters[name].value
                })
        
        new_gene.lineage['mutations'] = mutations
        return new_gene
    
    def crossover(self, other: 'StrategyGene') -> 'StrategyGene':
        """基因交叉"""
        import copy
        import random
        
        new_gene = copy.deepcopy(self)
        new_gene.id = StrategyGene._generate_id()
        new_gene.lineage['parents'] = [self.id, other.id]
        new_gene.lineage['generation'] = max(
            self.lineage['generation'], 
            other.lineage['generation']
        ) + 1
        
        # 参数交叉
        for name in new_gene.parameters:
            if name in other.parameters and random.random() < 0.5:
                new_gene.parameters[name] = copy.deepcopy(other.parameters[name])
        
        new_gene.lineage['mutations'] = [{'type': 'crossover', 'parents': [self.id, other.id]}]
        return new_gene


# 预定义基因模板
class GeneTemplates:
    """基因模板库"""
    
    @staticmethod
    def momentum_gene() -> StrategyGene:
        """动量基因模板"""
        return StrategyGene(
            gene_type=GeneType.SIGNAL,
            genotype={
                'expression': {
                    'node_type': 'operator',
                    'operator': 'gt',
                    'operands': [
                        {
                            'node_type': 'terminal',
                            'terminal': 'close',
                            'transform': 'momentum',
                            'period': 20
                        },
                        {
                            'node_type': 'constant',
                            'constant': 0.0
                        }
                    ]
                }
            },
            parameters={
                'momentum_period': EvolvableParameter('momentum_period', 20, 5, 60),
                'entry_threshold': EvolvableParameter('entry_threshold', 0.02, 0.001, 0.1),
                'position_size': EvolvableParameter('position_size', 0.1, 0.01, 0.5),
                'stop_loss': EvolvableParameter('stop_loss', 0.05, 0.01, 0.2)
            },
            conditions={
                'market_regime': [MarketRegime.TRENDING_UP.value, MarketRegime.TRENDING_DOWN.value],
                'min_volatility': 0.15,
                'max_volatility': 0.5
            }
        )
    
    @staticmethod
    def mean_reversion_gene() -> StrategyGene:
        """均值回归基因模板"""
        return StrategyGene(
            gene_type=GeneType.SIGNAL,
            genotype={
                'expression': {
                    'node_type': 'operator',
                    'operator': 'lt',
                    'operands': [
                        {
                            'node_type': 'terminal',
                            'terminal': 'rsi',
                            'period': 14
                        },
                        {
                            'node_type': 'constant',
                            'constant': 30.0
                        }
                    ]
                }
            },
            parameters={
                'rsi_period': EvolvableParameter('rsi_period', 14, 5, 30),
                'oversold': EvolvableParameter('oversold', 30, 10, 40),
                'overbought': EvolvableParameter('overbought', 70, 60, 90),
                'position_size': EvolvableParameter('position_size', 0.1, 0.01, 0.5)
            },
            conditions={
                'market_regime': [MarketRegime.RANGING.value],
                'min_volatility': 0.1,
                'max_volatility': 0.3
            }
        )
    
    @staticmethod
    def breakout_gene() -> StrategyGene:
        """突破基因模板"""
        return StrategyGene(
            gene_type=GeneType.SIGNAL,
            genotype={
                'expression': {
                    'node_type': 'operator',
                    'operator': 'and',
                    'operands': [
                        {
                            'node_type': 'operator',
                            'operator': 'gt',
                            'operands': [
                                {'node_type': 'terminal', 'terminal': 'close'},
                                {'node_type': 'terminal', 'terminal': 'high', 'transform': 'max', 'period': 20}
                            ]
                        },
                        {
                            'node_type': 'operator',
                            'operator': 'gt',
                            'operands': [
                                {'node_type': 'terminal', 'terminal': 'volume'},
                                {
                                    'node_type': 'operator',
                                    'operator': 'mul',
                                    'operands': [
                                        {'node_type': 'terminal', 'terminal': 'volume', 'transform': 'sma', 'period': 20},
                                        {'node_type': 'constant', 'constant': 1.5}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            },
            parameters={
                'lookback': EvolvableParameter('lookback', 20, 5, 60),
                'volume_multiplier': EvolvableParameter('volume_multiplier', 1.5, 1.0, 3.0),
                'position_size': EvolvableParameter('position_size', 0.15, 0.01, 0.5),
                'stop_loss': EvolvableParameter('stop_loss', 0.03, 0.01, 0.1)
            },
            conditions={
                'market_regime': [MarketRegime.BREAKOUT.value, MarketRegime.TRENDING_UP.value],
                'min_volatility': 0.2,
                'max_volatility': 0.6
            }
        )


# 示例用法
if __name__ == '__main__':
    print('GET Protocol v1.0 - Gene Expression Trading Protocol')
    print('=' * 60)
    
    # 创建动量基因
    gene = GeneTemplates.momentum_gene()
    print('\n动量基因模板:')
    print(gene.to_json())
    
    # 基因变异
    mutated = gene.mutate(mutation_rate=0.5)
    print('\n变异后的基因:')
    print(f'变异: {mutated.lineage["mutations"]}')
    
    # 基因哈希
    print(f'\n基因哈希: {gene.get_hash()}')
