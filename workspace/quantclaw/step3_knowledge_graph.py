"""
QuantClaw Community Edition - Step 3: 量化专用知识图谱
基于 Neo4j 的策略、因子、论文关系网络
"""

import os
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
import sqlite3

# 尝试导入 Neo4j
try:
    from py2neo import Graph, Node, Relationship, NodeMatcher
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: py2neo not installed. Using SQLite fallback.")


class EntityType(Enum):
    """知识图谱实体类型"""
    STRATEGY = "Strategy"           # 策略
    FACTOR = "Factor"               # 因子/基因
    PAPER = "Paper"                 # 论文
    AUTHOR = "Author"               # 作者
    MARKET = "Market"               # 市场
    ASSET = "Asset"                 # 资产/股票
    INDICATOR = "Indicator"         # 技术指标
    METHOD = "Method"               # 方法/算法


class RelationType(Enum):
    """知识图谱关系类型"""
    # 策略相关
    IMPLEMENTS = "IMPLEMENTS"           # 策略实现论文
    USES_FACTOR = "USES_FACTOR"         # 策略使用因子
    DERIVED_FROM = "DERIVED_FROM"       # 策略派生自
    IMPROVES = "IMPROVES"               # 策略改进自
    COMPOSED_OF = "COMPOSED_OF"         # 策略由...组成
    
    # 因子相关
    BASED_ON = "BASED_ON"               # 因子基于论文
    CORRELATES_WITH = "CORRELATES_WITH" # 因子相关于
    LEADS_TO = "LEADS_TO"               # 因子导致
    
    # 论文相关
    CITES = "CITES"                     # 论文引用
    WRITTEN_BY = "WRITTEN_BY"           # 论文作者
    APPLIES_TO = "APPLIES_TO"           # 论文应用于
    USES_METHOD = "USES_METHOD"         # 论文使用方法
    
    # 市场相关
    TRADES_ON = "TRADES_ON"             # 在市场交易
    BELONGS_TO = "BELONGS_TO"           # 属于市场
    AFFECTED_BY = "AFFECTED_BY"         # 受...影响
    
    # 验证相关
    VALIDATED_BY = "VALIDATED_BY"       # 被...验证
    TESTED_ON = "TESTED_ON"             # 在...上测试
    OUTPERFORMS = "OUTPERFORMS"         # 表现优于


@dataclass
class KnowledgeEntity:
    """知识实体"""
    entity_id: str
    entity_type: EntityType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type.value,
            "name": self.name,
            "properties": self.properties,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class KnowledgeRelation:
    """知识关系"""
    relation_id: str
    relation_type: RelationType
    source_id: str
    target_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "properties": self.properties,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat()
        }


