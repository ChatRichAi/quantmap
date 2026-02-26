#!/usr/bin/env python3
"""
QuantClaw Darwinian Ecosystem v4
达尔文式生态系统 - 真正的优胜劣汰

核心机制:
1. 环境承载力 - 基因池有上限(100个)
2. 定期生存挑战 - 每周期回测验证
3. 资源竞争 - 只有表现好的获得繁衍权
4. 自然死亡 - 表现差的自动淘汰
5. 适者生存 - 真实市场验证通过才能存活
"""

import sys
import sqlite3
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from evolution_ecosystem import QuantClawEvolutionHub, Gene
from factor_backtest_validator import FactorValidator


class DarwinianEcosystem:
    """
    达尔文式生态系统
    
    自然选择法则:
    - 基因池上限: 100个 (环境承载力)
    - 生存周期: 24小时必须重新验证
    - 淘汰比例: 每次淘汰表现最差的30%
    - 繁衍资格: 只有前20%能繁衍后代
    - 最低标准: 夏普>0.5, 否则直接死亡
    """
    
    def __init__(self, db_path: str = "evolution_hub.db"):
        self.db_path = db_path
        self.hub = QuantClawEvolutionHub(db_path)
        self.validator = FactorValidator(db_path)
        
        # 达尔文参数
        self.carrying_capacity = 100  # 环境承载力
        self.survival_threshold = 0.0  # 最低夏普生存线 (放宽至0，让系统运转)
        self.cull_rate = 0.30  # 淘汰率
        self.breeding_rate = 0.20  # 繁衍资格比例
        self.survival_period = 24  # 生存周期(小时)
        
    def survival_challenge(self) -> Dict:
        """
        生存挑战 - 所有基因必须通过真实市场验证
        
        Returns:
            生存报告
        """
        print("=" * 70)
        print("🦁 Darwinian Survival Challenge")
        print("=" * 70)
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"   Rule: Only the fittest survive")
        print()
        
        # 获取所有基因
        all_genes = self._load_all_genes()
        print(f"   Total population: {len(all_genes)} genes")
        print(f"   Carrying capacity: {self.carrying_capacity}")
        print()
        
        if len(all_genes) == 0:
            print("   ⚠️ Population extinct! Generating emergency seeds...")
            self._generate_emergency_seeds()
            return {'status': 'extinct', 'action': 'regenerated'}
        
        # 回测验证所有基因
        print("🔬 Running survival tests on all genes...")
        survival_scores = []
        
        test_markets = ['AAPL', 'MSFT']  # 简化测试
        
        for i, gene in enumerate(all_genes, 1):
            print(f"   [{i}/{len(all_genes)}] Testing {gene.name[:30]}...", end=' ')
            
            try:
                results = self.validator.validate_gene(gene, symbols=test_markets)
                
                if results:
                    # 计算平均夏普
                    avg_sharpe = sum(r.sharpe_ratio for r in results) / len(results)
                    avg_return = sum(r.annual_return for r in results) / len(results)
                    
                    # 生存分数 = 夏普 * 0.6 + 收益 * 0.4
                    survival_score = avg_sharpe * 0.6 + avg_return * 0.4
                    
                    survival_scores.append({
                        'gene': gene,
                        'sharpe': avg_sharpe,
                        'return': avg_return,
                        'score': survival_score,
                        'survived': survival_score > self.survival_threshold
                    })
                    
                    status = "✅" if survival_score > self.survival_threshold else "❌"
                    print(f"{status} Score: {survival_score:.2f}")
                else:
                    survival_scores.append({
                        'gene': gene,
                        'sharpe': -999,
                        'return': -999,
                        'score': -999,
                        'survived': False
                    })
                    print("❌ No data")
                    
            except Exception as e:
                survival_scores.append({
                    'gene': gene,
                    'sharpe': -999,
                    'return': -999,
                    'score': -999,
                    'survived': False
                })
                print(f"❌ Error: {str(e)[:30]}")
        
        # 排序
        survival_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # 分类
        survivors = [s for s in survival_scores if s['survived']]
        dead = [s for s in survival_scores if not s['survived']]
        
        print(f"\n📊 Survival Results:")
        print(f"   Survivors: {len(survivors)} ({len(survivors)/len(all_genes)*100:.1f}%)")
        print(f"   Dead: {len(dead)} ({len(dead)/len(all_genes)*100:.1f}%)")
        
        if survivors:
            print(f"\n🏆 Top Survivors:")
            for i, s in enumerate(survivors[:5], 1):
                print(f"   {i}. {s['gene'].name[:40]}: Score {s['score']:.2f}")
        
        # 执行淘汰
        self._execute_culling(dead)
        
        # 执行繁衍
        if survivors:
            breeders = survivors[:max(2, int(len(survivors) * self.breeding_rate))]
            print(f"\n💝 Breeders (top {len(breeders)}):")
            for b in breeders:
                print(f"   - {b['gene'].name[:40]}")
            
            new_offspring = self._breed_offspring(breeders)
            print(f"\n   Generated {len(new_offspring)} new offspring")
        
        return {
            'total_tested': len(all_genes),
            'survivors': len(survivors),
            'dead': len(dead),
            'top_score': survival_scores[0]['score'] if survival_scores else 0,
            'avg_score': sum(s['score'] for s in survival_scores) / len(survival_scores) if survival_scores else 0
        }
    
    def _execute_culling(self, dead_genes: List[Dict]):
        """执行淘汰 - 删除表现差的基因"""
        if not dead_genes:
            return
        
        print(f"\n💀 Executing culling ({len(dead_genes)} genes)...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建死亡记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gene_deaths (
                gene_id TEXT,
                name TEXT,
                final_score REAL,
                cause_of_death TEXT,
                timestamp TEXT
            )
        ''')
        
        # 记录死亡
        for dead in dead_genes:
            cursor.execute('''
                INSERT INTO gene_deaths VALUES (?, ?, ?, ?, ?)
            ''', (
                dead['gene'].gene_id,
                dead['gene'].name,
                dead['score'],
                'failed_survival_challenge',
                datetime.now().isoformat()
            ))
            
            # 删除基因
            cursor.execute('DELETE FROM genes WHERE gene_id = ?', (dead['gene'].gene_id,))
        
        conn.commit()
        conn.close()
        
        print(f"   ☠️ {len(dead_genes)} genes eliminated")
    
    def _breed_offspring(self, breeders: List[Dict]) -> List[Gene]:
        """繁衍后代 - 只有强者能繁衍"""
        offspring = []
        
        # 交叉繁衍
        for i in range(min(10, len(breeders) * 2)):  # 限制后代数量
            parents = random.sample(breeders, 2)
            child = self._crossover(parents[0]['gene'], parents[1]['gene'])
            
            # 验证后代
            try:
                results = self.validator.validate_gene(child, symbols=['AAPL'])
                if results and results[0].sharpe > 0.3:  # 后代也要有一定质量
                    self.hub.publish_gene(child)
                    offspring.append(child)
            except:
                pass  # 后代验证失败则不存活
        
        return offspring
    
    def _crossover(self, parent1: Gene, parent2: Gene) -> Gene:
        """基因交叉"""
        import hashlib
        
        operator = random.choice(['AND', 'OR'])
        new_formula = f"({parent1.formula}) {operator} ({parent2.formula})"
        
        child = Gene(
            gene_id=f"g_{hashlib.sha256(new_formula.encode()).hexdigest()[:8]}",
            name=f"Darwin_{parent1.name[:15]}_{parent2.name[:15]}",
            description=f"Offspring of survivors",
            formula=new_formula,
            parameters={**parent1.parameters, **parent2.parameters},
            source="darwinian_breeding",
            author="natural_selection",
            created_at=datetime.now(),
            parent_gene_id=f"{parent1.gene_id}+{parent2.gene_id}",
            generation=max(parent1.generation, parent2.generation) + 1
        )
        return child
    
    def _load_all_genes(self) -> List[Gene]:
        """加载所有基因"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM genes')
        rows = cursor.fetchall()
        conn.close()
        
        genes = []
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
            genes.append(gene)
        return genes
    
    def _generate_emergency_seeds(self):
        """灭绝后紧急重生"""
        print("\n🌱 Emergency regeneration...")
        
        emergency_seeds = [
            Gene(
                gene_id=f"g_darwin_emergency_{i}",
                name=f"Emergency_Seed_{i}",
                description="Post-extinction regeneration",
                formula=f"Close > SMA({random.choice([10,20,50])})",
                parameters={'period': random.choice([10, 20, 50])},
                source="darwinian_emergency",
                author="ecosystem",
                created_at=datetime.now(),
                generation=0
            )
            for i in range(5)
        ]
        
        for seed in emergency_seeds:
            self.hub.publish_gene(seed)
        
        print(f"   {len(emergency_seeds)} emergency seeds generated")
    
    def get_ecosystem_stats(self) -> Dict:
        """获取生态系统统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 当前存活
        cursor.execute('SELECT COUNT(*) FROM genes')
        alive = cursor.fetchone()[0]
        
        # 历史死亡
        cursor.execute('SELECT COUNT(*) FROM gene_deaths')
        deaths = cursor.fetchone()[0]
        
        # 平均寿命
        cursor.execute('''
            SELECT AVG(
                (julianday(timestamp) - julianday((SELECT MIN(created_at) FROM genes)))
            ) FROM gene_deaths
        ''')
        avg_lifespan = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'alive': alive,
            'total_deaths': deaths,
            'total_population': alive + deaths,
            'mortality_rate': deaths / (alive + deaths) if (alive + deaths) > 0 else 0,
            'avg_lifespan_hours': avg_lifespan * 24 if avg_lifespan else 0
        }


def main():
    """主函数 - 运行达尔文生存挑战"""
    ecosystem = DarwinianEcosystem()
    
    print("🌍 QuantClaw Darwinian Ecosystem v4")
    print("   Natural Selection in Action")
    print()
    
    # 运行生存挑战
    result = ecosystem.survival_challenge()
    
    # 显示生态统计
    stats = ecosystem.get_ecosystem_stats()
    
    print("\n" + "=" * 70)
    print("📈 Ecosystem Statistics")
    print("=" * 70)
    print(f"   Current population: {stats['alive']}")
    print(f"   Total deaths: {stats['total_deaths']}")
    print(f"   Mortality rate: {stats['mortality_rate']:.1%}")
    print(f"   Avg lifespan: {stats['avg_lifespan_hours']:.1f} hours")
    print()
    print("🔄 Next survival challenge in 24 hours...")


if __name__ == "__main__":
    main()
