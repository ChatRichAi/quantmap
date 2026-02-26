"""
Quant-GEP Protocol - 标准化协议Schema

定义Quant-GEP v1.0标准格式，支持版本控制和向后兼容
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


# 协议版本
PROTOCOL_VERSION = "1.0.0"
SCHEMA_VERSION = "quant-gep-v1"


class ValidationStatus(Enum):
    """验证状态"""
    PENDING = "pending"
    VALIDATING = "validating"
    VALIDATED = "validated"
    REJECTED = "rejected"


class GeneSource(Enum):
    """基因来源"""
    SEED_DISCOVERY = "seed_discovery"
    CROSSOVER = "crossover"
    MUTATION = "mutation"
    TRANSPOSITION = "transposition"
    PAPER = "paper"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class MutationType(Enum):
    """变异类型"""
    POINT = "point"
    SUBTREE = "subtree"
    IS_TRANSPOSITION = "is_transposition"
    RIS_TRANSPOSITION = "ris_transposition"
    INVERSION = "inversion"
    CROSSOVER = "crossover"
    UNKNOWN = "unknown"


# Quant-GEP v1.0 JSON Schema
QUANT_GEP_SCHEMA_V1 = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Quant-GEP Protocol v1.0",
    "description": "Gene Expression Programming protocol for quantitative trading",
    "version": "1.0.0",
    
    "definitions": {
        "ASTNode": {
            "type": "object",
            "required": ["node_type"],
            "properties": {
                "node_type": {
                    "type": "string",
                    "enum": ["OPERATOR", "COMPARATOR", "INDICATOR", "CONSTANT", "VARIABLE"]
                },
                "value": {"type": ["string", "number"]},
                "indicator": {"type": "string"},
                "parameters": {"type": "object"},
                "children": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/ASTNode"}
                }
            }
        },
        
        "Lineage": {
            "type": "object",
            "properties": {
                "parent_ids": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "mutation_type": {
                    "type": "string",
                    "enum": ["point", "subtree", "crossover", "transposition", "inversion", "unknown"]
                },
                "generation": {"type": "integer", "minimum": 0}
            }
        },
        
        "Validation": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["pending", "validating", "validated", "rejected"]
                },
                "sharpe_ratio": {"type": "number"},
                "max_drawdown": {"type": "number"},
                "annual_return": {"type": "number"},
                "win_rate": {"type": "number", "minimum": 0, "maximum": 1},
                "total_trades": {"type": "integer"},
                "profit_factor": {"type": "number"},
                "test_symbols": {"type": "array", "items": {"type": "string"}},
                "test_period": {"type": "string"},
                "backtest_result": {"type": "object"}
            }
        },
        
        "Metadata": {
            "type": "object",
            "properties": {
                "author": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "source": {
                    "type": "string",
                    "enum": ["seed_discovery", "crossover", "mutation", "transposition", "paper", "manual", "unknown"]
                },
                "tags": {"type": "array", "items": {"type": "string"}},
                "description": {"type": "string"}
            }
        }
    },
    
    "type": "object",
    "required": ["schema_version", "gene_id", "ast"],
    "properties": {
        "schema_version": {"type": "string", "const": "quant-gep-v1"},
        "protocol_version": {"type": "string"},
        "gene_id": {"type": "string", "pattern": "^[a-f0-9]{16}$"},
        "name": {"type": "string", "maxLength": 100},
        "ast": {"$ref": "#/definitions/ASTNode"},
        "lineage": {"$ref": "#/definitions/Lineage"},
        "validation": {"$ref": "#/definitions/Validation"},
        "meta": {"$ref": "#/definitions/Metadata"}
    }
}


@dataclass
class LineageInfo:
    """血统信息"""
    parent_ids: List[str] = field(default_factory=list)
    mutation_type: MutationType = MutationType.UNKNOWN
    generation: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "parent_ids": self.parent_ids,
            "mutation_type": self.mutation_type.value,
            "generation": self.generation
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LineageInfo":
        return cls(
            parent_ids=data.get("parent_ids", []),
            mutation_type=MutationType(data.get("mutation_type", "unknown")),
            generation=data.get("generation", 0)
        )


@dataclass
class ValidationInfo:
    """验证信息"""
    status: ValidationStatus = ValidationStatus.PENDING
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    annual_return: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    profit_factor: float = 0.0
    test_symbols: List[str] = field(default_factory=list)
    test_period: str = ""
    backtest_result: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
            "annual_return": self.annual_return,
            "win_rate": self.win_rate,
            "total_trades": self.total_trades,
            "profit_factor": self.profit_factor,
            "test_symbols": self.test_symbols,
            "test_period": self.test_period,
            "backtest_result": self.backtest_result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationInfo":
        return cls(
            status=ValidationStatus(data.get("status", "pending")),
            sharpe_ratio=data.get("sharpe_ratio", 0.0),
            max_drawdown=data.get("max_drawdown", 0.0),
            annual_return=data.get("annual_return", 0.0),
            win_rate=data.get("win_rate", 0.0),
            total_trades=data.get("total_trades", 0),
            profit_factor=data.get("profit_factor", 0.0),
            test_symbols=data.get("test_symbols", []),
            test_period=data.get("test_period", ""),
            backtest_result=data.get("backtest_result", {})
        )


@dataclass
class Metadata:
    """元数据"""
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: GeneSource = GeneSource.UNKNOWN
    tags: List[str] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "author": self.author,
            "created_at": self.created_at,
            "source": self.source.value,
            "tags": self.tags,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metadata":
        return cls(
            author=data.get("author", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            source=GeneSource(data.get("source", "unknown")),
            tags=data.get("tags", []),
            description=data.get("description", "")
        )


class QuantGEPSchema:
    """
    Quant-GEP协议序列化器
    
    提供标准化的Gene序列化和反序列化
    """
    
    @staticmethod
    def serialize(
        gene,
        validation: Optional[ValidationInfo] = None,
        meta: Optional[Metadata] = None
    ) -> Dict[str, Any]:
        """
        将Gene序列化为Quant-GEP格式
        
        Args:
            gene: GeneExpression对象
            validation: 验证信息
            meta: 元数据
        
        Returns:
            Quant-GEP标准格式的字典
        """
        from ..core.gene_ast import GeneExpression
        
        if not isinstance(gene, GeneExpression):
            raise TypeError(f"Expected GeneExpression, got {type(gene)}")
        
        # 构建基础结构
        payload = {
            "schema_version": SCHEMA_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "gene_id": gene.gene_id or hash(str(gene.to_dict()))[:16],
            "name": getattr(gene, 'name', 'UnnamedGene'),
            "ast": gene.to_dict()["ast"],
            "lineage": {
                "parent_ids": [],
                "mutation_type": "unknown",
                "generation": gene.generation
            },
            "validation": (validation or ValidationInfo()).to_dict(),
            "meta": (meta or Metadata()).to_dict()
        }
        
        return payload
    
    @staticmethod
    def deserialize(payload: Dict[str, Any]):
        """
        从Quant-GEP格式反序列化为Gene
        
        Args:
            payload: Quant-GEP格式的字典
        
        Returns:
            GeneExpression对象
        """
        from ..core.gene_ast import GeneExpression
        
        # 版本检查
        schema_version = payload.get("schema_version", "")
        if schema_version != SCHEMA_VERSION:
            # 尝试向后兼容
            payload = QuantGEPSchema._migrate_to_v1(payload)
        
        # 重建GeneExpression
        gene = GeneExpression.from_dict({
            "gene_id": payload.get("gene_id"),
            "generation": payload.get("lineage", {}).get("generation", 0),
            "ast": payload["ast"]
        })
        
        # 附加额外信息
        gene._validation = ValidationInfo.from_dict(payload.get("validation", {}))
        gene._meta = Metadata.from_dict(payload.get("meta", {}))
        
        return gene
    
    @staticmethod
    def _migrate_to_v1(payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        迁移旧版本数据到v1
        
        支持从QuantClaw原有格式迁移
        """
        # 如果已有schema_version但版本不同
        if "schema_version" in payload:
            # 这里可以添加不同版本间的迁移逻辑
            pass
        
        # 处理旧格式 (原有to_gep()格式)
        if "lineage" in payload and isinstance(payload["lineage"], dict):
            return payload  # 已经是新格式
        
        # 转换旧格式
        migrated = {
            "schema_version": SCHEMA_VERSION,
            "protocol_version": PROTOCOL_VERSION,
            "gene_id": payload.get("gene_id", ""),
            "name": payload.get("name", "UnnamedGene"),
            "ast": payload.get("ast") or QuantGEPSchema._formula_to_ast(payload.get("formula", "")),
            "lineage": {
                "parent_ids": payload.get("lineage", {}).get("parent_ids", []),
                "mutation_type": payload.get("lineage", {}).get("mutation_type", "unknown"),
                "generation": payload.get("generation", 0)
            },
            "validation": payload.get("validation", {}),
            "meta": payload.get("meta", {})
        }
        
        return migrated
    
    @staticmethod
    def _formula_to_ast(formula: str) -> Dict[str, Any]:
        """将字符串公式转换为AST (简单实现)"""
        # 这里可以复用GeneExpression.from_formula的逻辑
        return {
            "node_type": "VARIABLE",
            "value": "close"
        }
    
    @staticmethod
    def to_json(gene, **kwargs) -> str:
        """序列化为JSON字符串"""
        payload = QuantGEPSchema.serialize(gene, **kwargs)
        return json.dumps(payload, indent=2, ensure_ascii=False)
    
    @staticmethod
    def from_json(json_str: str):
        """从JSON字符串反序列化"""
        payload = json.loads(json_str)
        return QuantGEPSchema.deserialize(payload)
    
    @staticmethod
    def validate(payload: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        验证payload是否符合schema
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查必需字段
        required = ["schema_version", "gene_id", "ast"]
        for field in required:
            if field not in payload:
                errors.append(f"Missing required field: {field}")
        
        # 检查schema版本
        if payload.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"Unsupported schema version: {payload.get('schema_version')}")
        
        # 检查AST结构
        ast = payload.get("ast")
        if ast:
            if "node_type" not in ast:
                errors.append("AST missing node_type")
            if ast.get("node_type") not in ["OPERATOR", "COMPARATOR", "INDICATOR", "CONSTANT", "VARIABLE"]:
                errors.append(f"Invalid node_type: {ast.get('node_type')}")
        
        # 检查gene_id格式
        gene_id = payload.get("gene_id", "")
        if len(gene_id) != 16:
            errors.append(f"Invalid gene_id length: {len(gene_id)} (expected 16)")
        
        return len(errors) == 0, errors


