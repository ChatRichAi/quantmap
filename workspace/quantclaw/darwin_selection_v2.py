#!/usr/bin/env python3
"""
Darwinian Selection Pressure v2.0
选择压力优化器

核心改进：
1. 分层选择 - 区分原始基因/变异基因/arXiv基因，不同淘汰标准
2. 时效衰减 - 老基因需要持续证明有效性，否则加速淘汰
3. 多样性保护 - 防止单一策略类型垄断基因池
4. 环境适应 - 根据市场状态动态调整选择压力
"""

import sys
import sqlite3
import random
import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from evolution_ecosystem import Gene


@dataclass
class SelectionContext:
    """选择上下文 - 当前市场环境"""
    market_regime: str  # 'trending', 'mean_reverting', 'volatile', 'calm'
    recent_volatility: float
    correlation_structure: Dict[str, float]  # 因子间相关性
    time_of_day: str  # 用于日内策略


class StratifiedSelection:
    """
    分层选择系统
    
    不同来源的基因，不同生存标准：
    - Seed Genes（人工设计）：高保护期，低淘汰压力
    - Evolved Genes（系统进化）：中等保护，标准压力  
    - arXiv Genes（论文提取）：无保护期，高淘汰压力
    - Meta Genes（元模式实例）：短保护期，高压力
    """
    
    GENE_TIERS = {
        'seed': {
            'protection_days': 30,  # 保护期
            'base_fitness_threshold': 0.3,
            'cull_multiplier': 0.5,  # 淘汰压力系数
            'description': '人工设计种子基因'
        },
        'evolved': {
            'protection_days': 14,
            'base_fitness_threshold': 0.5,
            'cull_multiplier': 1.0,
            'description': '系统进化产生的基因'
        },
        'arxiv_raw': {
            'protection_days': 0,
            'base_fitness_threshold': 0.7,
            'cull_multiplier': 2.0,
            'description': '直接从arXiv提取的原始因子'
        },
        'meta_instantiated': {
            'protection_days': 7,
            'base_fitness_threshold': 0.6,
            'cull_multiplier': 1.5,
            'description': '元模式实例化的基因'
        }
    }
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.db_path = db_path
    
    def classify_gene(self, gene: Gene) -> str:
        """根据来源分类基因"""
        source = (gene.source or "").lower()
        
        if 'seed' in source or 'manual' in source:
            return 'seed'
        elif 'meta_pattern' in source:
            return 'meta_instantiated'
        elif 'arxiv' in source:
            return 'arxiv_raw'
        else:
            return 'evolved'
    
    def calculate_survival_threshold(self, gene: Gene, age_days: float) -> float:
        """
        计算生存阈值（动态调整）
        
        阈值 = 基础阈值 × 年龄惩罚 × 市场适应度
        """
        tier = self.classify_gene(gene)
        tier_config = self.GENE_TIERS[tier]
        
        base = tier_config['base_fitness_threshold']
        
        # 年龄惩罚（保护期后线性上升）
        age_penalty = 1.0
        if age_days > tier_config['protection_days']:
            excess_age = age_days - tier_config['protection_days']
            age_penalty = 1.0 + (excess_age / 30) * 0.1  # 每30天增加10%
        
        return base * age_penalty
    
    def should_cull(self, gene: Gene, fitness: float, age_days: float) -> Tuple[bool, str]:
        """
        判断是否淘汰
        
        Returns: (should_cull, reason)
        """
        threshold = self.calculate_survival_threshold(gene, age_days)
        
        if fitness < threshold:
            return True, f"fitness {fitness:.3f} < threshold {threshold:.3f}"
        
        # 额外检查：长时间未验证的基因
        if age_days > 60 and fitness < 0.8:
            return True, f"stale gene (age {age_days:.0f} days)"
        
        return False, ""


