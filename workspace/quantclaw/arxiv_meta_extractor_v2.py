#!/usr/bin/env python3
"""
ArXiv Meta-Extractor v2.0
梁文峰风格重构版

核心理念：
1. 不直接交易论文因子 → 提取 META-PATTERN（什么结构有效）
2. 负面筛选 → 识别失效模式，建立黑名单
3. 变异引擎 → 将论文逻辑拆解为可重组的基因片段

与 v1 的区别：
- v1: 论文 → 因子 → 基因池（直接注入，问题：发表即失效）
- v2: 论文 → 模式提取 → 变异素材库 → 交叉繁衍（间接价值）
"""

import sys
import re
import json
import hashlib
import sqlite3
import requests
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from xml.etree import ElementTree as ET
from collections import defaultdict

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from evolution_ecosystem import Gene


@dataclass 
class MetaPattern:
    """
    元模式 - 描述"什么样的因子结构可能有效"
    
    不是具体公式，而是抽象模板：
    - "价格突破 + 成交量确认" → 可实例化为多种具体实现
    - "均值回归 + 波动率过滤" → 同上
    """
    pattern_id: str
    name: str
    category: str  # momentum, mean_reversion, etc.
    
    # 结构描述
    logic_skeleton: str  # 逻辑骨架，如 "CONDITION_A AND CONDITION_B"
    condition_a: Dict    # 条件A的抽象描述
    condition_b: Dict    # 条件B的抽象描述
    
    # 来源追踪
    source_papers: List[str]  # 哪些论文出现此模式
    occurrence_count: int     # 出现次数
    
    # 有效性评估
    fitness_estimate: float   # 基于论文引用/年份的估计
    decay_risk: float         # 失效风险（老论文更高）
    
    # 可实例化模板
    instantiation_templates: List[Dict]  # 具体实现模板


@dataclass
class FailurePattern:
    """
    失效模式 - 记录已知的失败因子结构
    用于负面筛选，避免重复踩坑
    """
    pattern_id: str
    description: str
    failure_reason: str  # overfit, arbitrage_decay, data_mining
    source_evidence: List[str]  # 证据来源
    confidence: float