class QuantKnowledgeGraph:
    """
    量化专用知识图谱
    
    核心功能:
    1. 实体管理 (策略、因子、论文等)
    2. 关系管理 (实现、引用、改进等)
    3. 路径发现 (策略溯源)
    4. 相似度查询 (相似策略发现)
    5. 推荐系统 (基于图谱的策略推荐)
    """
    
    def __init__(self, uri: str = None, user: str = None, password: str = None,
                 fallback_db: str = "knowledge_graph.db"):
        """
        初始化知识图谱
        
        Args:
            uri: Neo4j URI (如: bolt://localhost:7687)
            user: Neo4j 用户名
            password: Neo4j 密码
            fallback_db: SQLite 备用数据库路径
        """
        self.use_neo4j = False
        self.graph = None
        self.matcher = None
        
        # 尝试连接 Neo4j
        if NEO4J_AVAILABLE and uri:
            try:
                self.graph = Graph(uri, auth=(user, password))
                self.matcher = NodeMatcher(self.graph)
                self.use_neo4j = True
                print(f"✅ Connected to Neo4j at {uri}")
            except Exception as e:
                print(f"❌ Neo4j connection failed: {e}")
                print(f"🔄 Falling back to SQLite")
        
        # SQLite 备用
        if not self.use_neo4j:
            self.fallback_db = fallback_db
            self._init_sqlite()
    
    def _init_sqlite(self):
        """初始化 SQLite 备用数据库"""
        conn = sqlite3.connect(self.fallback_db)
        cursor = conn.cursor()
        
        # 实体表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT,
                name TEXT,
                properties TEXT,
                created_at TEXT
            )
        ''')
        
        # 关系表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS relations (
                relation_id TEXT PRIMARY KEY,
                relation_type TEXT,
                source_id TEXT,
                target_id TEXT,
                properties TEXT,
                confidence REAL,
                created_at TEXT
            )
        ''')
        
        # 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_entity_type ON entities(entity_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relation_source ON relations(source_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_relation_target ON relations(target_id)')
        
        conn.commit()
        conn.close()
        print(f"✅ SQLite fallback initialized: {self.fallback_db}")
    
    # ==================== 实体操作 ====================
    
    def create_entity(self, entity_type: EntityType, name: str, 
                     properties: Dict = None, entity_id: str = None) -> str:
        """
        创建实体
        
        Args:
            entity_type: 实体类型
            name: 实体名称
            properties: 实体属性
            entity_id: 可选指定ID
            
        Returns:
            entity_id
        """
        if properties is None:
            properties = {}
        
        if entity_id is None:
            entity_id = f"{entity_type.value}_{hashlib.md5(name.encode()).hexdigest()[:12]}"
        
        entity = KnowledgeEntity(
            entity_id=entity_id,
            entity_type=entity_type,
            name=name,
            properties=properties
        )
        
        if self.use_neo4j:
            self._create_entity_neo4j(entity)
        else:
            self._create_entity_sqlite(entity)
        
        return entity_id
    
    def _create_entity_neo4j(self, entity: KnowledgeEntity):
        """在 Neo4j 中创建实体"""
        node = Node(
            entity.entity_type.value,
            entity_id=entity.entity_id,
            name=entity.name,
            **entity.properties
        )
        self.graph.create(node)
    
    def _create_entity_sqlite(self, entity: KnowledgeEntity):
        """在 SQLite 中创建实体"""
        conn = sqlite3.connect(self.fallback_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO entities VALUES (?, ?, ?, ?, ?)
        ''', (
            entity.entity_id,
            entity.entity_type.value,
            entity.name,
            json.dumps(entity.properties),
            entity.created_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_entity(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """获取实体"""
        if self.use_neo4j:
            return self._get_entity_neo4j(entity_id)
        else:
            return self._get_entity_sqlite(entity_id)
    
    def _get_entity_neo4j(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """从 Neo4j 获取实体"""
        node = self.matcher.match(entity_id=entity_id).first()
        if node is None:
            return None
        
        return KnowledgeEntity(
            entity_id=node["entity_id"],
            entity_type=EntityType(node.labels.__iter__().__next__())
            if node.labels else EntityType.STRATEGY,
            name=node["name"],
            properties={k: v for k, v in node.items() if k not in ["entity_id", "name"]}
        )
    
    def _get_entity_sqlite(self, entity_id: str) -> Optional[KnowledgeEntity]:
        """从 SQLite 获取实体"""
        conn = sqlite3.connect(self.fallback_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM entities WHERE entity_id = ?', (entity_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        return KnowledgeEntity(
            entity_id=row[0],
            entity_type=EntityType(row[1]),
            name=row[2],
            properties=json.loads(row[3]) if row[3] else {},
            created_at=datetime.fromisoformat(row[4])
        )
    
    def find_entities(self, entity_type: EntityType = None, 
                     name_pattern: str = None,
                     properties: Dict = None) -> List[KnowledgeEntity]:
        """
        查找实体
        
        Args:
            entity_type: 实体类型筛选
            name_pattern: 名称匹配模式
            properties: 属性匹配
        """
        if self.use_neo4j:
            return self._find_entities_neo4j(entity_type, name_pattern, properties)
        else:
            return self._find_entities_sqlite(entity_type, name_pattern, properties)
    
    def _find_entities_sqlite(self, entity_type: EntityType = None,
                              name_pattern: str = None,
                              properties: Dict = None) -> List[KnowledgeEntity]:
        """从 SQLite 查找实体"""
        conn = sqlite3.connect(self.fallback_db)
        cursor = conn.cursor()
        
        query = "SELECT * FROM entities WHERE 1=1"
        params = []
        
        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type.value)
        
        if name_pattern:
            query += " AND name LIKE ?"
            params.append(f"%{name_pattern}%")
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            entity_props = json.loads(row[3]) if row[3] else {}
            
            # 属性筛选
            if properties:
                match = True
                for key, value in properties.items():
                    if entity_props.get(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append(KnowledgeEntity(
                entity_id=row[0],
                entity_type=EntityType(row[1]),
                name=row[2],
                properties=entity_props,
                created_at=datetime.fromisoformat(row[4])
            ))
        
        return results
    
    def _find_entities_neo4j(self, entity_type: EntityType = None,
                             name_pattern: str = None,
                             properties: Dict = None) -> List[KnowledgeEntity]:
        """从 Neo4j 查找实体"""
        # 构建 Cypher 查询
        if entity_type:
            query = f"MATCH (n:{entity_type.value}) WHERE 1=1"
        else:
            query = "MATCH (n) WHERE 1=1"
        
        params = {}
        
        if name_pattern:
            query += " AND n.name CONTAINS $name_pattern"
            params["name_pattern"] = name_pattern
        
        if properties:
            for key, value in properties.items():
                query += f" AND n.{key} = ${key}"
                params[key] = value
        
        query += " RETURN n"
        
        results = []
        for record in self.graph.run(query, **params):
            node = record["n"]
            results.append(KnowledgeEntity(
                entity_id=node["entity_id"],
                entity_type=EntityType(list(node.labels)[0]) if node.labels else EntityType.STRATEGY,
                name=node["name"],
                properties={k: v for k, v in node.items() if k not in ["entity_id", "name"]}
            ))
        
        return results
    
    # ==================== 关系操作 ====================
    
    def create_relation(self, source_id: str, target_id: str,
                       relation_type: RelationType,
                       properties: Dict = None,
                       confidence: float = 1.0) -> str:
        """
        创建关系
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            properties: 关系属性
            confidence: 置信度 (0-1)
            
        Returns:
            relation_id
        """
        if properties is None:
            properties = {}
        
        relation_id = f"REL_{hashlib.md5(f'{source_id}_{target_id}_{relation_type.value}'.encode()).hexdigest()[:12]}"
        
        relation = KnowledgeRelation(
            relation_id=relation_id,
            relation_type=relation_type,
            source_id=source_id,
            target_id=target_id,
            properties=properties,
            confidence=confidence
        )
        
        if self.use_neo4j:
            self._create_relation_neo4j(relation)
        else:
            self._create_relation_sqlite(relation)
        
        return relation_id
    
    def _create_relation_neo4j(self, relation: KnowledgeRelation):
        """在 Neo4j 中创建关系"""
        source = self.matcher.match(entity_id=relation.source_id).first()
        target = self.matcher.match(entity_id=relation.target_id).first()
        
        if source is None or target is None:
            raise ValueError("Source or target entity not found")
        
        rel = Relationship(source, relation.relation_type.value, target,
                          relation_id=relation.relation_id,
                          confidence=relation.confidence,
                          **relation.properties)
        self.graph.create(rel)
    
    def _create_relation_sqlite(self, relation: KnowledgeRelation):
        """在 SQLite 中创建关系"""
        conn = sqlite3.connect(self.fallback_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO relations VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            relation.relation_id,
            relation.relation_type.value,
            relation.source_id,
            relation.target_id,
            json.dumps(relation.properties),
            relation.confidence,
            relation.created_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_relations(self, entity_id: str, 
                     relation_type: RelationType = None,
                     direction: str = "both") -> List[KnowledgeRelation]:
        """
        获取实体的关系
        
        Args:
            entity_id: 实体ID
            relation_type: 关系类型筛选
            direction: "out" ( outgoing ), "in" ( incoming ), "both"
        """
        if self.use_neo4j:
            return self._get_relations_neo4j(entity_id, relation_type, direction)
        else:
            return self._get_relations_sqlite(entity_id, relation_type, direction)
    
    def _get_relations_sqlite(self, entity_id: str,
                              relation_type: RelationType = None,
                              direction: str = "both") -> List[KnowledgeRelation]:
        """从 SQLite 获取关系"""
        conn = sqlite3.connect(self.fallback_db)
        cursor = conn.cursor()
        
        relations = []
        
        if direction in ["out", "both"]:
            query = "SELECT * FROM relations WHERE source_id = ?"
            params = [entity_id]
            
            if relation_type:
                query += " AND relation_type = ?"
                params.append(relation_type.value)
            
            cursor.execute(query, params)
            for row in cursor.fetchall():
                relations.append(self._row_to_relation(row))
        
        if direction in ["in", "both"]:
            query = "SELECT * FROM relations WHERE target_id = ?"
            params = [entity_id]
            
            if relation_type:
                query += " AND relation_type = ?"
                params.append(relation_type.value)
            
            cursor.execute(query, params)
            for row in cursor.fetchall():
                relations.append(self._row_to_relation(row))
        
        conn.close()
        return relations
    
    def _row_to_relation(self, row) -> KnowledgeRelation:
        """数据库行转关系对象"""
        return KnowledgeRelation(
            relation_id=row[0],
            relation_type=RelationType(row[1]),
            source_id=row[2],
            target_id=row[3],
            properties=json.loads(row[4]) if row[4] else {},
            confidence=row[5],
            created_at=datetime.fromisoformat(row[6])
        )
    
    # ==================== 高级查询 ====================
    
    def find_path(self, start_id: str, end_id: str, 
                 max_depth: int = 5) -> List[List[str]]:
        """
        查找两个实体之间的路径
        
        用途: 策略溯源、改进链追踪
        """
        if self.use_neo4j:
            return self._find_path_neo4j(start_id, end_id, max_depth)
        else:
            return self._find_path_sqlite(start_id, end_id, max_depth)
    
    def _find_path_sqlite(self, start_id: str, end_id: str,
                          max_depth: int) -> List[List[str]]:
        """在 SQLite 中查找路径 (BFS)"""
        # 简化版 BFS
        paths = []
        visited = set()
        queue = [(start_id, [start_id])]
        
        while queue and len(paths) < 10:  # 限制结果数量
            current, path = queue.pop(0)
            
            if current == end_id:
                paths.append(path)
                continue
            
            if len(path) > max_depth:
                continue
            
            if current in visited:
                continue
            
            visited.add(current)
            
            # 获取相邻节点
            relations = self._get_relations_sqlite(current, direction="out")
            for rel in relations:
                if rel.target_id not in visited:
                    queue.append((rel.target_id, path + [rel.target_id]))
        
        return paths
    
    def find_similar_strategies(self, strategy_id: str, n: int = 5) -> List[Tuple[str, float]]:
        """
        查找相似策略
        
        基于:
        1. 使用相同因子
        2. 基于相同论文
        3. 改进自相似策略
        """
        if self.use_neo4j:
            return self._find_similar_neo4j(strategy_id, n)
        else:
            return self._find_similar_sqlite(strategy_id, n)
    
    def _find_similar_sqlite(self, strategy_id: str, n: int) -> List[Tuple[str, float]]:
        """在 SQLite 中查找相似策略"""
        # 获取策略使用的因子
        relations = self._get_relations_sqlite(strategy_id, RelationType.USES_FACTOR, "out")
        factor_ids = [r.target_id for r in relations]
        
        if not factor_ids:
            return []
        
        # 查找使用相同因子的其他策略
        conn = sqlite3.connect(self.fallback_db)
        cursor = conn.cursor()
        
        similar_scores = {}
        
        for factor_id in factor_ids:
            cursor.execute('''
                SELECT source_id FROM relations 
                WHERE target_id = ? AND relation_type = ? AND source_id != ?
            ''', (factor_id, RelationType.USES_FACTOR.value, strategy_id))
            
            for row in cursor.fetchall():
                other_strategy = row[0]
                similar_scores[other_strategy] = similar_scores.get(other_strategy, 0) + 1
        
        conn.close()
        
        # 排序并返回
        sorted_strategies = sorted(similar_scores.items(), key=lambda x: -x[1])
        return sorted_strategies[:n]
    
    def get_strategy_lineage(self, strategy_id: str) -> Dict:
        """
        获取策略的进化谱系
        
        Returns:
            {
                "ancestors": [...],  # 祖先策略
                "descendants": [...], # 后代策略
                "influenced_by": [...], # 受哪些策略影响
                "improvements": [...] # 改进了哪些策略
            }
        """
        lineage = {
            "ancestors": [],
            "descendants": [],
            "influenced_by": [],
            "improvements": [],
            "papers": [],
            "factors": []
        }
        
        # 获取所有关系
        relations = self.get_relations(strategy_id, direction="both")
        
        for rel in relations:
            if rel.relation_type == RelationType.DERIVED_FROM:
                if rel.target_id == strategy_id:
                    lineage["ancestors"].append(rel.source_id)
                else:
                    lineage["descendants"].append(rel.target_id)
            
            elif rel.relation_type == RelationType.IMPROVES:
                if rel.target_id == strategy_id:
                    lineage["improvements"].append(rel.source_id)
                else:
                    lineage["influenced_by"].append(rel.target_id)
            
            elif rel.relation_type == RelationType.IMPLEMENTS:
                lineage["papers"].append(rel.target_id)
            
            elif rel.relation_type == RelationType.USES_FACTOR:
                lineage["factors"].append(rel.target_id)
        
        return lineage
    
    def recommend_strategies(self, user_strategy_ids: List[str], n: int = 5) -> List[Tuple[str, float, str]]:
        """
        基于用户已有策略推荐新策略
        
        Returns:
            [(strategy_id, score, reason), ...]
        """
        recommendations = {}
        
        for strategy_id in user_strategy_ids:
            # 获取策略谱系
            lineage = self.get_strategy_lineage(strategy_id)
            
            # 推荐改进版本
            for ancestor in lineage["ancestors"]:
                if ancestor not in user_strategy_ids:
                    recommendations[ancestor] = recommendations.get(ancestor, 0) + 0.8
            
            # 推荐使用相同因子但不同的策略
            similar = self.find_similar_strategies(strategy_id, n=3)
            for sim_id, sim_score in similar:
                if sim_id not in user_strategy_ids:
                    recommendations[sim_id] = recommendations.get(sim_id, 0) + sim_score * 0.5
            
            # 推荐基于相同论文的策略
            for paper_id in lineage["papers"]:
                # 查找其他实现相同论文的策略
                paper_relations = self.get_relations(paper_id, RelationType.IMPLEMENTS, "in")
                for rel in paper_relations:
                    if rel.source_id not in user_strategy_ids and rel.source_id != strategy_id:
                        recommendations[rel.source_id] = recommendations.get(rel.source_id, 0) + 0.6
        
        # 排序并添加理由
        sorted_recs = sorted(recommendations.items(), key=lambda x: -x[1])
        
        results = []
        for strategy_id, score in sorted_recs[:n]:
            reason = self._generate_recommendation_reason(strategy_id, user_strategy_ids)
            results.append((strategy_id, score, reason))
        
        return results
    
    def _generate_recommendation_reason(self, strategy_id: str, user_strategies: List[str]) -> str:
        """生成推荐理由"""
        lineage = self.get_strategy_lineage(strategy_id)
        
        # 检查是否是改进版本
        for ancestor in lineage["ancestors"]:
            if ancestor in user_strategies:
                return f"改进自你已有的策略"
        
        # 检查是否使用相同因子
        for factor in lineage["factors"]:
            for user_strat in user_strategies:
                user_lineage = self.get_strategy_lineage(user_strat)
                if factor in user_lineage["factors"]:
                    return f"使用与你已有策略相似的因子"
        
        # 检查是否基于相同论文
        for paper in lineage["papers"]:
            for user_strat in user_strategies:
                user_lineage = self.get_strategy_lineage(user_strat)
                if paper in user_lineage["papers"]:
                    return f"基于你已有策略使用的论文"
        
        return "可能符合你的投资风格"
    
    # ==================== 批量导入 ====================
    
    def import_from_evolution_ecosystem(self, evolution_db_path: str):
        """从进化生态系统导入数据"""
        conn = sqlite3.connect(evolution_db_path)
        cursor = conn.cursor()
        
        # 导入基因作为 Factor
        try:
            cursor.execute('SELECT * FROM genes')
            for row in cursor.fetchall():
                gene_id = row[0]
                name = row[1]
                formula = row[3]
                
                self.create_entity(
                    EntityType.FACTOR,
                    name,
                    {"formula": formula, "source": "evolution_ecosystem"},
                    entity_id=gene_id
                )
        except:
            pass
        
        # 导入 Capsule 作为 Strategy
        try:
            cursor.execute('SELECT * FROM capsules')
            for row in cursor.fetchall():
                capsule_id = row[0]
                gene_id = row[1]
                sharpe = row[5]
                
                self.create_entity(
                    EntityType.STRATEGY,
                    f"Strategy_{capsule_id}",
                    {"sharpe_ratio": sharpe, "source": "evolution_ecosystem"},
                    entity_id=capsule_id
                )
                
                # 创建关系
                if gene_id:
                    self.create_relation(capsule_id, gene_id, RelationType.USES_FACTOR)
        except:
            pass
        
        conn.close()
        print(f"✅ Imported data from {evolution_db_path}")


# ==================== 演示 ====================

def demo_knowledge_graph():
    """演示知识图谱"""
    print("="*80)
    print("QuantClaw Knowledge Graph Demo")
    print("="*80)
    
    # 创建知识图谱 (使用 SQLite 备用)
    kg = QuantKnowledgeGraph(fallback_db="demo_kg.db")
    
    # 1. 创建实体
    print("\n[Step 1] Creating entities...")
    
    # 论文
    paper1 = kg.create_entity(
        EntityType.PAPER,
        "Entropy-Regularized Portfolio Optimization",
        {"arxiv_id": "1234.5678", "authors": ["Smith", "Johnson"], "year": 2024}
    )
    print(f"   Created paper: {paper1}")
    
    # 作者
    author1 = kg.create_entity(EntityType.AUTHOR, "Dr. Smith", {"affiliation": "MIT"})
    
    # 因子
    factor1 = kg.create_entity(
        EntityType.FACTOR,
        "Entropy_Sample",
        {"formula": "SampEn(m=2, r=0.2)", "category": "complexity"}
    )
    factor2 = kg.create_entity(
        EntityType.FACTOR,
        "Hurst_Exponent",
        {"formula": "H = R/S analysis", "category": "trend"}
    )
    
    # 策略
    strategy1 = kg.create_entity(
        EntityType.STRATEGY,
        "EntropyMomentum Pro",
        {"sharpe": 1.8, "max_dd": 0.15, "win_rate": 0.62}
    )
    strategy2 = kg.create_entity(
        EntityType.STRATEGY,
        "EntropyMomentum Lite",
        {"sharpe": 1.5, "max_dd": 0.12, "win_rate": 0.58}
    )
    
    # 2. 创建关系
    print("\n[Step 2] Creating relations...")
    
    kg.create_relation(strategy1, paper1, RelationType.IMPLEMENTS)
    kg.create_relation(strategy1, factor1, RelationType.USES_FACTOR)
    kg.create_relation(strategy1, factor2, RelationType.USES_FACTOR)
    kg.create_relation(paper1, author1, RelationType.WRITTEN_BY)
    
    kg.create_relation(strategy2, strategy1, RelationType.DERIVED_FROM)
    kg.create_relation(strategy2, factor1, RelationType.USES_FACTOR)
    
    print(f"   Created relations")
    
    # 3. 查询相似策略
    print("\n[Step 3] Finding similar strategies...")
    similar = kg.find_similar_strategies(strategy1, n=5)
    print(f"   Strategies similar to {strategy1}:")
    for sim_id, score in similar:
        entity = kg.get_entity(sim_id)
        if entity:
            print(f"   - {entity.name} (score: {score})")
    
    # 4. 获取策略谱系
    print("\n[Step 4] Strategy lineage...")
    lineage = kg.get_strategy_lineage(strategy1)
    print(f"   Factors used: {lineage['factors']}")
    print(f"   Based on papers: {lineage['papers']}")
    print(f"   Descendants: {lineage['descendants']}")
    
    # 5. 策略推荐
    print("\n[Step 5] Strategy recommendations...")
    recs = kg.recommend_strategies([strategy2], n=3)
    print(f"   Recommendations for user with strategy {strategy2}:")
    for strat_id, score, reason in recs:
        entity = kg.get_entity(strat_id)
        if entity:
            print(f"   - {entity.name} (score: {score:.2f}): {reason}")
    
    # 6. 路径查找
    print("\n[Step 6] Path finding...")
    paths = kg.find_path(strategy2, author1, max_depth=3)
    print(f"   Paths from strategy to author:")
    for path in paths:
        print(f"   {' -> '.join(path)}")
    
    print("\n" + "="*80)
    print("Knowledge Graph Demo Complete!")
    print("="*80)
    
    return kg


if __name__ == "__main__":
    kg = demo_knowledge_graph()
