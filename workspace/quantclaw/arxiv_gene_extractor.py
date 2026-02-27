#!/usr/bin/env python3
"""
ArXiv Gene Extractor (AGE)
从 arXiv 论文中提取量化因子并注入基因池

Usage:
    python3 arxiv_gene_extractor.py --search "factor investing momentum" --limit 50
    python3 arxiv_gene_extractor.py --paper 1234.5678 --inject
"""

import sys
import re
import json
import hashlib
import argparse
import requests
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from xml.etree import ElementTree as ET

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from evolution_ecosystem import Gene


@dataclass
class ExtractedFactor:
    """从论文中提取的原始因子"""
    name: str
    formula: str
    description: str
    source_arxiv: str
    confidence: float  # 0-1, 提取置信度
    category: str  # momentum, value, volatility, etc.
    raw_text: str  # 原始文本片段


class ArXivAPI:
    """arXiv API 客户端"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    # 量化金融相关分类
    RELEVANT_CATEGORIES = [
        'q-fin.TR',   # Trading and Market Microstructure
        'q-fin.PM',   # Portfolio Management
        'q-fin.ST',   # Statistical Finance
        'q-fin.CP',   # Computational Finance
        'q-fin.MF',   # Mathematical Finance
        'cs.LG',      # Machine Learning
        'cs.AI',      # Artificial Intelligence
        'stat.ML',    # Statistics - Machine Learning
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArXivGeneExtractor/1.0 (quant research)'
        })
    
    def search(self, query: str, max_results: int = 50, start: int = 0) -> List[Dict]:
        """
        搜索 arXiv 论文
        
        Args:
            query: 搜索关键词
            max_results: 最大返回数量
            start: 起始位置
        """
        params = {
            'search_query': query,
            'start': start,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        try:
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            return self._parse_feed(response.text)
        except Exception as e:
            print(f"❌ arXiv API error: {e}")
            return []
    
    def _parse_feed(self, xml_content: str) -> List[Dict]:
        """解析 arXiv Atom feed"""
        papers = []
        root = ET.fromstring(xml_content)
        
        # arXiv 使用 Atom 命名空间
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        for entry in root.findall('atom:entry', ns):
            paper = {
                'id': entry.find('atom:id', ns).text.split('/')[-1],
                'title': entry.find('atom:title', ns).text.strip().replace('\n', ' '),
                'summary': entry.find('atom:summary', ns).text.strip() if entry.find('atom:summary', ns) else '',
                'published': entry.find('atom:published', ns).text if entry.find('atom:published', ns) else '',
                'categories': [cat.get('term') for cat in entry.findall('atom:category', ns)],
                'pdf_url': None
            }
            
            # 获取 PDF 链接
            for link in entry.findall('atom:link', ns):
                if link.get('title') == 'pdf':
                    paper['pdf_url'] = link.get('href')
                    break
            
            papers.append(paper)
        
        return papers
    
    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict]:
        """通过 ID 获取单篇论文"""
        query = f"id_list={arxiv_id}"
        results = self.search(query, max_results=1)
        return results[0] if results else None


class FactorExtractor:
    """因子提取器 - 从论文文本中识别量化策略"""
    
    # 因子模式库
    FACTOR_PATTERNS = {
        'momentum': {
            'keywords': ['momentum', 'trend', 'past return', 'price continuation'],
            'formulas': [
                r'(?i)(?:momentum|mom)\s*=\s*[^\n]+',
                r'(?i)past\s+\d+[-\s]month\s+return',
                r'(?i)(?:12[-\s]month|6[-\s]month)\s+momentum',
            ]
        },
        'value': {
            'keywords': ['value', 'book-to-market', ' earnings-to-price', 'pe ratio'],
            'formulas': [
                r'(?i)(?:book[-\s]to[-\s]market|btm)\s*=\s*[^\n]+',
                r'(?i)(?:earnings[-\s]to[-\s]price|ep)\s*=\s*[^\n]+',
                r'(?i)P/E\s+ratio',
            ]
        },
        'volatility': {
            'keywords': ['volatility', 'standard deviation', 'variance', 'garch', 'realized vol'],
            'formulas': [
                r'(?i)(?:realized\s+volatility|rv)\s*=\s*[^\n]+',
                r'(?i)std\s*\(\s*returns?\s*\)',
                r'(?i)GARCH\(\s*\d+\s*,\s*\d+\s*\)',
            ]
        },
        'quality': {
            'keywords': ['quality', 'profitability', 'roe', 'roa', 'gross profit'],
            'formulas': [
                r'(?i)(?:return\s+on\s+equity|roe)\s*=\s*[^\n]+',
                r'(?i)(?:return\s+on\s+assets|roa)\s*=\s*[^\n]+',
                r'(?i)gross\s+profitability',
            ]
        },
        'mean_reversion': {
            'keywords': ['mean reversion', 'reversal', 'contrarian', 'oversold'],
            'formulas': [
                r'(?i)(?:mean\s+reversion|reversal)\s+[^\n]+',
                r'(?i)(?:RSI|relative\s+strength\s+index)\s*<\s*\d+',
                r'(?i)z[-\s]score\s*=\s*[^\n]+',
            ]
        },
        'size': {
            'keywords': ['size', 'market cap', 'small cap', 'large cap'],
            'formulas': [
                r'(?i)(?:market\s+capitalization|market\s+cap)\s*=\s*[^\n]+',
                r'(?i)log\s*\(\s*market\s+value\s*\)',
                r'(?i)SMB|size\s+factor',
            ]
        },
        'liquidity': {
            'keywords': ['liquidity', 'turnover', 'volume', 'amihud'],
            'formulas': [
                r'(?i)(?:amihud|illiquidity)\s+ratio',
                r'(?i)turnover\s*=\s*[^\n]+',
                r'(?i)dollar\s+volume',
            ]
        },
        'low_beta': {
            'keywords': ['beta', 'low beta', 'market beta', 'bab'],
            'formulas': [
                r'(?i)(?:betting\s+against\s+beta|bab)',
                r'(?i)(?:market\s+beta|beta)\s*=\s*[^\n]+',
                r'(?i)cov\s*\(\s*r_i\s*,\s*r_m\s*\)',
            ]
        }
    }
    
    # 可计算的公式模板
    COMPUTABLE_FORMULAS = {
        'RSI_OVERSOLD': {
            'formula': 'RSI(close, period) < threshold',
            'params': {'period': 14, 'threshold': 30},
            'category': 'mean_reversion'
        },
        'MOMENTUM_12M': {
            'formula': 'momentum = close[-1] / close[-252] - 1',
            'params': {'lookback': 252},
            'category': 'momentum'
        },
        'BREAKOUT_VOLUME': {
            'formula': 'close > max(high[-20:]) and volume > mean(volume[-20:]) * 1.5',
            'params': {'period': 20, 'vol_mult': 1.5},
            'category': 'momentum'
        },
        'MEAN_REVERSION_ZSCORE': {
            'formula': 'zscore = (close - mean(close[-20:])) / std(close[-20:])',
            'params': {'period': 20, 'threshold': -2.0},
            'category': 'mean_reversion'
        },
        'VOLATILITY_TARGET': {
            'formula': 'volatility = std(returns[-20:]) * sqrt(252)',
            'params': {'period': 20, 'target_vol': 0.10},
            'category': 'volatility'
        },
        'PRICE_MA_CROSS': {
            'formula': 'close > MA(close, fast) and close < MA(close, slow)',
            'params': {'fast': 20, 'slow': 60},
            'category': 'momentum'
        }
    }
    
    def __init__(self):
        self.extracted_factors = []
    
    def extract(self, paper: Dict) -> List[ExtractedFactor]:
        """从论文中提取因子"""
        factors = []
        text = f"{paper['title']} {paper['summary']}"
        
        # 1. 分类检测
        detected_categories = self._detect_categories(text)
        
        # 2. 公式提取
        for category, confidence in detected_categories:
            factor = self._build_factor(paper, category, confidence, text)
            if factor:
                factors.append(factor)
        
        # 3. 通用模式匹配
        generic_factors = self._extract_generic_patterns(paper, text)
        factors.extend(generic_factors)
        
        # 去重
        seen = set()
        unique_factors = []
        for f in factors:
            key = f"{f.category}:{f.formula[:50]}"
            if key not in seen:
                seen.add(key)
                unique_factors.append(f)
        
        return unique_factors
    
    def _detect_categories(self, text: str) -> List[Tuple[str, float]]:
        """检测论文涉及的风格类别"""
        text_lower = text.lower()
        scores = []
        
        for category, patterns in self.FACTOR_PATTERNS.items():
            score = 0
            for kw in patterns['keywords']:
                count = text_lower.count(kw)
                score += count
            
            if score > 0:
                confidence = min(score / 3, 1.0)  # 归一化
                scores.append((category, confidence))
        
        # 按置信度排序
        return sorted(scores, key=lambda x: x[1], reverse=True)
    
    def _build_factor(self, paper: Dict, category: str, confidence: float, text: str) -> Optional[ExtractedFactor]:
        """构建因子对象"""
        # 使用预定义模板
        template = self._find_best_template(category, text)
        
        if not template:
            return None
        
        return ExtractedFactor(
            name=f"ARXIV_{category.upper()}_{paper['id'][-4:]}",
            formula=template['formula'],
            description=f"Extracted from {paper['title'][:60]}...",
            source_arxiv=paper['id'],
            confidence=confidence,
            category=category,
            raw_text=text[:200]
        )
    
    def _find_best_template(self, category: str, text: str) -> Optional[Dict]:
        """找到最匹配的公式模板"""
        candidates = []
        
        for name, template in self.COMPUTABLE_FORMULAS.items():
            if template['category'] == category:
                candidates.append(template)
        
        # 随机选择一个（实际应该用更智能的匹配）
        import random
        return random.choice(candidates) if candidates else None
    
    def _extract_generic_patterns(self, paper: Dict, text: str) -> List[ExtractedFactor]:
        """提取通用数学模式"""
        factors = []
        
        # 匹配回归方程
        regression_patterns = [
            r'(?i)r_{?\s*t\s*}?\s*=\s*[^\n]+',
            r'(?i)return\s*=\s*[^\n]+',
            r'(?i)E\s*\[\s*r\s*\]\s*=\s*[^\n]+',
        ]
        
        for pattern in regression_patterns:
            matches = re.findall(pattern, text)
            for match in matches[:2]:  # 只取前2个
                factors.append(ExtractedFactor(
                    name=f"ARXIV_REG_{paper['id'][-4:]}",
                    formula=match.strip(),
                    description="Regression-based factor",
                    source_arxiv=paper['id'],
                    confidence=0.5,
                    category='statistical',
                    raw_text=match
                ))
        
        return factors


_DEFAULT_DB_PATH = "/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db"


class GenePoolInjector:
    """基因池注入器"""

    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        self.db_path = db_path
    
    def inject(self, factor: ExtractedFactor, dry_run: bool = False) -> Optional[Gene]:
        """
        将提取的因子注入基因池
        
        Args:
            factor: 提取的因子
            dry_run: 如果为True，只打印不实际注入
        """
        # 生成基因ID
        content = f"{factor.formula}:{factor.category}"
        gene_id = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        # 创建 Gene 对象
        gene = Gene(
            gene_id=gene_id,
            name=factor.name,
            description=factor.description,
            formula=factor.formula,
            parameters=factor.__dict__.get('params', {'extracted': True}),
            source=f"arxiv:{factor.source_arxiv}",
            author="ArXivGeneExtractor",
            created_at=datetime.now(),
            generation=1
        )
        
        if dry_run:
            print(f"\n[DRY RUN] Would inject:")
            print(f"  ID: {gene.gene_id}")
            print(f"  Name: {gene.name}")
            print(f"  Formula: {gene.formula}")
            print(f"  Category: {factor.category}")
            print(f"  Confidence: {factor.confidence:.2f}")
            return gene
        
        # 实际注入数据库
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 确保表存在
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS genes (
                    gene_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    formula TEXT,
                    parameters TEXT,
                    source TEXT,
                    author TEXT,
                    created_at TEXT,
                    parent_gene_id TEXT,
                    generation INTEGER DEFAULT 0
                )
            ''')
            
            # 插入基因
            cursor.execute('''
                INSERT OR IGNORE INTO genes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                gene.gene_id,
                gene.name,
                gene.description,
                gene.formula,
                json.dumps(gene.parameters),
                gene.source,
                gene.author,
                gene.created_at.isoformat(),
                gene.parent_gene_id,
                gene.generation
            ))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                print(f"✅ Injected: {gene.name} (confidence: {factor.confidence:.2f})")
            else:
                print(f"⚠️ Duplicate: {gene.name} already exists")
            
            conn.close()
            return gene
            
        except Exception as e:
            print(f"❌ Injection failed: {e}")
            return None


class ArxivGenePipeline:
    """完整管道: 搜索 → 提取 → 注入"""

    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        self.api = ArXivAPI()
        self.extractor = FactorExtractor()
        self.injector = GenePoolInjector(db_path)
    
    def run(self, query: str, limit: int = 50, dry_run: bool = False, min_confidence: float = 0.3) -> Dict:
        """
        执行完整管道
        
        Args:
            query: arXiv 搜索关键词
            limit: 搜索论文数量
            dry_run: 仅预览不注入
            min_confidence: 最小置信度阈值
        """
        print("=" * 70)
        print("🧬 ArXiv Gene Extractor Pipeline")
        print("=" * 70)
        print(f"Search: '{query}'")
        print(f"Limit: {limit} papers")
        print(f"Min confidence: {min_confidence}")
        print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'LIVE (will inject)'}")
        print()
        
        # 1. 搜索论文
        print("🔍 Step 1: Searching arXiv...")
        papers = self.api.search(query, max_results=limit)
        print(f"   Found {len(papers)} papers")
        
        if not papers:
            return {'status': 'no_papers', 'injected': 0}
        
        # 2. 提取因子
        print("\n🧪 Step 2: Extracting factors...")
        all_factors = []
        
        for i, paper in enumerate(papers, 1):
            print(f"   [{i}/{len(papers)}] {paper['title'][:50]}...", end=' ')
            factors = self.extractor.extract(paper)
            
            # 过滤低置信度
            factors = [f for f in factors if f.confidence >= min_confidence]
            
            if factors:
                print(f"→ {len(factors)} factors")
                all_factors.extend(factors)
            else:
                print("→ no match")
        
        print(f"\n   Total factors extracted: {len(all_factors)}")
        
        if not all_factors:
            return {'status': 'no_factors', 'injected': 0}
        
        # 3. 注入基因池
        print("\n💉 Step 3: Injecting into gene pool...")
        injected = 0
        failed = 0
        
        for factor in all_factors:
            gene = self.injector.inject(factor, dry_run=dry_run)
            if gene:
                injected += 1
            else:
                failed += 1
        
        # 汇总
        print("\n" + "=" * 70)
        print("📊 Pipeline Summary")
        print("=" * 70)
        print(f"   Papers searched: {len(papers)}")
        print(f"   Factors extracted: {len(all_factors)}")
        print(f"   Successfully injected: {injected}")
        if failed > 0:
            print(f"   Failed: {failed}")
        
        return {
            'status': 'success',
            'papers': len(papers),
            'factors': len(all_factors),
            'injected': injected,
            'failed': failed
        }


def main():
    parser = argparse.ArgumentParser(description='ArXiv Gene Extractor')
    parser.add_argument('--search', '-s', type=str, help='Search query for arXiv')
    parser.add_argument('--paper', '-p', type=str, help='Specific arXiv paper ID')
    parser.add_argument('--limit', '-l', type=int, default=50, help='Max papers to search')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Preview only, no injection')
    parser.add_argument('--min-confidence', '-c', type=float, default=0.3, help='Minimum confidence threshold')
    parser.add_argument('--db', type=str, default=_DEFAULT_DB_PATH, help='Database path')
    
    args = parser.parse_args()
    
    pipeline = ArxivGenePipeline(args.db)
    
    if args.paper:
        # 单篇论文模式
        paper = pipeline.api.get_paper_by_id(args.paper)
        if paper:
            factors = pipeline.extractor.extract(paper)
            for f in factors:
                pipeline.injector.inject(f, dry_run=args.dry_run)
    
    elif args.search:
        # 批量搜索模式
        result = pipeline.run(
            query=args.search,
            limit=args.limit,
            dry_run=args.dry_run,
            min_confidence=args.min_confidence
        )
        print(f"\nFinal result: {result}")
    
    else:
        # 默认运行: 搜索量化因子相关论文
        default_queries = [
            'cat:q-fin.TR AND momentum',
            'cat:q-fin.PM AND factor investing',
            'cat:q-fin.ST AND mean reversion',
        ]
        
        for query in default_queries:
            pipeline.run(query, limit=20, dry_run=True, min_confidence=0.4)
            print("\n" + "-" * 70 + "\n")


if __name__ == '__main__':
    main()