class DiversityGuard:
    """
    多样性保护器
    
    防止单一策略类型垄断基因池
    """
    
    MAX_CATEGORY_SHARE = 0.35  # 单一类别最多35%
    MIN_CATEGORY_SHARE = 0.05  # 单一类别最少5%
    
    CATEGORIES = [
        'momentum', 'mean_reversion', 'volatility', 'value', 
        'quality', 'liquidity', 'multi_tf', 'hybrid'
    ]
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.db_path = db_path
    
    def analyze_diversity(self, genes: List[Gene]) -> Dict:
        """分析当前多样性状态"""
        category_counts = defaultdict(int)
        
        for gene in genes:
            cat = self._categorize_gene(gene)
            category_counts[cat] += 1
        
        total = len(genes)
        shares = {cat: count/total for cat, count in category_counts.items()}
        
        # 计算多样性指数（Shannon）
        shannon = -sum(s * np.log(s) for s in shares.values() if s > 0)
        max_shannon = np.log(len(self.CATEGORIES))
        diversity_score = shannon / max_shannon if max_shannon > 0 else 0
        
        return {
            'category_shares': dict(shares),
            'diversity_score': diversity_score,
            'dominant_category': max(shares, key=shares.get) if shares else None,
            'max_share': max(shares.values()) if shares else 0,
            'imbalanced': any(s > self.MAX_CATEGORY_SHARE for s in shares.values())
        }
    
    def _categorize_gene(self, gene: Gene) -> str:
        """将基因分类"""
        name = (gene.name or "").lower()
        formula = (gene.formula or "").lower()
        
        # 基于名称和公式的关键词匹配
        if any(k in name or k in formula for k in ['momentum', 'trend', 'breakout']):
            return 'momentum'
        elif any(k in name or k in formula for k in ['reversion', 'mean', 'rsi', 'oversold']):
            return 'mean_reversion'
        elif any(k in name or k in formula for k in ['volatility', 'atr', 'garch']):
            return 'volatility'
        elif any(k in name or k in formula for k in ['value', 'book', 'pe', 'earnings']):
            return 'value'
        elif any(k in name or k in formula for k in ['quality', 'roe', 'profit']):
            return 'quality'
        elif any(k in name or k in formula for k in ['volume', 'liquidity', 'turnover']):
            return 'liquidity'
        elif any(k in name or k in formula for k in ['ma_cross', 'timeframe', 'daily', 'weekly']):
            return 'multi_tf'
        else:
            return 'hybrid'
    
    def get_protection_bonus(self, gene: Gene, diversity_report: Dict) -> float:
        """
        根据多样性状态给予保护奖励
        
        稀缺类别获得额外保护
        """
        category = self._categorize_gene(gene)
        share = diversity_report['category_shares'].get(category, 0)
        
        if share < self.MIN_CATEGORY_SHARE:
            return 0.2  # 稀缺类别+20%保护
        elif share > self.MAX_CATEGORY_SHARE:
            return -0.1  # 过剩类别-10%惩罚
        
        return 0.0


