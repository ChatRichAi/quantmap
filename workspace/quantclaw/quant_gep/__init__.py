"""
Quant-GEP - Gene Expression Programming for Quantitative Trading

行业级 GEP 协议实现，包含：
1. 标准 Gene 表达式 AST
2. 完整 GEP 进化算子
3. 标准化回测接口
4. 版本化 Protocol Schema

版本: 1.0.0
协议: quant-gep-v1
"""

__version__ = "1.0.0"
__schema_version__ = "quant-gep-v1"

# Core - AST基因表达式
from .core.gene_ast import (
    GeneASTNode,
    GeneExpression,
    MarketContext,
    OperatorNode,
    Operator,
    IndicatorNode,
    IndicatorType,
    ConstantNode,
    VariableNode,
    create_buy_signal,
    create_crossover_signal
)

# Operators - GEP进化算子
from .operators import (
    GEPConfig,
    PointMutation,
    SubtreeMutation,
    OnePointCrossover,
    TranspositionOperator,
    InversionOperator,
    SelectionOperator,
    RandomTreeGenerator
)

# Evolution - 进化算法
from .evolution import (
    GEPAlgorithm,
    MultiObjectiveGEP,
    FitnessResult,
    EvolutionStats,
    quick_evolve
)

# Backtest - 标准化回测
from .backtest import (
    BacktestAdapter,
    SimpleBacktestEngine,
    AShareAdapter,
    USStockAdapter,
    CryptoAdapter,
    MarketData,
    MarketType,
    TimeFrame,
    BacktestResult,
    create_adapter,
    quick_backtest
)

# Protocol - 标准Schema
from .protocol import (
    QuantGEPSchema,
    ValidationStatus,
    GeneSource,
    MutationType,
    LineageInfo,
    ValidationInfo,
    Metadata,
    serialize_gene,
    deserialize_gene,
    gene_to_json,
    gene_from_json,
    PROTOCOL_VERSION,
    SCHEMA_VERSION
)

# API - 标准接口
from .api import GEPAPI

__all__ = [
    # Version
    "__version__",
    "__schema_version__",
    
    # Core
    "GeneASTNode",
    "GeneExpression",
    "MarketContext",
    "OperatorNode",
    "Operator",
    "IndicatorNode",
    "IndicatorType",
    "ConstantNode",
    "VariableNode",
    "create_buy_signal",
    "create_crossover_signal",
    
    # Operators
    "GEPConfig",
    "PointMutation",
    "SubtreeMutation",
    "OnePointCrossover",
    "TranspositionOperator",
    "InversionOperator",
    "SelectionOperator",
    "RandomTreeGenerator",
    
    # Evolution
    "GEPAlgorithm",
    "MultiObjectiveGEP",
    "FitnessResult",
    "EvolutionStats",
    "quick_evolve",
    
    # Backtest
    "BacktestAdapter",
    "SimpleBacktestEngine",
    "AShareAdapter",
    "USStockAdapter",
    "CryptoAdapter",
    "MarketData",
    "MarketType",
    "TimeFrame",
    "BacktestResult",
    "create_adapter",
    "quick_backtest",
    
    # Protocol
    "QuantGEPSchema",
    "ValidationStatus",
    "GeneSource",
    "MutationType",
    "LineageInfo",
    "ValidationInfo",
    "Metadata",
    "serialize_gene",
    "deserialize_gene",
    "gene_to_json",
    "gene_from_json",
    "PROTOCOL_VERSION",
    "SCHEMA_VERSION",
    
    # API
    "GEPAPI"
]
