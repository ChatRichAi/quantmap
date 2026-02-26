#!/usr/bin/env python3
"""
QuantGenius Nation - 量化天才之国
全自动进化基础设施

架构：
├── 素材挖掘层 (Miners) - 多源信息摄入
├── 模式提取层 (Extractors) - 从噪声中提取结构
├── 基因工程层 (Engineering) - 设计、变异、重组
├── 自然选择层 (Selection) - 残酷淘汰，适者生存
├── 知识沉淀层 (Knowledge) - 长期记忆与传承
└── 元认知层 (Meta) - 自我监控与策略调整
"""

import os
import sys
import json
import time
import schedule
import sqlite3
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')


@dataclass
class EvolutionState:
    """系统状态快照"""
    timestamp: datetime
    generation: int
    population: int
    gene_tiers: Dict[str, int]
    diversity_score: float
    recent_casualties: int
    recent_births: int
    top_performer: Optional[str]
    system_health: str  # healthy, stressed, critical


class DataSourceMiners:
    """
    多源素材挖掘器
    不设上限，不设下限，只要可能有价值就挖
    """
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.mined_materials = []
        
    def _load_config(self, path):
        """加载数据源配置"""
        default = {
            'arxiv': {'enabled': True, 'queries': [
                'factor investing', 'momentum strategy', 'mean reversion',
                'statistical arbitrage', 'volatility trading', 'machine learning trading',
                'quantitative strategy', 'algorithmic trading', 'pairs trading',
                'market microstructure', 'high frequency trading'
            ]},
            'github': {'enabled': True, 'queries': [
                'quantitative trading', 'backtesting', 'trading strategy',
                'technical analysis', 'algorithmic trading python'
            ]},
            'financial_blogs': {'enabled': False},  # 需要爬虫
            'academic_databases': {'enabled': False},  # 需要 API key
            'trading_forums': {'enabled': False},  # 需要解析
        }
        return default
    
    def mine_all(self) -> List[Dict]:
        """执行全量挖掘"""
        print("\n" + "="*70)
        print("⛏️  UNRESTRICTED DATA MINING")
        print("="*70)
        
        all_materials = []
        
        # 1. arXiv 挖掘
        if self.config['arxiv']['enabled']:
            materials = self._mine_arxiv()
            all_materials.extend(materials)
        
        # 2. GitHub 挖掘
        if self.config['github']['enabled']:
            materials = self._mine_github()
            all_materials.extend(materials)
        
        # 3. 本地知识库挖掘
        materials = self._mine_local_knowledge()
        all_materials.extend(materials)
        
        # 4. 市场数据模式挖掘
        materials = self._mine_market_patterns()
        all_materials.extend(materials)
        
        print(f"\n✅ Total materials mined: {len(all_materials)}")
        return all_materials
    
    def _mine_arxiv(self) -> List[Dict]:
        """挖掘 arXiv"""
        print("\n📚 Mining arXiv...")
        
        from arxiv_gene_extractor import ArXivAPI
        
        api = ArXivAPI()
        materials = []
        
        for query in self.config['arxiv']['queries']:
            try:
                papers = api.search(query, max_results=30)
                for paper in papers:
                    materials.append({
                        'source': 'arxiv',
                        'source_id': paper['id'],
                        'title': paper['title'],
                        'content': paper.get('summary', ''),
                        'metadata': {
                            'categories': paper.get('categories', []),
                            'published': paper.get('published', ''),
                            'query': query
                        },
                        'mined_at': datetime.now().isoformat()
                    })
                print(f"   {query}: {len(papers)} papers")
                time.sleep(1)  # 礼貌延迟
            except Exception as e:
                print(f"   ❌ {query}: {e}")
        
        return materials
    
    def _mine_github(self) -> List[Dict]:
        """挖掘 GitHub 量化项目"""
        print("\n💻 Mining GitHub...")
        
        materials = []
        
        # 使用 GitHub API 搜索
        for query in self.config['github']['queries']:
            try:
                # 简单实现：使用 gh CLI
                result = subprocess.run(
                    ['gh', 'search', 'repos', query, '--limit', '20', '--json', 'name,description,url,readme'],
                    capture_output=True, text=True, timeout=30
                )
                
                if result.returncode == 0:
                    repos = json.loads(result.stdout)
                    for repo in repos:
                        materials.append({
                            'source': 'github',
                            'source_id': repo.get('url', ''),
                            'title': repo.get('name', ''),
                            'content': repo.get('description', ''),
                            'metadata': {
                                'readme': repo.get('readme', '')[:2000],
                                'query': query
                            },
                            'mined_at': datetime.now().isoformat()
                        })
                    print(f"   {query}: {len(repos)} repos")
                else:
                    print(f"   ⚠️  gh CLI error: {result.stderr[:100]}")
                    
            except Exception as e:
                print(f"   ❌ {query}: {e}")
        
        return materials
    
    def _mine_local_knowledge(self) -> List[Dict]:
        """挖掘本地知识库"""
        print("\n📂 Mining local knowledge...")
        
        materials = []
        memory_path = Path('/Users/oneday/.openclaw/workspace/memory')
        
        # 扫描记忆文件
        for md_file in memory_path.rglob('*.md'):
            try:
                content = md_file.read_text(encoding='utf-8')
                if len(content) > 100:  # 过滤空文件
                    materials.append({
                        'source': 'local_memory',
                        'source_id': str(md_file.relative_to(memory_path)),
                        'title': md_file.stem,
                        'content': content[:5000],  # 限制长度
                        'metadata': {
                            'path': str(md_file),
                            'size': len(content)
                        },
                        'mined_at': datetime.now().isoformat()
                    })
            except:
                pass
        
        print(f"   Local files: {len(materials)}")
        return materials
    
    def _mine_market_patterns(self) -> List[Dict]:
        """从市场数据挖掘模式"""
        print("\n📈 Mining market patterns...")
        
        materials = []
        
        # 这里可以接入实时市场数据挖掘
        # 暂时使用已有分析结果
        state_files = [
            '/Users/oneday/.openclaw/workspace/memory/state/a-share-state.json',
            '/Users/oneday/.openclaw/workspace/memory/state/us-stock-state.json',
            '/Users/oneday/.openclaw/workspace/memory/state/crypto-state.json'
        ]
        
        for state_file in state_files:
            try:
                with open(state_file) as f:
                    data = json.load(f)
                    materials.append({
                        'source': 'market_state',
                        'source_id': state_file,
                        'title': f"Market State: {data.get('market', 'unknown')}",
                        'content': json.dumps(data, indent=2),
                        'metadata': data,
                        'mined_at': datetime.now().isoformat()
                    })
            except:
                pass
        
        print(f"   Market states: {len(materials)}")
        return materials


