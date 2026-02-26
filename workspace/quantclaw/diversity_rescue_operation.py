#!/usr/bin/env python3
"""
QuantClaw Diversity Rescue Operation
多样性救援行动 - 自动修复基因池失衡

问题：RSI+熵支系占85%，多样性严重不足
方案：
1. 备份当前基因池
2. 筛选各支系代表性基因（精英保留）
3. 注入新的多样性种子
4. 重启进化
"""

import sys
import sqlite3
import json
import shutil
from datetime import datetime
from collections import defaultdict
from typing import Dict, List

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from evolution_ecosystem import QuantClawEvolutionHub, Gene


class DiversityRescueOperation:
    """多样性救援行动"""
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.db_path = db_path
        self.hub = QuantClawEvolutionHub(db_path)
        self.backup_path = f"evolution_hub_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
    def backup_gene_pool(self):
        """备份当前基因池"""
        print("💾 Backing up gene pool...")
        shutil.copy(self.db_path, self.backup_path)
        print(f"   Backup saved: {self.backup_path}")
        
    def analyze_lineages(self) -> dict:
        """分析各支系分布"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM genes')
        rows = cursor.fetchall()
        conn.close()
        
        lineages = defaultdict(list)
        
        for row in rows:
            gene = Gene(
                gene_id=row[0],
                name=row[1],
                description=row[2],
                formula=row[3],
                parameters=json.loads(row[4]),
                source=row[5],
                author=row[6],
                parent_gene_id=row[7],
                generation=row[8],
                created_at=datetime.fromisoformat(row[9])
            )
            
            # 识别支系类型
            if 'RSI' in gene.formula and 'SampEn' in gene.formula:
                lineages['RSI+Entropy'].append(gene)
            elif 'RSI' in gene.formula:
                lineages['RSI_Only'].append(gene)
            elif 'SampEn' in gene.formula or 'Hurst' in gene.formula:
                lineages['Academic'].append(gene)
            elif 'SMA' in gene.formula or 'EMA' in gene.formula:
                lineages['MovingAverage'].append(gene)
            elif 'BB' in gene.formula:
                lineages['Bollinger'].append(gene)
            elif 'MACD' in gene.formula:
                lineages['MACD'].append(gene)
            elif 'Volatility' in gene.formula or 'ATR' in gene.formula:
                lineages['Volatility'].append(gene)
            elif 'MOM' in gene.formula or 'ROC' in gene.formula:
                lineages['Momentum'].append(gene)
            else:
                lineages['Other'].append(gene)
        
        return dict(lineages)
    
    def select_elites_per_lineage(self, lineages: dict, max_per_lineage: int = 5) -> list:
        """从每个支系选择精英基因"""
        elites = []
        
        for lineage_name, genes in lineages.items():
            print(f"\n   {lineage_name}: {len(genes)} genes")
            
            if not genes:
                continue
            
            # 按代数和质量排序
            # 优先选择：高代数 + 简洁公式
            scored_genes = []
            for gene in genes:
                # 简洁度评分（公式越短越好）
                simplicity_score = max(0, 100 - len(gene.formula))
                # 代数评分
                generation_score = gene.generation * 5
                # 综合评分
                total_score = simplicity_score + generation_score
                scored_genes.append((gene, total_score))
            
            # 排序并选择前N个
            scored_genes.sort(key=lambda x: x[1], reverse=True)
            selected = [g for g, _ in scored_genes[:max_per_lineage]]
            
            elites.extend(selected)
            print(f"      Selected: {len(selected)} elites")
        
        return elites
    
    def generate_diversity_seeds(self, n_seeds: int = 20) -> list:
        """生成多样性种子"""
        print("\n🌱 Generating diversity seeds...")
        
        seed_templates = [
            # 趋势跟踪
            {'name': 'Trend_Following_SMA', 'formula': 'Close > SMA(20)', 'params': {'period': 20}},
            {'name': 'Trend_Following_EMA', 'formula': 'Close > EMA(50)', 'params': {'period': 50}},
            # 均值回归
            {'name': 'Mean_Reversion_RSI', 'formula': 'RSI(14) < 30', 'params': {'period': 14, 'threshold': 30}},
            {'name': 'Mean_Reversion_BB', 'formula': 'Close < BB.lower(20)', 'params': {'period': 20}},
            # 动量
            {'name': 'Momentum_ROC', 'formula': 'ROC(10) > 0', 'params': {'period': 10}},
            {'name': 'Momentum_MOM', 'formula': 'MOM(20) > 0', 'params': {'period': 20}},
            # 波动率
            {'name': 'Volatility_Breakout', 'formula': 'ATR(14) > ATR(14).mean()', 'params': {'period': 14}},
            {'name': 'Volatility_Squeeze', 'formula': 'BB.width < BB.width.mean(20)', 'params': {'period': 20}},
            # 成交量
            {'name': 'Volume_Breakout', 'formula': 'Volume > SMA(Volume, 20) * 1.5', 'params': {'multiplier': 1.5}},
            {'name': 'Volume_Confirmation', 'formula': 'Volume > Volume.shift(1) AND Close > Close.shift(1)', 'params': {}},
            # 组合策略
            {'name': 'Combo_Trend_Volume', 'formula': 'Close > SMA(20) AND Volume > SMA(Volume, 20)', 'params': {}},
            {'name': 'Combo_RSI_BB', 'formula': 'RSI(14) < 30 AND Close < BB.lower(20)', 'params': {}},
            # 多时间框架
            {'name': 'MTF_SMA_Cross', 'formula': 'SMA(10) > SMA(30) AND SMA(30) > SMA(50)', 'params': {}},
            {'name': 'MTF_EMA_Cross', 'formula': 'EMA(12) > EMA(26) AND MACD > 0', 'params': {}},
            # 价格行为
            {'name': 'Price_Higher_High', 'formula': 'High > High.shift(1) AND Low > Low.shift(1)', 'params': {}},
            {'name': 'Price_Lower_Low', 'formula': 'Low < Low.shift(1) AND High < High.shift(1)', 'params': {}},
            # 统计策略
            {'name': 'Stat_ZScore', 'formula': 'ZScore(Close, 20) < -2', 'params': {'period': 20, 'threshold': -2}},
            {'name': 'Stat_Percentile', 'formula': 'Percentile(Close, 50, 20) < 0.2', 'params': {'period': 20, 'percentile': 0.2}},
            # 技术组合
            {'name': 'Tech_ADX_Trend', 'formula': 'ADX(14) > 25 AND DI+ > DI-', 'params': {'period': 14}},
            {'name': 'Tech_Stoch_Oversold', 'formula': 'StochK(14) < 20 AND StochD(14) < 20', 'params': {'period': 14}},
        ]
        
        seeds = []
        for i, template in enumerate(seed_templates[:n_seeds], 1):
            gene = Gene(
                gene_id=f"g_rescue_seed_{datetime.now().strftime('%Y%m%d')}_{i:03d}",
                name=template['name'],
                description=f"Diversity rescue seed: {template['formula']}",
                formula=template['formula'],
                parameters=template['params'],
                source='diversity_rescue',
                author='rescue_operation',
                created_at=datetime.now(),
                generation=0
            )
            seeds.append(gene)
        
        print(f"   Generated {len(seeds)} diversity seeds")
        return seeds
    
    def reset_gene_pool(self, elites: list, new_seeds: list):
        """重置基因池"""
        print("\n🔄 Resetting gene pool...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 清空当前基因表
        cursor.execute('DELETE FROM genes')
        
        # 重新插入精英基因
        for gene in elites:
            cursor.execute('''
                INSERT OR REPLACE INTO genes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                gene.gene_id,
                gene.name,
                gene.description,
                gene.formula,
                json.dumps(gene.parameters),
                gene.source,
                gene.author,
                gene.parent_gene_id,
                gene.generation,
                gene.created_at.isoformat()
            ))
        
        # 插入新种子
        for gene in new_seeds:
            cursor.execute('''
                INSERT OR REPLACE INTO genes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                gene.gene_id,
                gene.name,
                gene.description,
                gene.formula,
                json.dumps(gene.parameters),
                gene.source,
                gene.author,
                gene.parent_gene_id,
                gene.generation,
                gene.created_at.isoformat()
            ))
        
        conn.commit()
        conn.close()
        
        total = len(elites) + len(new_seeds)
        print(f"   New pool: {total} genes ({len(elites)} elites + {len(new_seeds)} new seeds)")
    
    def execute_rescue(self):
        """执行救援行动"""
        print("=" * 70)
        print("🚨 QuantClaw Diversity Rescue Operation")
        print("=" * 70)
        print()
        
        # 1. 备份
        self.backup_gene_pool()
        
        # 2. 分析当前状态
        print("\n🔍 Analyzing current gene pool...")
        lineages = self.analyze_lineages()
        
        print(f"\n📊 Lineage Distribution:")
        for name, genes in sorted(lineages.items(), key=lambda x: len(x[1]), reverse=True):
            pct = len(genes) / sum(len(g) for g in lineages.values()) * 100
            bar = '█' * int(pct / 5)
            print(f"   {name:20s}: {len(genes):3d} ({pct:5.1f}%) {bar}")
        
        # 3. 选择精英
        print("\n🏆 Selecting elite genes from each lineage...")
        elites = self.select_elites_per_lineage(lineages, max_per_lineage=3)
        
        # 4. 生成新种子
        new_seeds = self.generate_diversity_seeds(n_seeds=20)
        
        # 5. 重置基因池
        self.reset_gene_pool(elites, new_seeds)
        
        # 6. 报告
        print("\n" + "=" * 70)
        print("✅ Diversity Rescue Complete!")
        print("=" * 70)
        print(f"\n📈 New Gene Pool:")
        print(f"   Total genes: {len(elites) + len(new_seeds)}")
        print(f"   Elite preserved: {len(elites)}")
        print(f"   New diversity seeds: {len(new_seeds)}")
        print(f"   Backup: {self.backup_path}")
        print()
        print("🚀 System ready for new evolution cycle with improved diversity")


def main():
    """主函数"""
    rescue = DiversityRescueOperation()
    rescue.execute_rescue()


if __name__ == "__main__":
    main()