class ArxivMetaMiner:
    """
    arXiv 元模式挖掘器
    
    核心洞察：
    量化论文的价值不在于"具体公式"，而在于"结构有效性"的统计证据。
    如果 50 篇高质量论文都在用"动量+波动率过滤"，说明这个结构有价值，
    即使具体参数已失效。
    """
    
    # 逻辑骨架模板库
    SKELETON_PATTERNS = {
        'momentum_confirmation': {
            'skeleton': 'TREND_SIGNAL AND CONFIRMATION_SIGNAL',
            'description': '趋势信号需要确认信号过滤假突破',
            'examples': [
                'price_breakout AND volume_surge',
                'ma_crossover AND rsi_strength',
                'new_high AND momentum_acceleration'
            ]
        },
        'mean_reversion_filter': {
            'skeleton': 'EXTREME_DEVIATION AND REVERSION_CATALYST',
            'description': '极端偏离+反转催化剂',
            'examples': [
                'zscore_extreme AND volume_climax',
                'rsi_oversold AND bullish_divergence',
                'bollinger_break AND mean_attraction'
            ]
        },
        'volatility_regime': {
            'skeleton': 'VOLATILITY_CONDITION AND DIRECTIONAL_BIAS',
            'description': '波动率状态下的方向性偏向',
            'examples': [
                'low_vol_environment AND trend_following',
                'high_vol_spike AND mean_reversion',
                'vol_contraction AND breakout_setup'
            ]
        },
        'multi_timeframe': {
            'skeleton': 'HIGHER_TF_ALIGN AND LOWER_TF_ENTRY',
            'description': '多时间框架共振',
            'examples': [
                'weekly_uptrend AND daily_pullback',
                'monthly_breakout AND hourly_consolidation',
                'daily_support AND 15min_reversal'
            ]
        },
        'fundamental_technical': {
            'skeleton': 'FUNDAMENTAL_FILTER AND TECHNICAL_TRIGGER',
            'description': '基本面过滤+技术面触发',
            'examples': [
                'earnings_growth AND price_momentum',
                'value_cheap AND technical_breakout',
                'quality_high AND trend_following'
            ]
        }
    }
    
    # 关键词到条件的映射
    CONDITION_KEYWORDS = {
        'price_breakout': ['breakout', 'break through', 'exceeds', 'penetrates', 'surpasses'],
        'volume_surge': ['volume', 'turnover spike', 'increased volume', 'liquidity surge'],
        'ma_crossover': ['moving average', 'ma cross', 'golden cross', 'ma breakout'],
        'rsi_strength': ['rsi', 'relative strength', 'overbought', 'oversold'],
        'zscore_extreme': ['z-score', 'standard deviation', 'sigma', 'extreme deviation'],
        'volatility_low': ['low volatility', 'volatility compression', 'quiet period'],
        'volatility_high': ['high volatility', 'volatility expansion', 'volatile'],
        'trend_uptrend': ['uptrend', 'bullish trend', 'rising trend', 'positive trend'],
        'trend_downtrend': ['downtrend', 'bearish trend', 'falling trend', 'negative trend'],
        'support_level': ['support', 'demand zone', 'floor'],
        'resistance_level': ['resistance', 'supply zone', 'ceiling'],
    }
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.db_path = db_path
        self.meta_patterns: Dict[str, MetaPattern] = {}
        self.failure_patterns: List[FailurePattern] = []
        self.paper_metadata: Dict[str, Dict] = {}
        
    def analyze_papers(self, papers: List[Dict]) -> Dict:
        """
        批量分析论文，提取元模式
        """
        print("\n" + "="*70)
        print("🔬 META-PATTERN EXTRACTION")
        print("="*70)
        
        for paper in papers:
            self._analyze_single_paper(paper)
        
        # 聚合统计
        self._aggregate_patterns()
        
        # 生成报告
        return self._generate_report()
    
    def _analyze_single_paper(self, paper: Dict):
        """分析单篇论文"""
        text = f"{paper['title']} {paper.get('summary', '')}".lower()
        arxiv_id = paper['id']
        
        # 提取年份（用于 decay 评估）
        year = self._extract_year(paper.get('published', ''))
        
        # 1. 检测逻辑骨架匹配
        matched_skeletons = self._detect_skeletons(text)
        
        # 2. 提取具体条件
        detected_conditions = self._detect_conditions(text)
        
        # 3. 组合成元模式
        for skeleton_name in matched_skeletons:
            skeleton = self.SKELETON_PATTERNS[skeleton_name]
            
            # 尝试匹配条件
            condition_pairs = self._match_conditions_to_skeleton(
                skeleton, detected_conditions
            )
            
            for pair in condition_pairs:
                pattern_key = f"{skeleton_name}:{pair[0]}:{pair[1]}"
                
                if pattern_key not in self.meta_patterns:
                    self.meta_patterns[pattern_key] = MetaPattern(
                        pattern_id=hashlib.sha256(pattern_key.encode()).hexdigest()[:16],
                        name=f"{skeleton_name}_{pair[0]}_{pair[1]}",
                        category=self._categorize(skeleton_name),
                        logic_skeleton=skeleton['skeleton'],
                        condition_a={'type': pair[0], 'keywords': self.CONDITION_KEYWORDS.get(pair[0], [])},
                        condition_b={'type': pair[1], 'keywords': self.CONDITION_KEYWORDS.get(pair[1], [])},
                        source_papers=[arxiv_id],
                        occurrence_count=1,
                        fitness_estimate=self._estimate_fitness(year, paper),
                        decay_risk=self._calculate_decay_risk(year),
                        instantiation_templates=[]
                    )
                else:
                    pattern = self.meta_patterns[pattern_key]
                    pattern.occurrence_count += 1
                    pattern.source_papers.append(arxiv_id)
                    # 更新 fitness（取平均）
                    pattern.fitness_estimate = (
                        pattern.fitness_estimate * (pattern.occurrence_count - 1) +
                        self._estimate_fitness(year, paper)
                    ) / pattern.occurrence_count
        
        # 4. 检测失效模式信号
        self._detect_failure_signals(paper, text)
    
    def _detect_skeletons(self, text: str) -> List[str]:
        """检测文本匹配的逻辑骨架"""
        matched = []
        
        # 基于关键词组合匹配
        indicators = {
            'momentum_confirmation': ['momentum', 'trend', 'confirm', 'volume'],
            'mean_reversion_filter': ['reversion', 'mean', 'extreme', 'deviation'],
            'volatility_regime': ['volatility', 'regime', 'conditional', 'state'],
            'multi_timeframe': ['timeframe', 'frequency', 'daily', 'weekly', 'aggregate'],
            'fundamental_technical': ['fundamental', 'technical', 'filter', 'screen']
        }
        
        for skeleton, keywords in indicators.items():
            score = sum(1 for kw in keywords if kw in text)
            if score >= 2:  # 至少匹配2个关键词
                matched.append(skeleton)
        
        return matched
    
    def _detect_conditions(self, text: str) -> Set[str]:
        """检测文本中出现的条件类型"""
        detected = set()
        
        for condition, keywords in self.CONDITION_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    detected.add(condition)
                    break
        
        return detected
    
    def _match_conditions_to_skeleton(self, skeleton: Dict, conditions: Set[str]) -> List[Tuple[str, str]]:
        """将检测到的条件匹配到骨架的占位符"""
        pairs = []
        
        # 简化策略：随机组合两个检测到的条件
        # 实际应该用更智能的语义匹配
        conditions_list = list(conditions)
        
        if len(conditions_list) >= 2:
            for i in range(min(len(conditions_list), 3)):
                for j in range(i+1, min(len(conditions_list), 4)):
                    pairs.append((conditions_list[i], conditions_list[j]))
        
        return pairs
    
    def _extract_year(self, published: str) -> int:
        """从日期字符串提取年份"""
        try:
            return int(published[:4])
        except:
            return datetime.now().year
    
    def _estimate_fitness(self, year: int, paper: Dict) -> float:
        """
        基于论文元数据估计因子有效性
        
        启发式规则：
        - 新论文（2023+）：0.6（可能有生存偏差）
        - 经典论文（2015-2022）：0.7（经过时间考验）
        - 老论文（<2015）：0.4（可能已失效）
        """
        current_year = datetime.now().year
        age = current_year - year
        
        if age <= 2:
            return 0.6  # 新论文，可能有发表偏误
        elif age <= 8:
            return 0.7  # 黄金期
        else:
            return max(0.3, 0.7 - (age - 8) * 0.05)  # 线性衰减
    
    def _calculate_decay_risk(self, year: int) -> float:
        """计算失效风险"""
        age = datetime.now().year - year
        return min(0.9, age * 0.08)  # 每年8%风险累积
    
    def _categorize(self, skeleton_name: str) -> str:
        """分类"""
        mapping = {
            'momentum_confirmation': 'momentum',
            'mean_reversion_filter': 'mean_reversion',
            'volatility_regime': 'volatility',
            'multi_timeframe': 'multi_tf',
            'fundamental_technical': 'hybrid'
        }
        return mapping.get(skeleton_name, 'unknown')
    
    def _detect_failure_signals(self, paper: Dict, text: str):
        """检测论文中的失效信号"""
        failure_signals = [
            ('data mining', 'data_mining'),
            ('overfitting', 'overfit'),
            ('in-sample', 'overfit'),
            ('survivorship bias', 'bias'),
            ('transaction costs', 'friction'),
            ('no longer profitable', 'decay'),
            ('disappeared', 'decay'),
        ]
        
        for signal, reason in failure_signals:
            if signal in text:
                self.failure_patterns.append(FailurePattern(
                    pattern_id=hashlib.sha256(f"{paper['id']}:{signal}".encode()).hexdigest()[:16],
                    description=f"Detected in {paper['title'][:50]}",
                    failure_reason=reason,
                    source_evidence=[paper['id']],
                    confidence=0.6
                ))
    
    def _aggregate_patterns(self):
        """聚合统计，识别高频模式"""
        print(f"\n📊 Pattern Aggregation:")
        print(f"   Total unique patterns: {len(self.meta_patterns)}")
        print(f"   Failure signals detected: {len(self.failure_patterns)}")
        
        # 按出现次数排序
        sorted_patterns = sorted(
            self.meta_patterns.values(),
            key=lambda p: p.occurrence_count,
            reverse=True
        )
        
        print(f"\n   Top patterns by frequency:")
        for p in sorted_patterns[:5]:
            print(f"   - {p.name}: {p.occurrence_count} papers, fitness={p.fitness_estimate:.2f}")
    
    def _generate_report(self) -> Dict:
        """生成分析报告"""
        return {
            'patterns': [asdict(p) for p in self.meta_patterns.values()],
            'failures': [asdict(f) for f in self.failure_patterns],
            'stats': {
                'total_patterns': len(self.meta_patterns),
                'high_confidence_patterns': len([p for p in self.meta_patterns.values() if p.occurrence_count >= 3]),
                'failure_signals': len(self.failure_patterns)
            }
        }
    
    def save_to_db(self):
        """保存到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建元模式表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meta_patterns (
                pattern_id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                logic_skeleton TEXT,
                condition_a TEXT,
                condition_b TEXT,
                source_papers TEXT,
                occurrence_count INTEGER,
                fitness_estimate REAL,
                decay_risk REAL,
                created_at TEXT
            )
        ''')
        
        # 创建失效模式表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failure_patterns (
                pattern_id TEXT PRIMARY KEY,
                description TEXT,
                failure_reason TEXT,
                source_evidence TEXT,
                confidence REAL,
                created_at TEXT
            )
        ''')
        
        # 插入元模式
        for pattern in self.meta_patterns.values():
            cursor.execute('''
                INSERT OR REPLACE INTO meta_patterns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id,
                pattern.name,
                pattern.category,
                pattern.logic_skeleton,
                json.dumps(pattern.condition_a),
                json.dumps(pattern.condition_b),
                json.dumps(pattern.source_papers),
                pattern.occurrence_count,
                pattern.fitness_estimate,
                pattern.decay_risk,
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
        print(f"\n💾 Saved {len(self.meta_patterns)} patterns to database")


class MetaPatternInstantiator:
    """
    元模式实例化器
    
    将抽象的元模式转化为可执行的具体基因
    例如："价格突破 + 成交量确认" → 具体的 `close > max(high[-20:]) AND volume > mean(volume[-20:]) * 1.5`
    """
    
    # 条件到代码的映射
    CONDITION_TEMPLATES = {
        'price_breakout': {
            'python': 'close > max(high[-{period}:])',
            'params': {'period': [10, 20, 60]}
        },
        'volume_surge': {
            'python': 'volume > mean(volume[-{period}:]) * {mult}',
            'params': {'period': [20], 'mult': [1.5, 2.0, 3.0]}
        },
        'rsi_strength': {
            'python': 'RSI(close, {period}) {op} {threshold}',
            'params': {'period': [14], 'op': ['>', '<'], 'threshold': [30, 70]}
        },
        'ma_crossover': {
            'python': 'MA(close, {fast}) {op} MA(close, {slow})',
            'params': {'fast': [5, 10, 20], 'slow': [20, 60, 120], 'op': ['>', '<']}
        },
        'zscore_extreme': {
            'python': 'abs((close - mean(close[-{period}:])) / std(close[-{period}:])) > {threshold}',
            'params': {'period': [20, 60], 'threshold': [2.0, 2.5, 3.0]}
        },
        'volatility_low': {
            'python': 'ATR(close, {period}) / close < {threshold}',
            'params': {'period': [14], 'threshold': [0.02, 0.03, 0.05]}
        },
        'trend_uptrend': {
            'python': 'close > MA(close, {period})',
            'params': {'period': [20, 60, 120]}
        },
        'support_level': {
            'python': 'close >= min(low[-{period}:]) * (1 + {tolerance})',
            'params': {'period': [20, 60], 'tolerance': [0.0, 0.02]}
        }
    }
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.db_path = db_path
    
    def instantiate(self, meta_pattern: MetaPattern, max_instances: int = 5) -> List[Gene]:
        """
        将元模式实例化为具体基因
        
        使用笛卡尔积生成参数组合，但限制数量避免爆炸
        """
        genes = []
        
        cond_a = meta_pattern.condition_a.get('type')
        cond_b = meta_pattern.condition_b.get('type')
        
        template_a = self.CONDITION_TEMPLATES.get(cond_a)
        template_b = self.CONDITION_TEMPLATES.get(cond_b)
        
        if not template_a or not template_b:
            return genes
        
        # 生成参数组合（限制数量）
        import itertools
        
        params_a_list = self._generate_param_combinations(template_a['params'])
        params_b_list = self._generate_param_combinations(template_b['params'])
        
        count = 0
        for pa in params_a_list[:3]:  # 限制每条件3种
            for pb in params_b_list[:3]:
                if count >= max_instances:
                    break
                
                # 构建公式
                formula_a = template_a['python'].format(**pa)
                formula_b = template_b['python'].format(**pb)
                full_formula = f"({formula_a}) AND ({formula_b})"
                
                # 创建基因
                gene = Gene(
                    gene_id=hashlib.sha256(full_formula.encode()).hexdigest()[:16],
                    name=f"META_{meta_pattern.name}_{count}",
                    description=f"Instantiated from {meta_pattern.name}",
                    formula=full_formula,
                    parameters={**pa, **pb, 'meta_pattern_id': meta_pattern.pattern_id},
                    source=f"meta_pattern:{meta_pattern.pattern_id}",
                    author="MetaInstantiator",
                    created_at=datetime.now(),
                    generation=1
                )
                
                genes.append(gene)
                count += 1
        
        return genes
    
    def _generate_param_combinations(self, params: Dict) -> List[Dict]:
        """生成参数组合"""
        keys = list(params.keys())
        values = [params[k] if isinstance(params[k], list) else [params[k]] for k in keys]
        
        import itertools
        combinations = []
        for combo in itertools.product(*values):
            combinations.append(dict(zip(keys, combo)))
        
        return combinations
    
    def batch_instantiate(self, min_occurrence: int = 3, dry_run: bool = False) -> List[Gene]:
        """
        批量实例化高频元模式
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取高频模式
        cursor.execute('''
            SELECT * FROM meta_patterns 
            WHERE occurrence_count >= ? 
            ORDER BY occurrence_count DESC
        ''', (min_occurrence,))
        
        rows = cursor.fetchall()
        conn.close()
        
        all_genes = []
        
        print(f"\n🧬 Instantiating {len(rows)} high-frequency patterns...")
        
        for row in rows:
            pattern = MetaPattern(
                pattern_id=row[0],
                name=row[1],
                category=row[2],
                logic_skeleton=row[3],
                condition_a=json.loads(row[4]),
                condition_b=json.loads(row[5]),
                source_papers=json.loads(row[6]),
                occurrence_count=row[7],
                fitness_estimate=row[8],
                decay_risk=row[9],
                instantiation_templates=[]
            )
            
            genes = self.instantiate(pattern, max_instances=3)
            all_genes.extend(genes)
            
            print(f"   {pattern.name}: {len(genes)} instances")
        
        if not dry_run:
            self._save_genes(all_genes)
        
        return all_genes
    
    def _save_genes(self, genes: List[Gene]):
        """保存基因到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        inserted = 0
        for gene in genes:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO genes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    gene.gene_id, gene.name, gene.description, gene.formula,
                    json.dumps(gene.parameters), gene.source, gene.author,
                    gene.created_at.isoformat(), gene.parent_gene_id, gene.generation
                ))
                if cursor.rowcount > 0:
                    inserted += 1
            except:
                pass
        
        conn.commit()
        conn.close()
        print(f"\n💾 Saved {inserted}/{len(genes)} instantiated genes")


# 命令行接口
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='ArXiv Meta-Extractor v2.0')
    parser.add_argument('--fetch', '-f', action='store_true', help='Fetch papers from arXiv')
    parser.add_argument('--search', '-s', default='factor investing momentum', help='Search query')
    parser.add_argument('--limit', '-l', type=int, default=50, help='Paper limit')
    parser.add_argument('--instantiate', '-i', action='store_true', help='Instantiate meta patterns')
    parser.add_argument('--min-occurrence', '-m', type=int, default=3, help='Min occurrence for instantiation')
    parser.add_argument('--db', default='evolution_hub.db', help='Database path')
    
    args = parser.parse_args()
    
    if args.fetch:
        # 获取论文
        print("Fetching papers from arXiv...")
        # 这里复用 v1 的 API 客户端
        sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')
        from arxiv_gene_extractor import ArXivAPI
        
        api = ArXivAPI()
        papers = api.search(args.search, max_results=args.limit)
        
        # 分析
        miner = ArxivMetaMiner(args.db)
        report = miner.analyze_papers(papers)
        miner.save_to_db()
        
        print(f"\n✅ Analysis complete: {report['stats']['total_patterns']} patterns extracted")
    
    if args.instantiate:
        # 实例化
        instantiator = MetaPatternInstantiator(args.db)
        genes = instantiator.batch_instantiate(min_occurrence=args.min_occurrence)
        print(f"\n✅ Instantiation complete: {len(genes)} genes created")
