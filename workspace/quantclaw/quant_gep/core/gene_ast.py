"""
Quant-GEP Core - Gene Expression AST
标准基因表达式抽象语法树实现

提供 genotype (树形结构) 到 phenotype (可执行策略) 的完整转换
"""

from __future__ import annotations

import json
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Protocol, Tuple, Union


class NodeType(Enum):
    """AST节点类型"""
    OPERATOR = auto()      # 逻辑/算术运算符
    INDICATOR = auto()     # 技术指标
    CONSTANT = auto()      # 常数
    VARIABLE = auto()      # 变量 (如 close, open)
    COMPARATOR = auto()    # 比较运算符


class Operator(Enum):
    """逻辑和算术运算符"""
    # 逻辑运算符
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    # 算术运算符
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    
    # 比较运算符
    GT = ">"
    LT = "<"
    GE = ">="
    LE = "<="
    EQ = "=="
    NE = "!="


class IndicatorType(Enum):
    """技术指标类型"""
    SMA = "SMA"
    EMA = "EMA"
    RSI = "RSI"
    MACD = "MACD"
    ATR = "ATR"
    BOLL = "BOLL"
    KDJ = "KDJ"
    CCI = "CCI"
    ADX = "ADX"
    OBV = "OBV"
    VOLUME = "VOLUME"


@dataclass
class MarketContext:
    """市场数据上下文"""
    symbol: str
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    # 历史数据 (用于指标计算)
    history: List[Dict[str, float]] = field(default_factory=list)
    
    def get_series(self, field: str, periods: int) -> List[float]:
        """获取历史序列数据"""
        values = [bar[field] for bar in self.history[-periods:]]
        values.append(getattr(self, field))
        return values


