"""
QuantClaw Pro - MBTI 股性分类系统
知识图谱模块 (Knowledge Graph) - Neo4j集成
Phase 4: Week 7-8

实现股性数据的持久化存储和持续学习
"""

import numpy as np
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 尝试导入py2neo，如果没有安装则使用模拟实现
try:
    from py2neo import Graph, Node, Relationship, NodeMatcher
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("py2neo not installed. Running in mock mode.")


class MockGraph:
    """Neo4j模拟类（用于开发和测试）"""
    
    def __init__(self, *args, **kwargs):
        self.data_store = {
            'nodes': {},
            'relationships': []
        }
        logger.info("Using MockGraph (Neo4j not available)")
    
    def run(self, query: str, **parameters) -> Any:
        """模拟执行Cypher查询"""
        logger.debug(f"Mock query: {query[:50]}...")
        return MockResult()
    
    def create(self, node) -> None:
        """模拟创建节点"""
        pass
    
    def push(self, node) -> None:
        """模拟推送节点"""
        pass


class MockResult:
    """模拟查询结果"""
    
    def data(self) -> List[Dict]:
        return []
    
    def __iter__(self):
        return iter([])


class PersonalityKnowledgeGraph:
    """
    股性知识图谱操作类
    管理股票性格、策略匹配和市场环境的数据
    """
    
    def __init__(self, 
                 uri: str = "bolt://localhost:7687",
                 user: str = "neo4j",
                 password: str = "password"):
        """
        初始化知识图谱连接
        
        Args:
            uri: Neo4j连接URI
            user: 用户名
            password: 密码
        """
        if NEO4J_AVAILABLE:
            try:
                self.graph = Graph(uri, auth=(user, password))
                self.matcher = NodeMatcher(self.graph)
                logger.info("Connected to Neo4j database")
                self._initialize_schema()
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                self.graph = MockGraph()
                self.matcher = None
        else:
            self.graph = MockGraph()
            self.matcher = None
    
    def _initialize_schema(self) -> None:
        """初始化数据库Schema（约束和索引）"""
        constraints = [
            "CREATE CONSTRAINT stock_ticker IF NOT EXISTS FOR (s:Stock) REQUIRE s.ticker IS UNIQUE",
            "CREATE CONSTRAINT personality_code IF NOT EXISTS FOR (p:Personality) REQUIRE p.code IS UNIQUE",
            "CREATE CONSTRAINT strategy_id IF NOT EXISTS FOR (st:Strategy) REQUIRE st.id IS UNIQUE",
            "CREATE CONSTRAINT snapshot_id IF NOT EXISTS FOR (ps:PersonalitySnapshot) REQUIRE ps.id IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                self.graph.run(constraint)
            except Exception as e:
                logger.warning(f"Constraint creation failed: {e}")
        
        logger.info("Schema initialized")
    
    # ========== 股票节点操作 ==========
    
    def create_stock(self, ticker: str, name: str, sector: str,
                     market_cap: float, exchange: str = "US") -> bool:
        """
        创建股票节点
        
        Args:
            ticker: 股票代码
            name: 公司名称
            sector: 行业
            market_cap: 市值
            exchange: 交易所
            
        Returns:
            是否成功
        """
        query = """
        MERGE (s:Stock {ticker: $ticker})
        SET s.name = $name,
            s.sector = $sector,
            s.market_cap = $market_cap,
            s.exchange = $exchange,
            s.updated_at = datetime()
        RETURN s
        """
        try:
            self.graph.run(query, ticker=ticker, name=name,
                         sector=sector, market_cap=market_cap,
                         exchange=exchange)
            logger.info(f"Created/Updated stock node: {ticker}")
            return True
        except Exception as e:
            logger.error(f"Failed to create stock node: {e}")
            return False
    
    def get_stock(self, ticker: str) -> Optional[Dict]:
        """获取股票节点"""
        query = """
        MATCH (s:Stock {ticker: $ticker})
        RETURN s.ticker, s.name, s.sector, s.market_cap
        """
        try:
            result = self.graph.run(query, ticker=ticker).data()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get stock: {e}")
            return None
    
    # ========== 性格节点操作 ==========
    
    def initialize_personalities(self) -> bool:
        """初始化16型性格节点"""
        personalities = [
            {'code': 'INTJ', 'name': '战略大师', 'category': 'Analysts', 'risk': 'High'},
            {'code': 'INTP', 'name': '逻辑解谜者', 'category': 'Analysts', 'risk': 'High'},
            {'code': 'ENTJ', 'name': '霸道总裁', 'category': 'Analysts', 'risk': 'Medium'},
            {'code': 'ENTP', 'name': '辩论家', 'category': 'Analysts', 'risk': 'High'},
            {'code': 'INFJ', 'name': '逆向先知', 'category': 'Diplomats', 'risk': 'High'},
            {'code': 'INFP', 'name': '梦想家', 'category': 'Diplomats', 'risk': 'Extreme'},
            {'code': 'ENFJ', 'name': '魅力领袖', 'category': 'Diplomats', 'risk': 'Medium'},
            {'code': 'ENFP', 'name': '创新先锋', 'category': 'Diplomats', 'risk': 'High'},
            {'code': 'ISTJ', 'name': '稳健守护者', 'category': 'Sentinels', 'risk': 'Low'},
            {'code': 'ISFJ', 'name': '价值守望者', 'category': 'Sentinels', 'risk': 'Low'},
            {'code': 'ESTJ', 'name': '效率机器', 'category': 'Sentinels', 'risk': 'Medium'},
            {'code': 'ESFJ', 'name': '群体领袖', 'category': 'Sentinels', 'risk': 'Medium'},
            {'code': 'ISTP', 'name': '敏捷猎手', 'category': 'Explorers', 'risk': 'High'},
            {'code': 'ISFP', 'name': '艺术玩家', 'category': 'Explorers', 'risk': 'Extreme'},
            {'code': 'ESTP', 'name': '短线狂徒', 'category': 'Explorers', 'risk': 'Extreme'},
            {'code': 'ESFP', 'name': '派对动物', 'category': 'Explorers', 'risk': 'Extreme'}
        ]
        
        query = """
        UNWIND $personalities AS p
        MERGE (personality:Personality {code: p.code})
        SET personality.name = p.name,
            personality.category = p.category,
            personality.risk_level = p.risk,
            personality.created_at = datetime()
        """
        
        try:
            self.graph.run(query, personalities=personalities)
            logger.info("Initialized 16 personality types")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize personalities: {e}")
            return False
    
    # ========== 性格快照操作 ==========
    
    def create_personality_snapshot(self, ticker: str,
                                    ie_score: float, ns_score: float,
                                    tf_score: float, jp_score: float,
                                    confidence: float,
                                    snapshot_date: Optional[date] = None) -> bool:
        """
        创建性格快照
        
        Args:
            ticker: 股票代码
            ie_score: I/E维度分数
            ns_score: N/S维度分数
            tf_score: T/F维度分数
            jp_score: J/P维度分数
            confidence: 分类置信度
            snapshot_date: 快照日期
            
        Returns:
            是否成功
        """
        snapshot_date = snapshot_date or date.today()
        snapshot_id = f"{ticker}_{snapshot_date}"
        
        # 确定MBTI代码
        mbti_code = self._scores_to_mbti(ie_score, ns_score, tf_score, jp_score)
        
        query = """
        // 创建快照节点
        CREATE (ps:PersonalitySnapshot {
            id: $snapshot_id,
            date: date($snapshot_date),
            ie_score: $ie_score,
            ns_score: $ns_score,
            tf_score: $tf_score,
            jp_score: $jp_score,
            confidence: $confidence,
            created_at: datetime()
        })
        
        // 关联到股票
        WITH ps
        MATCH (s:Stock {ticker: $ticker})
        CREATE (s)-[:HAS_SNAPSHOT {date: date($snapshot_date)}]->(ps)
        
        // 关联到性格类型
        WITH ps
        MATCH (p:Personality {code: $mbti_code})
        CREATE (ps)-[:SNAPSHOT_OF]->(p)
        
        RETURN ps.id
        """
        
        try:
            self.graph.run(query,
                         snapshot_id=snapshot_id,
                         snapshot_date=str(snapshot_date),
                         ticker=ticker,
                         ie_score=ie_score,
                         ns_score=ns_score,
                         tf_score=tf_score,
                         jp_score=jp_score,
                         confidence=confidence,
                         mbti_code=mbti_code)
            logger.info(f"Created personality snapshot: {snapshot_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            return False
    
    def _scores_to_mbti(self, ie: float, ns: float, tf: float, jp: float) -> str:
        """将四维分数转换为MBTI代码"""
        code = ""
        code += "E" if ie > 0.5 else "I"
        code += "N" if ns > 0.5 else "S"
        code += "F" if tf > 0.5 else "T"
        code += "J" if jp > 0.5 else "P"
        return code
    
    def get_personality_history(self, ticker: str, limit: int = 10) -> List[Dict]:
        """获取股票性格历史"""
        query = """
        MATCH (s:Stock {ticker: $ticker})-[:HAS_SNAPSHOT]->(ps:PersonalitySnapshot)
        MATCH (ps)-[:SNAPSHOT_OF]->(p:Personality)
        RETURN ps.date AS date, p.code AS personality, p.name AS name,
               ps.ie_score, ps.ns_score, ps.tf_score, ps.jp_score,
               ps.confidence
        ORDER BY ps.date DESC
        LIMIT $limit
        """
        try:
            return self.graph.run(query, ticker=ticker, limit=limit).data()
        except Exception as e:
            logger.error(f"Failed to get personality history: {e}")
            return []
    
    # ========== 策略兼容性操作 ==========
    
    def update_strategy_compatibility(self,
                                     personality_code: str,
                                     strategy_name: str,
                                     win_rate: float,
                                     avg_return: float,
                                     sharpe_ratio: float,
                                     sample_count: int = 1) -> bool:
        """
        更新性格-策略兼容性
        
        使用指数加权平均更新历史数据
        """
        query = """
        MATCH (p:Personality {code: $personality_code})
        MATCH (st:Strategy {name: $strategy_name})
        MERGE (p)-[cw:COMPATIBLE_WITH]->(st)
        ON CREATE SET cw.win_rate = $win_rate,
                      cw.avg_return = $avg_return,
                      cw.sharpe_ratio = $sharpe_ratio,
                      cw.sample_count = $sample_count,
                      cw.first_seen = datetime(),
                      cw.last_updated = datetime()
        ON MATCH SET cw.win_rate = (cw.win_rate * cw.sample_count + $win_rate * $sample_count) 
                                  / (cw.sample_count + $sample_count),
                     cw.avg_return = (cw.avg_return * cw.sample_count + $avg_return * $sample_count) 
                                   / (cw.sample_count + $sample_count),
                     cw.sharpe_ratio = (cw.sharpe_ratio * cw.sample_count + $sharpe_ratio * $sample_count) 
                                     / (cw.sample_count + $sample_count),
                     cw.sample_count = cw.sample_count + $sample_count,
                     cw.last_updated = datetime()
        RETURN p.code, st.name, cw.win_rate, cw.sample_count
        """
        
        try:
            self.graph.run(query,
                         personality_code=personality_code,
                         strategy_name=strategy_name,
                         win_rate=win_rate,
                         avg_return=avg_return,
                         sharpe_ratio=sharpe_ratio,
                         sample_count=sample_count)
            logger.info(f"Updated compatibility: {personality_code} -> {strategy_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update compatibility: {e}")
            return False
    
    def get_recommended_strategies(self, personality_code: str, 
                                   top_n: int = 3) -> List[Dict]:
        """获取推荐策略"""
        query = """
        MATCH (p:Personality {code: $personality_code})
              -[cw:COMPATIBLE_WITH]->(st:Strategy)
        RETURN st.name AS strategy,
               st.description AS description,
               cw.win_rate AS win_rate,
               cw.avg_return AS avg_return,
               cw.sharpe_ratio AS sharpe,
               cw.sample_count AS samples
        ORDER BY cw.sharpe_ratio DESC, cw.win_rate DESC
        LIMIT $top_n
        """
        try:
            return self.graph.run(query, 
                                personality_code=personality_code, 
                                top_n=top_n).data()
        except Exception as e:
            logger.error(f"Failed to get recommended strategies: {e}")
            return []
    
    # ========== 性格转变记录 ==========
    
    def record_personality_transition(self,
                                     ticker: str,
                                     old_personality: str,
                                     new_personality: str,
                                     trigger_event: str,
                                     reason: str) -> bool:
        """记录股票性格转变"""
        query = """
        MATCH (s:Stock {ticker: $ticker})
        MATCH (old:Personality {code: $old_personality})
        MATCH (new:Personality {code: $new_personality})
        CREATE (old)-[m:MUTATED_TO {
            mutation_date: date(),
            trigger_event: $trigger_event,
            reason: $reason,
            ticker: $ticker
        }]->(new)
        CREATE (s)-[:EXPERIENCED_TRANSITION {date: date()}]->(m)
        RETURN m
        """
        
        try:
            self.graph.run(query,
                         ticker=ticker,
                         old_personality=old_personality,
                         new_personality=new_personality,
                         trigger_event=trigger_event,
                         reason=reason)
            logger.info(f"Recorded transition: {ticker} {old_personality} -> {new_personality}")
            return True
        except Exception as e:
            logger.error(f"Failed to record transition: {e}")
            return False
    
    # ========== 统计查询 ==========
    
    def get_most_stable_personalities(self, min_samples: int = 10) -> List[Dict]:
        """获取最稳定的性格类型（转变最少）"""
        query = """
        MATCH (s:Stock)-[:HAS_SNAPSHOT]->(ps:PersonalitySnapshot)
               -[:SNAPSHOT_OF]->(p:Personality)
        WITH p, count(DISTINCT s) AS stock_count
        WHERE stock_count >= $min_samples
        OPTIONAL MATCH (p)<-[:MUTATED_TO]-(m)
        WITH p, stock_count, count(m) AS transitions
        RETURN p.code AS personality, p.name AS name,
               stock_count, transitions,
               CASE WHEN stock_count > 0 THEN transitions * 1.0 / stock_count ELSE 0 END AS transition_rate
        ORDER BY transition_rate ASC
        LIMIT 10
        """
        try:
            return self.graph.run(query, min_samples=min_samples).data()
        except Exception as e:
            logger.error(f"Failed to get stable personalities: {e}")
            return []
    
    def get_best_performing_strategies(self, personality_code: Optional[str] = None) -> List[Dict]:
        """获取表现最佳的策略"""
        if personality_code:
            query = """
            MATCH (p:Personality {code: $code})-[cw:COMPATIBLE_WITH]->(st:Strategy)
            WHERE cw.sample_count >= 10
            RETURN st.name AS strategy, p.code AS personality,
                   cw.win_rate, cw.avg_return, cw.sharpe_ratio, cw.sample_count
            ORDER BY cw.sharpe_ratio DESC
            LIMIT 10
            """
            params = {'code': personality_code}
        else:
            query = """
            MATCH (p:Personality)-[cw:COMPATIBLE_WITH]->(st:Strategy)
            WHERE cw.sample_count >= 10
            RETURN st.name AS strategy, p.code AS personality,
                   cw.win_rate, cw.avg_return, cw.sharpe_ratio, cw.sample_count
            ORDER BY cw.sharpe_ratio DESC
            LIMIT 10
            """
            params = {}
        
        try:
            return self.graph.run(query, **params).data()
        except Exception as e:
            logger.error(f"Failed to get best strategies: {e}")
            return []


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("QuantClaw Pro - 知识图谱模块测试")
    print("=" * 70)
    
    # 创建知识图谱实例（使用Mock模式）
    kg = PersonalityKnowledgeGraph()
    
    print("\n【测试1】初始化16型性格节点")
    print("-" * 70)
    success = kg.initialize_personalities()
    print(f"初始化结果: {'成功' if success else '失败'}")
    
    print("\n【测试2】创建股票节点")
    print("-" * 70)
    stocks = [
        ('AAPL', 'Apple Inc.', 'Technology', 3000000000000),
        ('TSLA', 'Tesla Inc.', 'Automotive', 800000000000),
        ('JNJ', 'Johnson & Johnson', 'Healthcare', 400000000000)
    ]
    for ticker, name, sector, cap in stocks:
        success = kg.create_stock(ticker, name, sector, cap)
        print(f"  {ticker}: {'✓' if success else '✗'}")
    
    print("\n【测试3】创建性格快照")
    print("-" * 70)
    snapshots = [
        ('AAPL', 0.35, 0.68, 0.42, 0.71, 0.82),
        ('TSLA', 0.75, 0.72, 0.65, 0.35, 0.78),
        ('JNJ', 0.25, 0.35, 0.45, 0.75, 0.85)
    ]
    for data in snapshots:
        success = kg.create_personality_snapshot(*data)
        print(f"  {data[0]}: {'✓' if success else '✗'}")
    
    print("\n【测试4】记录性格转变")
    print("-" * 70)
    success = kg.record_personality_transition(
        'TSLA', 'ENFP', 'ESTP', 'earnings_volatility', '财报波动导致性格转变'
    )
    print(f"转变记录: {'✓' if success else '✗'}")
    
    print("\n" + "=" * 70)
    print("知识图谱模块测试完成!")
    print("注: 当前运行在非Neo4j环境，使用Mock模式")
    print("=" * 70)
