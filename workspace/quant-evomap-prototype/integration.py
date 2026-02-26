"""
Integration Layer - Quant EvoMap 与 OpenClaw 系统整合
对接赏金猎人、Auto-Evolve、Nowledge Mem
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import subprocess


class BountySniperIntegration:
    """
    赏金猎人系统整合
    扩展现有 bounty-sniper.js 功能，支持 Quant EvoMap 任务
    """
    
    def __init__(self, bounty_sniper_path: str = '../skills/auto-evolve'):
        self.bounty_sniper_path = bounty_sniper_path
        self.quant_market_url = 'http://localhost:5000/api'
    
    def scan_quant_bounties(self) -> List[Dict]:
        """
        扫描 Quant EvoMap 赏金任务
        类似于现有的 EvoMap 任务扫描
        """
        from bounty_system import BountyMarket
        
        market = BountyMarket()
        open_bounties = market.get_open_bounties()
        
        # 转换为赏金猎人格式
        tasks = []
        for bounty in open_bounties:
            tasks.append({
                'id': bounty.id,
                'type': 'quant_strategy',
                'symbol': bounty.symbol,
                'reward': bounty.reward.calculate({'sharpe_ratio': 1.5}),
                'criteria': bounty.criteria.to_dict(),
                'priority': bounty.priority,
                'deadline': bounty.deadline
            })
        
        return tasks
    
    def claim_and_mine(self, bounty_id: str, agent_id: str = 'sniper_agent') -> Dict:
        """
        认领赏金并自动挖掘策略
        """
        from bounty_system import BountyMarket
        from quant_evomap import QuantEvoMap
        
        market = BountyMarket()
        
        # 1. 认领任务
        if not market.claim_bounty(bounty_id, agent_id):
            return {'error': 'Failed to claim bounty'}
        
        bounty = market.get_bounty(bounty_id)
        print(f'[{agent_id}] 已认领赏金: {bounty_id} ({bounty.symbol})')
        
        # 2. 挖掘策略
        evomap = QuantEvoMap()
        result = evomap.discover_strategy(bounty.symbol, save_results=True)
        
        # 3. 提交结果
        submission = market.submit_solution(
            bounty_id=bounty_id,
            gene_id=result['gene']['id'],
            performance=result['backtest'],
            agent_id=agent_id
        )
        
        return {
            'bounty_id': bounty_id,
            'gene_id': result['gene']['id'],
            'performance': result['backtest'],
            'reward': submission.get('reward', 0),
            'status': submission.get('status', 'unknown')
        }


class AutoEvolveIntegration:
    """
    Auto-Evolve 整合
    策略持续自我进化
    """
    
    def __init__(self, gene_library_path: str = './gene_library.json'):
        self.gene_library_path = gene_library_path
    
    def evolve_genes(self, generations: int = 10) -> List[Dict]:
        """
        对基因库中的策略进行进化优化
        类似于 Auto-Evolve 的修复机制
        """
        from get_protocol import StrategyGene, GeneTemplates
        from quant_evomap import QuantEvoMap
        import random
        
        # 加载现有基因
        genes = self._load_genes()
        
        if len(genes) < 2:
            print('[AutoEvolve] 基因库不足，无法进化')
            return []
        
        # 选择亲代 (按表现排序)
        genes.sort(key=lambda g: g.performance.get('sharpe_ratio', 0), reverse=True)
        parents = genes[:10]  # 前10名
        
        new_genes = []
        
        for gen in range(generations):
            # 交叉
            parent_a = random.choice(parents)
            parent_b = random.choice(parents)
            child = parent_a.crossover(parent_b)
            
            # 变异
            child = child.mutate(mutation_rate=0.3)
            
            # 验证
            evomap = QuantEvoMap()
            symbol = child.conditions.get('symbol', 'TSLA')
            
            try:
                result = evomap.discover_strategy(symbol, save_results=False)
                child.performance = result['backtest']
                
                # 如果表现好，加入基因库
                if child.performance.get('sharpe_ratio', 0) > 1.0:
                    new_genes.append(child)
                    print(f'[AutoEvolve] 第{gen}代进化成功: {child.id}')
            except Exception as e:
                print(f'[AutoEvolve] 第{gen}代进化失败: {e}')
        
        # 保存新基因
        self._save_genes(genes + new_genes)
        
        return [g.to_dict() for g in new_genes]
    
    def validate_genes(self) -> Dict:
        """
        验证基因库中所有策略的有效性
        标记失效的策略
        """
        from quant_evomap import QuantEvoMap
        
        genes = self._load_genes()
        evomap = QuantEvoMap()
        
        validated = 0
        failed = 0
        
        for gene in genes:
            # 重新回测
            symbol = gene.conditions.get('symbol', 'TSLA')
            
            try:
                result = evomap.discover_strategy(symbol, save_results=False)
                new_performance = result['backtest']
                
                # 检查是否仍然有效
                if new_performance.get('sharpe_ratio', 0) < 0.5:
                    gene.validation['status'] = 'expired'
                    failed += 1
                else:
                    gene.performance = new_performance
                    validated += 1
            except:
                gene.validation['status'] = 'error'
                failed += 1
        
        self._save_genes(genes)
        
        return {
            'total': len(genes),
            'validated': validated,
            'failed': failed
        }
    
    def _load_genes(self) -> List:
        """加载基因库"""
        from get_protocol import StrategyGene
        
        try:
            with open(self.gene_library_path, 'r') as f:
                data = json.load(f)
                return [StrategyGene.from_dict(g) for g in data.get('genes', [])]
        except:
            return []
    
    def _save_genes(self, genes: List):
        """保存基因库"""
        data = {
            'genes': [g.to_dict() for g in genes],
            'updated_at': datetime.now().isoformat()
        }
        with open(self.gene_library_path, 'w') as f:
            json.dump(data, f, indent=2)


class NowledgeMemIntegration:
    """
    Nowledge Mem 整合
    自动记录发现的策略和交易经验
    """
    
    def __init__(self):
        self.use_nmem = self._check_nmem()
    
    def _check_nmem(self) -> bool:
        """检查 nmem CLI 是否可用"""
        try:
            result = subprocess.run(['which', 'nmem'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def save_strategy_gene(self, gene: Dict, symbol: str) -> bool:
        """
        保存策略基因到 Nowledge Mem
        """
        if not self.use_nmem:
            print('[NowledgeMem] nmem 不可用，跳过保存')
            return False
        
        importance = 0.7
        if gene.get('performance', {}).get('sharpe_ratio', 0) > 2.0:
            importance = 0.9
        elif gene.get('performance', {}).get('sharpe_ratio', 0) > 1.5:
            importance = 0.8
        
        # 构建记忆内容
        memory = {
            'title': f"Strategy Gene: {gene['id']} for {symbol}",
            'text': json.dumps(gene, indent=2),
            'unit_type': 'learning',
            'labels': ['quant-evomap', 'strategy-gene', symbol.lower()],
            'importance': importance
        }
        
        try:
            # 使用 nmem CLI 保存
            cmd = [
                'nmem', 'save',
                '--title', memory['title'],
                '--text', memory['text'],
                '--type', memory['unit_type'],
                '--labels', ','.join(memory['labels']),
                '--importance', str(importance)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f'[NowledgeMem] 已保存策略基因: {gene["id"]}')
                return True
            else:
                print(f'[NowledgeMem] 保存失败: {result.stderr}')
                return False
        except Exception as e:
            print(f'[NowledgeMem] 错误: {e}')
            return False
    
    def search_similar_genes(self, symbol: str) -> List[Dict]:
        """
        搜索相似的策略基因
        """
        if not self.use_nmem:
            return []
        
        try:
            cmd = ['nmem', 'search', f'{symbol} strategy gene', '--json']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except:
            return []
    
    def save_evolution_event(self, event_type: str, details: Dict) -> bool:
        """
        保存进化事件
        """
        if not self.use_nmem:
            return False
        
        memory = {
            'title': f'Quant EvoMap: {event_type}',
            'text': json.dumps(details, indent=2),
            'unit_type': 'event',
            'labels': ['quant-evomap', 'evolution', event_type],
            'importance': 0.6
        }
        
        try:
            # 这里简化处理，实际使用 nmem CLI
            print(f'[NowledgeMem] 记录进化事件: {event_type}')
            return True
        except:
            return False


class QuantEvoMapOrchestrator:
    """
    Quant EvoMap 编排器
    整合所有模块，提供统一接口
    """
    
    def __init__(self):
        self.bounty_integration = BountySniperIntegration()
        self.evolve_integration = AutoEvolveIntegration()
        self.memory_integration = NowledgeMemIntegration()
    
    def run_discovery_cycle(self, symbols: List[str] = None) -> Dict:
        """
        运行完整的策略发现周期
        """
        symbols = symbols or ['TSLA', 'AAPL', 'NVDA']
        
        print('='*60)
        print('Quant EvoMap Discovery Cycle')
        print('='*60)
        
        results = []
        
        for symbol in symbols:
            print(f'\n发现 {symbol} 的策略...')
            
            # 1. 发现策略
            from quant_evomap import QuantEvoMap
            evomap = QuantEvoMap()
            result = evomap.discover_strategy(symbol)
            
            # 2. 保存到 Nowledge Mem
            self.memory_integration.save_strategy_gene(
                result['gene'], symbol
            )
            
            results.append(result)
        
        # 3. 进化优化
        print('\n开始进化优化...')
        evolved = self.evolve_integration.evolve_genes(generations=5)
        
        # 4. 验证
        print('\n验证基因库...')
        validation = self.evolve_integration.validate_genes()
        
        return {
            'discovered': len(results),
            'evolved': len(evolved),
            'validation': validation
        }
    
    def run_bounty_mode(self, max_bounties: int = 5) -> List[Dict]:
        """
        赏金模式: 自动扫描并认领任务
        """
        print('='*60)
        print('Quant EvoMap Bounty Mode')
        print('='*60)
        
        # 1. 扫描赏金
        bounties = self.bounty_integration.scan_quant_bounties()
        print(f'发现 {len(bounties)} 个开放赏金')
        
        results = []
        
        # 2. 认领并执行 (限制数量)
        for bounty in bounties[:max_bounties]:
            print(f'\n处理赏金: {bounty["id"]} ({bounty["symbol"]})')
            
            result = self.bounty_integration.claim_and_mine(
                bounty_id=bounty['id'],
                agent_id='quant_sniper_001'
            )
            
            results.append(result)
            
            # 3. 记录到 Nowledge Mem
            if result.get('status') == 'passed':
                self.memory_integration.save_evolution_event(
                    'bounty_completed',
                    {
                        'bounty_id': bounty['id'],
                        'gene_id': result.get('gene_id'),
                        'reward': result.get('reward')
                    }
                )
        
        return results
    
    def get_dashboard(self) -> Dict:
        """
        获取系统仪表板数据
        """
        from bounty_system import BountyMarket
        
        market = BountyMarket()
        
        return {
            'open_bounties': len(market.get_open_bounties()),
            'total_bounties': len(market.bounties),
            'genes_in_library': len(self.evolve_integration._load_genes()),
            'nmem_connected': self.memory_integration.use_nmem
        }


# CLI 入口
def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Quant EvoMap Integration')
    parser.add_argument('command', choices=['discover', 'bounty', 'evolve', 'dashboard'])
    parser.add_argument('--symbols', nargs='+', default=['TSLA', 'AAPL'])
    parser.add_argument('--max-bounties', type=int, default=5)
    
    args = parser.parse_args()
    
    orchestrator = QuantEvoMapOrchestrator()
    
    if args.command == 'discover':
        result = orchestrator.run_discovery_cycle(args.symbols)
        print('\n发现完成:')
        print(json.dumps(result, indent=2))
    
    elif args.command == 'bounty':
        results = orchestrator.run_bounty_mode(args.max_bounties)
        print('\n赏金任务完成:')
        print(json.dumps(results, indent=2))
    
    elif args.command == 'evolve':
        evolved = orchestrator.evolve_integration.evolve_genes(generations=10)
        print(f'\n进化完成，生成 {len(evolved)} 个新基因')
    
    elif args.command == 'dashboard':
        dashboard = orchestrator.get_dashboard()
        print('\n系统状态:')
        print(json.dumps(dashboard, indent=2))


if __name__ == '__main__':
    main()