class ProtocolCompatibility:
    """协议兼容性处理"""
    
    SUPPORTED_VERSIONS = ["quant-gep-v1"]
    
    @classmethod
    def check_compatibility(cls, payload: Dict[str, Any]) -> bool:
        """检查payload是否兼容"""
        version = payload.get("schema_version", "")
        return version in cls.SUPPORTED_VERSIONS
    
    @classmethod
    def get_migration_path(cls, from_version: str, to_version: str = SCHEMA_VERSION):
        """获取版本迁移路径"""
        # 这里可以定义版本间的迁移链
        migrations = {
            ("legacy", "quant-gep-v1"): QuantGEPSchema._migrate_to_v1
        }
        return migrations.get((from_version, to_version))


# 便捷函数
def serialize_gene(gene, **kwargs) -> Dict[str, Any]:
    """快捷序列化函数"""
    return QuantGEPSchema.serialize(gene, **kwargs)


def deserialize_gene(payload: Dict[str, Any]):
    """快捷反序列化函数"""
    return QuantGEPSchema.deserialize(payload)


def gene_to_json(gene, **kwargs) -> str:
    """Gene转JSON"""
    return QuantGEPSchema.to_json(gene, **kwargs)


def gene_from_json(json_str: str):
    """JSON转Gene"""
    return QuantGEPSchema.from_json(json_str)


# 示例用法
if __name__ == "__main__":
    # 创建示例gene
    from ..core.gene_ast import create_buy_signal, IndicatorType
    
    gene = create_buy_signal(IndicatorType.RSI, 30)
    gene.gene_id = "abc123def4567890"
    
    # 序列化
    payload = QuantGEPSchema.serialize(
        gene,
        validation=ValidationInfo(
            status=ValidationStatus.VALIDATED,
            sharpe_ratio=1.8,
            max_drawdown=-0.15
        ),
        meta=Metadata(
            author="QuantClaw",
            source=GeneSource.MUTATION,
            tags=["rsi", "mean_reversion"]
        )
    )
    
    print(json.dumps(payload, indent=2))
    
    # 验证
    is_valid, errors = QuantGEPSchema.validate(payload)
    print(f"Valid: {is_valid}, Errors: {errors}")