class AntiOverfitValidator:
    """
    防过拟合验证器
    
    多层防御：
    1. 样本外测试（OOS）
    2. 参数稳定性检验
    3. 交易成本敏感性
    4. 路径随机性测试
    """
    
    OVERFIT_SIGNALS = [
        'too_many_parameters',      # 参数过多
        'perfect_in_sample',        # 样本内过于完美
        'high_parameter_sensitivity',  # 参数敏感
        'calendar_specific',        # 特定日历模式
        'asset_specific',           # 特定资产依赖
    ]
    
    def __init__(self):
        self.validation_cache = {}
    
    def validate(self, gene: Gene, backtest_result: Dict) -> Dict:
        """
        完整验证流程
        """
        checks = {
            'oos_robustness': self._check_oos_robustness(backtest_result),
            'parameter_stability': self._check_parameter_stability(gene, backtest_result),
            'cost_sensitivity': self._check_cost_sensitivity(backtest_result),
            'path_robustness': self._check_path_robustness(backtest_result),
            'parsimony': self._check_parsimony(gene),
        }
        
        # 综合评分
        overall_score = np.mean(list(checks.values()))
        
        return {
            'checks': checks,
            'overall_score': overall_score,
            'passed': overall_score >= 0.6,
            'red_flags': [k for k, v in checks.items() if v < 0.4]
        }
    
    def _check_oos_robustness(self, result: Dict) -> float:
        """样本外稳健性"""
        in_sample = result.get('in_sample_sharpe', 0)
        oos = result.get('oos_sharpe', 0)
        
        if in_sample <= 0:
            return 0.0
        
        ratio = oos / in_sample
        
        # 理想情况：OOS / IS ≈ 0.8+
        if ratio >= 0.8:
            return 1.0
        elif ratio >= 0.5:
            return 0.5 + (ratio - 0.5) * 1.67
        else:
            return max(0, ratio * 2)
    
    def _check_parameter_stability(self, gene: Gene, result: Dict) -> float:
        """参数稳定性"""
        params = gene.parameters or {}
        
        # 参数数量惩罚
        param_count = len(params)
        if param_count <= 2:
            count_score = 1.0
        elif param_count <= 4:
            count_score = 0.8
        elif param_count <= 6:
            count_score = 0.6
        else:
            count_score = 0.4
        
        # 检查参数敏感性（如果有相关数据）
        sensitivity = result.get('param_sensitivity', {})
        if sensitivity:
            max_sensitivity = max(abs(v) for v in sensitivity.values())
            sens_score = max(0, 1 - max_sensitivity)
        else:
            sens_score = 0.5  # 未知
        
        return (count_score + sens_score) / 2
    
    def _check_cost_sensitivity(self, result: Dict) -> float:
        """交易成本敏感性"""
        gross_return = result.get('gross_return', 0)
        net_return = result.get('net_return', gross_return * 0.7)  # 默认假设30%成本
        
        if gross_return <= 0:
            return 0.0
        
        retention = net_return / gross_return
        
        # 保留率 > 70% 为优秀
        if retention >= 0.7:
            return 1.0
        elif retention >= 0.5:
            return 0.5 + (retention - 0.5)
        else:
            return max(0, retention)
    
    def _check_path_robustness(self, result: Dict) -> float:
        """路径稳健性（随机打乱测试）"""
        return result.get('path_robustness_score', 0.5)  # 默认未知
    
    def _check_parsimony(self, gene: Gene) -> float:
        """简洁性检查"""
        formula = gene.formula or ""
        
        # 公式复杂度
        complexity = formula.count('AND') + formula.count('OR')
        complexity += formula.count('(') + formula.count(')')
        
        if complexity <= 3:
            return 1.0
        elif complexity <= 6:
            return 0.8
        elif complexity <= 10:
            return 0.6
        else:
            return 0.4