class PatternRecognitionEngine:
    """
    模式识别引擎
    从原始素材中提取可复用的策略模式
    """
    
    # 扩展的模式库
    PATTERN_LIBRARY = {
        # 价格行为模式
        'breakout_patterns': {
            'keywords': ['breakout', '突破', 'break through', 'penetrates'],
            'logic': 'PRICE_THRESHOLD AND CONFIRMATION',
            'variations': ['volume_confirm', 'time_confirm', 'multi_tf_confirm']
        },
        'reversal_patterns': {
            'keywords': ['reversal', 'revert', '反转', 'mean reversion'],
            'logic': 'EXTREME_DEVIATION AND REVERSION_SIGNAL',
            'variations': ['rsi_extreme', 'bollinger_extreme', 'zscore_extreme']
        },
        'trend_following': {
            'keywords': ['trend', 'momentum', '趋势', '动量'],
            'logic': 'TREND_ALIGN AND ENTRY_TRIGGER',
            'variations': ['ma_cross', 'macd_signal', 'adx_filter']
        },
        'volatility_strategies': {
            'keywords': ['volatility', '波动', 'garch', 'realized vol'],
            'logic': 'VOLATILITY_REGIME AND POSITION_SIZING',
            'variations': ['vol_target', 'vol_filter', 'vol_expansion']
        },
        'statistical_arbitrage': {
            'keywords': ['cointegration', 'pair trading', '均值回复', '统计套利'],
            'logic': 'COINTEGRATION AND DEVIATION',
            'variations': ['pair_selection', 'spread_zscore', 'half_life']
        },
        'machine_learning': {
            'keywords': ['machine learning', 'ml', 'prediction', 'classification'],
            'logic': 'FEATURE_SET AND MODEL_PREDICTION',
            'variations': ['supervised', 'unsupervised', 'reinforcement']
        },
        'market_microstructure': {
            'keywords': ['microstructure', 'order flow', 'liquidity', 'spread'],
            'logic': 'ORDER_FLOW_ANALYSIS AND EXECUTION',
            'variations': ['imbalance', 'tick_data', 'depth_analysis']
        },
        'risk_management': {
            'keywords': ['risk', 'drawdown', 'stop loss', 'position sizing'],
            'logic': 'RISK_METRIC AND CONTROL_RULE',
            'variations': ['vol_target', 'max_drawdown', 'correlation_limit']
        }
    }
    
    def __init__(self):
        self.extracted_patterns = []
    
    def process_materials(self, materials: List[Dict]) -> List[Dict]:
        """处理所有素材，提取模式"""
        print("\n" + "="*70)
        print("🔍 PATTERN RECOGNITION")
        print("="*70)
        
        patterns = []
        
        for material in materials:
            extracted = self._extract_from_material(material)
            patterns.extend(extracted)
        
        # 去重和聚合
        unique_patterns = self._aggregate_patterns(patterns)
        
        print(f"\n✅ Extracted {len(unique_patterns)} unique patterns")
        return unique_patterns
    
    def _extract_from_material(self, material: Dict) -> List[Dict]:
        """从单个素材提取模式"""
        patterns = []
        text = f"{material.get('title', '')} {material.get('content', '')}".lower()
        
        for pattern_name, pattern_def in self.PATTERN_LIBRARY.items():
            score = 0
            matched_keywords = []
            
            for kw in pattern_def['keywords']:
                if kw.lower() in text:
                    score += 1
                    matched_keywords.append(kw)
            
            if score >= 2:  # 至少匹配2个关键词
                patterns.append({
                    'pattern_type': pattern_name,
                    'logic_skeleton': pattern_def['logic'],
                    'confidence': min(score / len(pattern_def['keywords']) * 1.5, 1.0),
                    'matched_keywords': matched_keywords,
                    'source': material['source'],
                    'source_id': material['source_id'],
                    'variations': pattern_def['variations'],
                    'extracted_at': datetime.now().isoformat()
                })
        
        return patterns
    
    def _aggregate_patterns(self, patterns: List[Dict]) -> List[Dict]:
        """聚合同类模式"""
        grouped = {}
        
        for p in patterns:
            key = p['pattern_type']
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(p)
        
        aggregated = []
        for pattern_type, group in grouped.items():
            # 合并同类模式
            aggregated.append({
                'pattern_type': pattern_type,
                'occurrence_count': len(group),
                'avg_confidence': sum(p['confidence'] for p in group) / len(group),
                'sources': list(set(p['source'] for p in group)),
                'logic_skeleton': group[0]['logic_skeleton'],
                'variations': group[0]['variations'],
                'examples': [p['source_id'] for p in group[:3]]  # 保留3个示例
            })
        
        # 按出现次数排序
        return sorted(aggregated, key=lambda x: -x['occurrence_count'])