class GeneASTNode(ABC):
    """基因AST节点基类"""
    
    def __init__(self, node_type: NodeType):
        self.node_type = node_type
        self.children: List[GeneASTNode] = []
        self.parent: Optional[GeneASTNode] = None
    
    @abstractmethod
    def evaluate(self, context: MarketContext) -> Union[bool, float]:
        """在市场上下文中评估节点"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        pass
    
    @abstractmethod
    def clone(self) -> GeneASTNode:
        """深拷贝节点"""
        pass
    
    def add_child(self, child: GeneASTNode) -> None:
        """添加子节点"""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: GeneASTNode) -> None:
        """移除子节点"""
        if child in self.children:
            child.parent = None
            self.children.remove(child)
    
    def replace_child(self, old_child: GeneASTNode, new_child: GeneASTNode) -> None:
        """替换子节点"""
        idx = self.children.index(old_child)
        old_child.parent = None
        new_child.parent = self
        self.children[idx] = new_child
    
    def get_depth(self) -> int:
        """获取节点深度"""
        if not self.children:
            return 1
        return 1 + max(child.get_depth() for child in self.children)
    
    def get_node_count(self) -> int:
        """获取子树节点总数"""
        return 1 + sum(child.get_node_count() for child in self.children)
    
    def traverse(self) -> List[GeneASTNode]:
        """遍历所有节点"""
        result = [self]
        for child in self.children:
            result.extend(child.traverse())
        return result
    
    def find_nodes(self, predicate) -> List[GeneASTNode]:
        """查找符合条件的节点"""
        return [n for n in self.traverse() if predicate(n)]
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> GeneASTNode:
        """从字典反序列化"""
        node_type = NodeType[data["node_type"]]
        
        if node_type == NodeType.OPERATOR or node_type == NodeType.COMPARATOR:
            node = OperatorNode(Operator(data["value"]))
        elif node_type == NodeType.INDICATOR:
            node = IndicatorNode(
                IndicatorType(data["indicator"]),
                data.get("parameters", {})
            )
        elif node_type == NodeType.CONSTANT:
            node = ConstantNode(data["value"])
        elif node_type == NodeType.VARIABLE:
            node = VariableNode(data["value"])
        else:
            raise ValueError(f"Unknown node type: {node_type}")
        
        for child_data in data.get("children", []):
            child = GeneASTNode.from_dict(child_data)
            node.add_child(child)
        
        return node


class OperatorNode(GeneASTNode):
    """运算符节点"""
    
    def __init__(self, operator: Operator):
        super().__init__(NodeType.OPERATOR if operator in 
                        [Operator.AND, Operator.OR, Operator.NOT, 
                         Operator.ADD, Operator.SUB, Operator.MUL, Operator.DIV]
                        else NodeType.COMPARATOR)
        self.operator = operator
    
    def evaluate(self, context: MarketContext) -> Union[bool, float]:
        if self.operator == Operator.NOT:
            return not self.children[0].evaluate(context)
        
        left = self.children[0].evaluate(context)
        right = self.children[1].evaluate(context) if len(self.children) > 1 else None
        
        # 逻辑运算符
        if self.operator == Operator.AND:
            return left and right
        elif self.operator == Operator.OR:
            return left or right
        
        # 比较运算符
        elif self.operator == Operator.GT:
            return left > right
        elif self.operator == Operator.LT:
            return left < right
        elif self.operator == Operator.GE:
            return left >= right
        elif self.operator == Operator.LE:
            return left <= right
        elif self.operator == Operator.EQ:
            return left == right
        elif self.operator == Operator.NE:
            return left != right
        
        # 算术运算符
        elif self.operator == Operator.ADD:
            return left + right
        elif self.operator == Operator.SUB:
            return left - right
        elif self.operator == Operator.MUL:
            return left * right
        elif self.operator == Operator.DIV:
            return left / right if right != 0 else float('inf')
        
        raise ValueError(f"Unknown operator: {self.operator}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": self.node_type.name,
            "value": self.operator.value,
            "children": [child.to_dict() for child in self.children]
        }
    
    def clone(self) -> OperatorNode:
        node = OperatorNode(self.operator)
        for child in self.children:
            node.add_child(child.clone())
        return node
    
    def __repr__(self) -> str:
        return f"OperatorNode({self.operator.value})"


class IndicatorNode(GeneASTNode):
    """技术指标节点"""
    
    def __init__(self, indicator: IndicatorType, parameters: Dict[str, Any] = None):
        super().__init__(NodeType.INDICATOR)
        self.indicator = indicator
        self.parameters = parameters or {}
    
    def evaluate(self, context: MarketContext) -> float:
        """计算技术指标值"""
        # 获取参数
        period = self.parameters.get("period", 14)
        
        if self.indicator == IndicatorType.SMA:
            series = context.get_series("close", period)
            return sum(series) / len(series) if series else context.close
        
        elif self.indicator == IndicatorType.EMA:
            series = context.get_series("close", period * 2)
            if not series:
                return context.close
            multiplier = 2 / (period + 1)
            ema = series[0]
            for price in series[1:]:
                ema = (price - ema) * multiplier + ema
            return ema
        
        elif self.indicator == IndicatorType.RSI:
            series = context.get_series("close", period + 1)
            if len(series) < 2:
                return 50.0
            gains = []
            losses = []
            for i in range(1, len(series)):
                change = series[i] - series[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            if avg_loss == 0:
                return 100.0
            rs = avg_gain / avg_loss
            return 100 - (100 / (1 + rs))
        
        elif self.indicator == IndicatorType.ATR:
            highs = context.get_series("high", period)
            lows = context.get_series("low", period)
            closes = context.get_series("close", period + 1)
            tr_list = []
            for i in range(len(highs)):
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i]) if i > 0 else 0,
                    abs(lows[i] - closes[i]) if i > 0 else 0
                )
                tr_list.append(tr)
            return sum(tr_list) / len(tr_list) if tr_list else context.high - context.low
        
        elif self.indicator == IndicatorType.VOLUME:
            return context.volume
        
        # 默认返回收盘价
        return context.close
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": self.node_type.name,
            "indicator": self.indicator.value,
            "parameters": self.parameters,
            "children": [child.to_dict() for child in self.children]
        }
    
    def clone(self) -> IndicatorNode:
        node = IndicatorNode(self.indicator, self.parameters.copy())
        for child in self.children:
            node.add_child(child.clone())
        return node
    
    def __repr__(self) -> str:
        return f"IndicatorNode({self.indicator.value})"


class ConstantNode(GeneASTNode):
    """常数节点"""
    
    def __init__(self, value: float):
        super().__init__(NodeType.CONSTANT)
        self.value = value
    
    def evaluate(self, context: MarketContext) -> float:
        return self.value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": self.node_type.name,
            "value": self.value
        }
    
    def clone(self) -> ConstantNode:
        return ConstantNode(self.value)
    
    def __repr__(self) -> str:
        return f"ConstantNode({self.value})"


class VariableNode(GeneASTNode):
    """变量节点 (OHLCV等)"""
    
    VALID_VARIABLES = {"open", "high", "low", "close", "volume", "hl2", "hlc3", "ohlc4"}
    
    def __init__(self, name: str):
        super().__init__(NodeType.VARIABLE)
        if name not in self.VALID_VARIABLES:
            raise ValueError(f"Invalid variable: {name}. Must be one of {self.VALID_VARIABLES}")
        self.name = name
    
    def evaluate(self, context: MarketContext) -> float:
        if self.name == "open":
            return context.open
        elif self.name == "high":
            return context.high
        elif self.name == "low":
            return context.low
        elif self.name == "close":
            return context.close
        elif self.name == "volume":
            return context.volume
        elif self.name == "hl2":
            return (context.high + context.low) / 2
        elif self.name == "hlc3":
            return (context.high + context.low + context.close) / 3
        elif self.name == "ohlc4":
            return (context.open + context.high + context.low + context.close) / 4
        return context.close
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": self.node_type.name,
            "value": self.name
        }
    
    def clone(self) -> VariableNode:
        return VariableNode(self.name)
    
    def __repr__(self) -> str:
        return f"VariableNode({self.name})"


@dataclass
class GeneExpression:
    """
    基因表达式 - 完整的基因型表示
    
    将字符串公式转换为AST，支持完整的GEP操作
    """
    root: GeneASTNode
    gene_id: Optional[str] = None
    generation: int = 0
    
    def evaluate(self, context: MarketContext) -> Union[bool, float]:
        """评估基因表达式"""
        return self.root.evaluate(context)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "gene_id": self.gene_id,
            "generation": self.generation,
            "ast": self.root.to_dict()
        }
    
    def to_json(self) -> str:
        """序列化为JSON"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GeneExpression:
        """从字典创建"""
        root = GeneASTNode.from_dict(data["ast"])
        return cls(
            root=root,
            gene_id=data.get("gene_id"),
            generation=data.get("generation", 0)
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> GeneExpression:
        """从JSON创建"""
        return cls.from_dict(json.loads(json_str))
    
    @classmethod
    def from_formula(cls, formula: str) -> GeneExpression:
        """
        从字符串公式解析为AST
        
        支持格式:
        - "RSI(14) < 30"
        - "SMA(20) > close AND volume > 1000000"
        - "close > SMA(20) AND RSI(14) < 70"
        """
        # 简单解析器 (可扩展为完整parser)
        formula = formula.strip()
        
        # 处理 AND/OR 连接
        if " AND " in formula.upper():
            parts = formula.upper().split(" AND ")
            root = OperatorNode(Operator.AND)
            for part in parts:
                child = cls._parse_simple_condition(part.strip())
                root.add_child(child)
            return cls(root=root)
        
        if " OR " in formula.upper():
            parts = formula.upper().split(" OR ")
            root = OperatorNode(Operator.OR)
            for part in parts:
                child = cls._parse_simple_condition(part.strip())
                root.add_child(child)
            return cls(root=root)
        
        root = cls._parse_simple_condition(formula)
        return cls(root=root)
    
    @staticmethod
    def _parse_simple_condition(condition: str) -> GeneASTNode:
        """解析简单条件"""
        condition = condition.strip()
        
        # 查找比较运算符
        for op in [">=", "<=", "==", "!=", ">", "<"]:
            if op in condition:
                left_str, right_str = condition.split(op, 1)
                left = GeneExpression._parse_operand(left_str.strip())
                right = GeneExpression._parse_operand(right_str.strip())
                
                op_map = {
                    ">": Operator.GT, "<": Operator.LT,
                    ">=": Operator.GE, "<=": Operator.LE,
                    "==": Operator.EQ, "!=": Operator.NE
                }
                
                root = OperatorNode(op_map[op])
                root.add_child(left)
                root.add_child(right)
                return root
        
        # 如果没有运算符，直接返回操作数
        return GeneExpression._parse_operand(condition)
    
    @staticmethod
    def _parse_operand(operand: str) -> GeneASTNode:
        """解析操作数"""
        operand = operand.strip()
        
        # 检查是否是指标函数
        if "(" in operand and ")" in operand:
            func_name = operand[:operand.index("(")].upper()
            args_str = operand[operand.index("(")+1:operand.index(")")]
            
            if func_name in [i.value for i in IndicatorType]:
                params = {}
                if args_str:
                    params["period"] = int(args_str)
                return IndicatorNode(IndicatorType[func_name], params)
        
        # 检查是否是变量
        if operand.lower() in VariableNode.VALID_VARIABLES:
            return VariableNode(operand.lower())
        
        # 尝试解析为常数
        try:
            return ConstantNode(float(operand))
        except ValueError:
            pass
        
        # 默认返回收盘价变量
        return VariableNode("close")
    
    def clone(self) -> GeneExpression:
        """深拷贝"""
        return GeneExpression(
            root=self.root.clone(),
            gene_id=self.gene_id,
            generation=self.generation
        )
    
    def get_depth(self) -> int:
        """获取表达式深度"""
        return self.root.get_depth()
    
    def get_complexity(self) -> int:
        """获取复杂度 (节点数)"""
        return self.root.get_node_count()
    
    def to_formula(self) -> str:
        """转换回字符串公式 (可读性)"""
        return self._node_to_formula(self.root)
    
    def _node_to_formula(self, node: GeneASTNode) -> str:
        """递归转换节点为公式"""
        if isinstance(node, ConstantNode):
            return str(node.value)
        elif isinstance(node, VariableNode):
            return node.name
        elif isinstance(node, IndicatorNode):
            if node.parameters:
                params = ",".join(f"{k}={v}" for k, v in node.parameters.items())
                return f"{node.indicator.value}({params})"
            return f"{node.indicator.value}()"
        elif isinstance(node, OperatorNode):
            if node.operator == Operator.NOT:
                return f"NOT({self._node_to_formula(node.children[0])})"
            
            left = self._node_to_formula(node.children[0])
            right = self._node_to_formula(node.children[1]) if len(node.children) > 1 else ""
            
            if node.operator in [Operator.AND, Operator.OR]:
                return f"({left} {node.operator.value} {right})"
            return f"{left} {node.operator.value} {right}"
        
        return ""


# 便捷函数
def create_buy_signal(
    indicator: IndicatorType,
    threshold: float,
    condition: str = "<"
) -> GeneExpression:
    """
    快速创建买入信号基因
    
    Args:
        indicator: 指标类型
        threshold: 阈值
        condition: 条件 ("<", ">", "<=", ">=")
    
    Example:
        >>> gene = create_buy_signal(IndicatorType.RSI, 30, "<")
        >>> # 生成: RSI(14) < 30
    """
    ind_node = IndicatorNode(indicator, {"period": 14})
    const_node = ConstantNode(threshold)
    
    op_map = {"<": Operator.LT, ">": Operator.GT, "<=": Operator.LE, ">=": Operator.GE}
    op = OperatorNode(op_map.get(condition, Operator.LT))
    
    op.add_child(ind_node)
    op.add_child(const_node)
    
    return GeneExpression(root=op)


def create_crossover_signal(
    fast_period: int,
    slow_period: int
) -> GeneExpression:
    """
    创建均线金叉信号
    
    Example:
        >>> gene = create_crossover_signal(20, 60)
        >>> # 生成: SMA(20) > SMA(60)
    """
    fast_sma = IndicatorNode(IndicatorType.SMA, {"period": fast_period})
    slow_sma = IndicatorNode(IndicatorType.SMA, {"period": slow_period})
    
    op = OperatorNode(Operator.GT)
    op.add_child(fast_sma)
    op.add_child(slow_sma)
    
    return GeneExpression(root=op)