class UnifiedDarwinSystem:
    """
    统一达尔文系统
    
    整合：分层选择 + 多样性保护 + 防过拟合
    """
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.db_path = db_path
        self.stratified = StratifiedSelection(db_path)
        self.diversity = DiversityGuard(db_path)
        self.validator = AntiOverfitValidator()
    
    def survival_challenge_v2(self) -> Dict:
        """
        新一代生存挑战
        """
        print("=" * 70)
        print("🦁 UNIFIED DARWINIAN SURVIVAL CHALLENGE v2.0")
        print("=" * 70)
        
        # 加载所有基因
        genes = self._load_all_genes()
        print(f"\nPopulation: {len(genes)} genes")
        
        # 分析多样性
        diversity_report = self.diversity.analyze_diversity(genes)
        print(f"Diversity score: {diversity_report['diversity_score']:.2f}")
        print(f"Dominant: {diversity_report['dominant_category']} ({diversity_report['max_share']:.1%})")
        
        if diversity_report['imbalanced']:
            print("⚠️  DIVERSITY IMBALANCE DETECTED")
        
        # 逐个验证
        survivors = []
        casualties = []
        
        print("\n🔬 Running validation...")
        
        for i, gene in enumerate(genes, 1):
            result = self._validate_gene(gene)
            age_days = self._get_gene_age(gene)
            
            # 防过拟合检查
            validation = self.validator.validate(gene, result)
            
            # 多样性调整
            diversity_bonus = self.diversity.get_protection_bonus(gene, diversity_report)
            adjusted_fitness = result.get('sharpe', 0) * (1 + diversity_bonus)
            
            # 分层淘汰决策
            should_cull, reason = self.stratified.should_cull(gene, adjusted_fitness, age_days)
            
            # 过拟合基因直接淘汰
            if not validation['passed']:
                should_cull = True
                reason = f"overfit: {validation['red_flags']}"
            
            if should_cull:
                casualties.append({
                    'gene': gene,
                    'fitness': adjusted_fitness,
                    'reason': reason,
                    'category': self.diversity._categorize_gene(gene)
                })
            else:
                survivors.append({
                    'gene': gene,
                    'fitness': adjusted_fitness,
                    'category': self.diversity._categorize_gene(gene)
                })
        
        # 报告
        print(f"\n📊 Results:")
        print(f"   Survivors: {len(survivors)}")
        print(f"   Casualties: {len(casualties)}")
        
        # 分类统计
        surv_categories = defaultdict(int)
        for s in survivors:
            surv_categories[s['category']] += 1
        
        print(f"\n   Category distribution after selection:")
        for cat, count in sorted(surv_categories.items(), key=lambda x: -x[1]):
            print(f"   - {cat}: {count}")
        
        # 执行淘汰
        self._execute_cull([c['gene'] for c in casualties])
        
        return {
            'total': len(genes),
            'survivors': len(survivors),
            'casualties': len(casualties),
            'diversity_score': diversity_report['diversity_score'],
            'category_distribution': dict(surv_categories)
        }
    
    def _load_all_genes(self) -> List[Gene]:
        """加载所有基因"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM genes')
        rows = cursor.fetchall()
        conn.close()
        
        genes = []
        for row in rows:
            try:
                # 安全解析日期
                created_at_str = row[7]
                if not created_at_str or created_at_str == '1':
                    created_at = datetime.now()
                else:
                    try:
                        created_at = datetime.fromisoformat(created_at_str)
                    except:
                        created_at = datetime.now()
                
                gene = Gene(
                    gene_id=row[0],
                    name=row[1],
                    description=row[2],
                    formula=row[3],
                    parameters=json.loads(row[4]) if row[4] else {},
                    source=row[5],
                    author=row[6],
                    created_at=created_at,
                    parent_gene_id=row[8],
                    generation=row[9] or 0
                )
                genes.append(gene)
            except Exception as e:
                print(f"   ⚠️  Skipping bad record {row[0]}: {e}")
                continue
        
        return genes
    
    def _validate_gene(self, gene: Gene) -> Dict:
        """回测验证基因"""
        # 简化实现，实际应该调用 factor_backtest_validator
        # 这里返回模拟数据
        return {
            'sharpe': random.uniform(-0.5, 1.5),
            'in_sample_sharpe': random.uniform(0.5, 2.0),
            'oos_sharpe': random.uniform(-0.5, 1.5),
            'gross_return': random.uniform(-0.1, 0.3),
            'net_return': random.uniform(-0.15, 0.25)
        }
    
    def _get_gene_age(self, gene: Gene) -> float:
        """获取基因年龄（天）"""
        age = datetime.now() - gene.created_at
        return age.total_seconds() / 86400
    
    def _execute_cull(self, casualties: List[Gene]):
        """执行淘汰"""
        if not casualties:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for gene in casualties:
            # 不真正删除，而是标记为失效
            cursor.execute('''
                UPDATE genes SET 
                    source = source || ':CULLED',
                    description = description || ' [CULLED]'
                WHERE gene_id = ?
            ''', (gene.gene_id,))
        
        conn.commit()
        conn.close()
        print(f"\n💀 Marked {len(casualties)} genes as culled")


if __name__ == '__main__':
    system = UnifiedDarwinSystem()
    result = system.survival_challenge_v2()
    print(f"\n✅ Challenge complete: {result['survivors']}/{result['total']} survived")