class InfiniteEvolutionLoop:
    """
    无限进化循环
    全自动、无人工干预、持续运行
    """
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.db_path = db_path
        self.miners = DataSourceMiners()
        self.recognizer = PatternRecognitionEngine()
        self.generation = 0
        self.running = False
        
        # 状态追踪
        self.state_history = []
        self.best_performers = []
        
    def start(self, mode: str = 'continuous'):
        """
        启动进化
        
        mode: 'continuous' - 持续运行
              'single' - 单轮运行
              'scheduled' - 定时运行
        """
        print("\n" + "="*70)
        print("🧬 QUANT GENIUS NATION - INFINITE EVOLUTION STARTED")
        print("="*70)
        print(f"Mode: {mode}")
        print(f"Database: {self.db_path}")
        print(f"Start time: {datetime.now()}")
        print()
        
        if mode == 'continuous':
            self._continuous_loop()
        elif mode == 'single':
            self._evolution_cycle()
        elif mode == 'scheduled':
            self._scheduled_loop()
    
    def _continuous_loop(self):
        """持续运行循环"""
        self.running = True
        cycle_count = 0
        
        while self.running:
            cycle_count += 1
            print(f"\n{'='*70}")
            print(f"🔄 EVOLUTION CYCLE #{cycle_count}")
            print(f"{'='*70}")
            
            try:
                self._evolution_cycle()
                
                # 状态报告
                if cycle_count % 5 == 0:
                    self._generate_report()
                
                # 休息间隔
                print(f"\n⏳ Resting for 60 seconds...")
                time.sleep(60)
                
            except Exception as e:
                print(f"\n❌ Cycle failed: {e}")
                print("Restarting in 30 seconds...")
                time.sleep(30)
    
    def _scheduled_loop(self):
        """定时运行"""
        # 设置定时任务
        schedule.every(2).hours.do(self._evolution_cycle)
        schedule.every().day.at("08:00").do(self._generate_report)
        
        print("Scheduled tasks:")
        print("  - Evolution cycle: every 2 hours")
        print("  - Daily report: 08:00")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def _evolution_cycle(self):
        """单轮进化周期"""
        self.generation += 1
        cycle_start = datetime.now()
        
        # 1. 素材挖掘
        print("\n📥 PHASE 1: MATERIAL MINING")
        materials = self.miners.mine_all()
        
        # 2. 模式识别
        print("\n🧠 PHASE 2: PATTERN RECOGNITION")
        patterns = self.recognizer.process_materials(materials)
        
        # 3. 基因工程（实例化模式为基因）
        print("\n🔬 PHASE 3: GENE ENGINEERING")
        new_genes = self._engineer_genes(patterns)
        
        # 4. 注入基因池
        print("\n💉 PHASE 4: GENE POOL INJECTION")
        injected = self._inject_genes(new_genes)
        
        # 5. 生存挑战
        print("\n🦁 PHASE 5: SURVIVAL CHALLENGE")
        survivors = self._run_survival_challenge()
        
        # 6. 繁衍进化
        print("\n🧬 PHASE 6: EVOLUTION & BREEDING")
        offspring = self._breed_offspring(survivors)
        
        # 7. 知识沉淀
        print("\n📚 PHASE 7: KNOWLEDGE PERSISTENCE")
        self._persist_knowledge()
        
        # 记录状态
        cycle_end = datetime.now()
        self._record_state({
            'generation': self.generation,
            'materials': len(materials),
            'patterns': len(patterns),
            'new_genes': len(new_genes),
            'injected': injected,
            'survivors': len(survivors),
            'offspring': len(offspring),
            'duration': (cycle_end - cycle_start).total_seconds()
        })
        
        print(f"\n✅ Cycle {self.generation} complete in {(cycle_end - cycle_start).total_seconds():.1f}s")
    
    def _engineer_genes(self, patterns: List[Dict]) -> List[Dict]:
        """将模式工程化为基因"""
        genes = []
        
        for pattern in patterns:
            # 基于模式类型创建不同变体
            variations = self._create_variations(pattern)
            genes.extend(variations)
        
        # 限制每轮新基因数量
        if len(genes) > 50:
            # 按置信度排序，保留top 50
            genes = sorted(genes, key=lambda x: -x.get('confidence', 0))[:50]
        
        print(f"   Engineered {len(genes)} gene candidates")
        return genes
    
    def _create_variations(self, pattern: Dict) -> List[Dict]:
        """为模式创建参数变体"""
        variations = []
        
        base_gene = {
            'name': f"PATTERN_{pattern['pattern_type'].upper()}_{self.generation}",
            'pattern_type': pattern['pattern_type'],
            'logic': pattern['logic_skeleton'],
            'source_pattern': pattern,
            'confidence': pattern['avg_confidence'],
            'generation': self.generation
        }
        
        # 为每个变体创建
        for i, var in enumerate(pattern.get('variations', [])[:3]):
            gene = base_gene.copy()
            gene['name'] = f"{base_gene['name']}_V{i}"
            gene['variation'] = var
            gene['formula'] = self._generate_formula(pattern['pattern_type'], var)
            variations.append(gene)
        
        return variations
    
    def _generate_formula(self, pattern_type: str, variation: str) -> str:
        """生成具体公式"""
        templates = {
            'breakout_patterns': {
                'volume_confirm': 'close > max(high[-20:]) AND volume > mean(volume[-20:]) * 1.5',
                'time_confirm': 'close > max(high[-20:]) AND sustained(3)',
                'multi_tf_confirm': 'daily_breakout AND weekly_uptrend'
            },
            'reversal_patterns': {
                'rsi_extreme': 'RSI(close, 14) < 30 AND divergence(bullish)',
                'bollinger_extreme': 'close < lower_band AND volume_climax',
                'zscore_extreme': 'abs(zscore(close, 20)) > 2 AND reverting'
            },
            'trend_following': {
                'ma_cross': 'MA(close, 20) > MA(close, 60) AND close > MA(close, 20)',
                'macd_signal': 'MACD_line > signal_line AND histogram > 0',
                'adx_filter': 'ADX(14) > 25 AND DI+ > DI-'
            }
        }
        
        pt = templates.get(pattern_type, {})
        return pt.get(variation, f'{pattern_type}_{variation}')
    
    def _inject_genes(self, genes: List[Dict]) -> int:
        """注入基因到数据库"""
        import hashlib
        
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
        
        inserted = 0
        for gene in genes:
            try:
                gene_id = hashlib.sha256(gene['formula'].encode()).hexdigest()[:16]
                
                cursor.execute('''
                    INSERT OR IGNORE INTO genes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    gene_id,
                    gene['name'],
                    f"Pattern: {gene['pattern_type']}, Variation: {gene.get('variation', 'default')}",
                    gene['formula'],
                    json.dumps({'confidence': gene.get('confidence', 0), 'variation': gene.get('variation', '')}),
                    f"pattern_extraction:{gene['pattern_type']}",
                    "QuantGeniusNation",
                    datetime.now().isoformat(),
                    None,
                    gene.get('generation', self.generation)
                ))
                
                if cursor.rowcount > 0:
                    inserted += 1
                    
            except Exception as e:
                print(f"   ⚠️  Injection error: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"   Injected {inserted}/{len(genes)} new genes")
        return inserted
    
    def _run_survival_challenge(self) -> List[Dict]:
        """运行生存挑战"""
        try:
            from darwin_selection_v2 import UnifiedDarwinSystem
            
            system = UnifiedDarwinSystem(self.db_path)
            result = system.survival_challenge_v2()
            
            print(f"   Survivors: {result['survivors']}/{result['total']}")
            return [{'gene_id': 'placeholder', 'fitness': 1.0}] * result['survivors']
            
        except Exception as e:
            print(f"   ⚠️  Survival challenge error: {e}")
            return []
    
    def _breed_offspring(self, survivors: List[Dict]) -> List[Dict]:
        """繁衍后代"""
        # 简化的繁衍逻辑
        offspring = []
        
        # 交叉
        if len(survivors) >= 2:
            for i in range(min(len(survivors), 10)):  # 最多10个后代
                offspring.append({
                    'type': 'crossover',
                    'parents': [survivors[i % len(survivors)], survivors[(i+1) % len(survivors)]]
                })
        
        # 变异
        for s in survivors[:5]:  # 前5个幸存者变异
            offspring.append({
                'type': 'mutation',
                'parent': s
            })
        
        print(f"   Created {len(offspring)} offspring")
        return offspring
    
    def _persist_knowledge(self):
        """知识持久化"""
        # 保存状态历史
        state_file = Path('/Users/oneday/.openclaw/workspace/memory/state/evolution_state.json')
        state_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(state_file, 'w') as f:
            json.dump({
                'last_update': datetime.now().isoformat(),
                'generation': self.generation,
                'history': self.state_history[-100:]  # 保留最近100条
            }, f, indent=2)
        
        print("   Knowledge persisted")
    
    def _record_state(self, state: Dict):
        """记录状态"""
        self.state_history.append(state)
        
        # 控制台输出
        print(f"\n📊 STATE RECORD:")
        print(f"   Generation: {state['generation']}")
        print(f"   Materials: {state['materials']}")
        print(f"   Patterns: {state['patterns']}")
        print(f"   New genes: {state['new_genes']}")
        print(f"   Injected: {state['injected']}")
        print(f"   Survivors: {state['survivors']}")
        print(f"   Duration: {state['duration']:.1f}s")
    
    def _generate_report(self):
        """生成报告"""
        print("\n" + "="*70)
        print("📈 EVOLUTION REPORT")
        print("="*70)
        
        if not self.state_history:
            print("No data yet")
            return
        
        recent = self.state_history[-10:]
        
        print(f"\nLast 10 cycles summary:")
        print(f"  Avg materials/cycle: {sum(s['materials'] for s in recent)/len(recent):.1f}")
        print(f"  Avg patterns/cycle: {sum(s['patterns'] for s in recent)/len(recent):.1f}")
        print(f"  Avg new genes/cycle: {sum(s['new_genes'] for s in recent)/len(recent):.1f}")
        print(f"  Total survivors: {recent[-1]['survivors'] if recent else 0}")
        
        # 保存到文件
        report_path = Path('/Users/oneday/.openclaw/workspace/memory/reports')
        report_path.mkdir(parents=True, exist_ok=True)
        
        report_file = report_path / f"evolution_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'generation': self.generation,
                'summary': self.state_history
            }, f, indent=2)
        
        print(f"\nReport saved: {report_file}")


def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quant Genius Nation')
    parser.add_argument('--mode', '-m', default='single', 
                       choices=['single', 'continuous', 'scheduled'],
                       help='运行模式')
    parser.add_argument('--db', default='evolution_hub.db', help='数据库路径')
    
    args = parser.parse_args()
    
    # 启动进化
    nation = InfiniteEvolutionLoop(args.db)
    nation.start(mode=args.mode)


if __name__ == '__main__':
    main()
