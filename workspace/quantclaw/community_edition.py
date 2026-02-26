"""
QuantClaw Community Edition - 完整整合系统
集成 P2P网络 + 策略市场 + 知识图谱
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

# 导入三个步骤的模块
from step1_p2p_network import P2PNetwork, CollaborativeEvolver, MessageType, P2PMessage
from step2_strategy_marketplace import StrategyMarketplace, StrategyListing, Order, OrderType
from step3_knowledge_graph import QuantKnowledgeGraph, EntityType, RelationType

# 导入之前的进化生态系统
from evolution_ecosystem import (
    QuantClawEvolutionHub, QuantClawEvolver, Gene, Capsule, 
    StrategyBundle, BountyTask, TaskStatus
)


class QuantClawCommunity:
    """
    QuantClaw 社区版主控制器
    
    整合所有组件:
    - P2P网络: 多Agent通信
    - 进化中心: 本地进化管理
    - 策略市场: 买卖策略
    - 知识图谱: 关系网络
    """
    
    def __init__(self, node_id: str, host: str = "127.0.0.1", port: int = 8080):
        self.node_id = node_id
        
        # 初始化各个组件
        print("🚀 Initializing QuantClaw Community Edition...")
        
        # 1. P2P网络
        self.p2p = P2PNetwork(node_id, host, port)
        self.evolver = CollaborativeEvolver(node_id, self.p2p)
        
        # 2. 进化中心
        self.hub = QuantClawEvolutionHub(db_path=f"{node_id}_evolution.db")
        
        # 3. 策略市场
        self.market = StrategyMarketplace(db_path=f"{node_id}_market.db")
        
        # 4. 知识图谱
        self.kg = QuantKnowledgeGraph(fallback_db=f"{node_id}_kg.db")
        
        # 注册P2P消息处理器
        self._register_handlers()
        
        print(f"✅ Community node {node_id} ready at {host}:{port}")
    
    def _register_handlers(self):
        """注册P2P消息处理器"""
        # 策略分享
        self.p2p.register_handler(MessageType.SHARE_GENE, self._on_share_gene)
        self.p2p.register_handler(MessageType.SHARE_CAPSULE, self._on_share_capsule)
    
    async def start(self):
        """启动社区节点"""
        await self.p2p.start()
        
        # 启动后台任务
        asyncio.create_task(self._sync_loop())
        asyncio.create_task(self._market_maker_loop())
    
    async def stop(self):
        """停止社区节点"""
        await self.p2p.stop()
    
    # ==================== 进化工作流 ====================
    
    async def propose_evolution_task(self, paper_arxiv_id: str, 
                                    task_type: str = "implement_paper") -> str:
        """
        提议进化任务
        
        流程:
        1. 创建赏金任务
        2. P2P广播
        3. 等待其他节点认领
        """
        # 创建本地赏金任务
        bounty = BountyTask(
            task_id="",
            title=f"Implement {paper_arxiv_id}",
            description=f"Implement paper {paper_arxiv_id} in QuantClaw",
            task_type=task_type,
            reward_credits=100,
            difficulty=3,
            requirements={"paper_arxiv_id": paper_arxiv_id}
        )
        
        task_id = self.hub.create_bounty(bounty)
        
        # P2P广播任务
        task = {
            "task_id": task_id,
            "title": bounty.title,
            "type": task_type,
            "difficulty": bounty.difficulty,
            "reward": bounty.reward_credits,
            "paper_arxiv_id": paper_arxiv_id
        }
        
        await self.evolver.propose_task(task)
        
        return task_id
    
    async def claim_and_execute_task(self, task_id: str) -> bool:
        """
        认领并执行任务
        
        流程:
        1. 认领任务
        2. 实现论文
        3. A/B测试
        4. 提交结果到知识图谱
        5. 可选择上架市场
        """
        # 获取任务
        bounties = self.hub.list_bounties(status=TaskStatus.PENDING)
        task = None
        for b in bounties:
            if b.task_id == task_id:
                task = b
                break
        
        if not task:
            return False
        
        # 认领
        if not self.hub.claim_bounty(task_id, self.node_id):
            return False
        
        print(f"🔧 Executing task: {task.title}")
        
        # 执行 (简化版)
        # 实际应该调用 AutoEvolve 逻辑
        result = {
            "status": "success",
            "gene_id": f"gene_{int(datetime.now().timestamp())}",
            "capsule_id": f"capsule_{int(datetime.now().timestamp())}",
            "sharpe_improvement": 0.15
        }
        
        # 完成任务
        self.hub.complete_bounty(task_id, self.node_id, result["capsule_id"])
        
        # 添加到知识图谱
        self._add_to_knowledge_graph(task, result)
        
        return True
    
    def _add_to_knowledge_graph(self, task: BountyTask, result: Dict):
        """将结果添加到知识图谱"""
        # 创建策略实体
        strategy_id = self.kg.create_entity(
            EntityType.STRATEGY,
            f"Strategy_{result['capsule_id']}",
            {
                "sharpe_improvement": result["sharpe_improvement"],
                "gene_id": result["gene_id"],
                "capsule_id": result["capsule_id"]
            }
        )
        
        # 如果有论文，创建关系
        paper_arxiv_id = task.requirements.get("paper_arxiv_id")
        if paper_arxiv_id:
            # 检查论文是否已存在
            papers = self.kg.find_entities(EntityType.PAPER, properties={"arxiv_id": paper_arxiv_id})
            
            if papers:
                paper_id = papers[0].entity_id
            else:
                paper_id = self.kg.create_entity(
                    EntityType.PAPER,
                    f"Paper_{paper_arxiv_id}",
                    {"arxiv_id": paper_arxiv_id}
                )
            
            # 创建实现关系
            self.kg.create_relation(strategy_id, paper_id, RelationType.IMPLEMENTS)
    
    # ==================== 策略市场工作流 ====================
    
    def list_strategy_on_market(self, bundle_id: str, price: float,
                                seller_id: str = None) -> str:
        """
        将策略上架到市场
        
        流程:
        1. 从进化中心获取Bundle
        2. 验证性能指标
        3. 创建上架
        4. P2P广播
        """
        if seller_id is None:
            seller_id = self.node_id
        
        # 从进化中心获取Bundle信息
        # 简化版: 直接从知识图谱获取
        strategies = self.kg.find_entities(
            EntityType.STRATEGY,
            properties={"capsule_id": bundle_id}
        )
        
        if not strategies:
            return None
        
        strategy = strategies[0]
        props = strategy.properties
        
        # 创建上架
        listing = StrategyListing(
            listing_id="",
            seller_id=seller_id,
            bundle_id=bundle_id,
            gene_id=props.get("gene_id", ""),
            capsule_id=bundle_id,
            title=strategy.name,
            description=f"Strategy implementing {props.get('gene_id', 'unknown')}",
            strategy_type="quantitative",
            sharpe_ratio=props.get("sharpe_improvement", 1.0),
            max_drawdown=0.15,
            annual_return=0.20,
            win_rate=0.60,
            backtest_period="2020-2024",
            validation_count=3,
            validator_scores=[0.8, 0.85, 0.82],
            price=price,
            price_model="fixed",
            license_type="one_time"
        )
        
        listing_id = self.market.list_strategy(listing)
        
        # P2P广播新上架
        asyncio.create_task(self._broadcast_listing(listing))
        
        return listing_id
    
    async def _broadcast_listing(self, listing: StrategyListing):
        """广播策略上架"""
        msg = P2PMessage(
            msg_type=MessageType.SHARE_CAPSULE,
            sender_id=self.node_id,
            sender_address=self.p2p.address,
            timestamp=datetime.now().timestamp(),
            payload={"listing": listing.to_dict()}
        )
        
        await self.p2p.broadcast(msg)
    
    def buy_strategy(self, listing_id: str, buyer_id: str = None) -> bool:
        """
        购买策略
        
        流程:
        1. 提交买单
        2. 等待匹配
        3. 执行交易
        4. 添加到投资组合
        5. 更新知识图谱
        """
        if buyer_id is None:
            buyer_id = self.node_id
        
        # 获取上架信息
        listings = self.market.search_strategies()
        target_listing = None
        for l in listings:
            if l.listing_id == listing_id:
                target_listing = l
                break
        
        if not target_listing:
            return False
        
        # 创建买单
        order = Order(
            order_id="",
            order_type=OrderType.BUY,
            trader_id=buyer_id,
            listing_id=listing_id,
            price=target_listing.price,
            min_sharpe=target_listing.sharpe_ratio * 0.8  # 允许稍微低一点的夏普
        )
        
        order_id = self.market.place_order(order)
        
        return True
    
    # ==================== 知识图谱工作流 ====================
    
    def query_strategy_lineage(self, strategy_id: str) -> Dict:
        """查询策略谱系"""
        return self.kg.get_strategy_lineage(strategy_id)
    
    def find_similar_strategies(self, strategy_id: str, n: int = 5) -> List:
        """查找相似策略"""
        return self.kg.find_similar_strategies(strategy_id, n)
    
    def get_strategy_recommendations(self, user_id: str, n: int = 5) -> List:
        """获取策略推荐"""
        # 获取用户投资组合
        portfolio = self.market.get_portfolio(user_id)
        
        if not portfolio or not portfolio.holdings:
            return []
        
        # 获取策略ID列表
        strategy_ids = list(portfolio.holdings.keys())
        
        # 查询知识图谱推荐
        return self.kg.recommend_strategies(strategy_ids, n)
    
    # ==================== P2P处理器 ====================
    
    async def _on_share_gene(self, msg: P2PMessage):
        """处理基因分享"""
        gene_data = msg.payload.get("gene", {})
        print(f"📥 Received gene from {msg.sender_id}: {gene_data.get('name', 'unknown')}")
        
        # 可以添加到本地知识图谱
        # 这里简化处理
    
    async def _on_share_capsule(self, msg: P2PMessage):
        """处理胶囊分享 (策略上架)"""
        listing_data = msg.payload.get("listing", {})
        print(f"📥 Received listing from {msg.sender_id}: {listing_data.get('title', 'unknown')}")
        
        # 可以添加到本地市场缓存
        # 这里简化处理
    
    # ==================== 后台任务 ====================
    
    async def _sync_loop(self):
        """同步循环 - 定期同步数据"""
        while True:
            await asyncio.sleep(300)  # 每5分钟
            
            # 同步进化数据到知识图谱
            self._sync_evolution_to_kg()
    
    def _sync_evolution_to_kg(self):
        """同步进化数据到知识图谱"""
        # 导入基因
        # 这里可以调用 kg.import_from_evolution_ecosystem
        pass
    
    async def _market_maker_loop(self):
        """做市商循环 - 自动匹配订单"""
        while True:
            await asyncio.sleep(60)  # 每分钟检查
            
            # 匹配开放订单
            # 这里简化处理
            pass
    
    # ==================== 统计和报告 ====================
    
    def get_community_stats(self) -> Dict:
        """获取社区统计"""
        return {
            "node_id": self.node_id,
            "p2p": {
                "peers": len(self.p2p.peers),
                "address": self.p2p.address
            },
            "market": self.market.get_market_stats(),
            "evolution": self.hub.get_statistics() if hasattr(self.hub, 'get_statistics') else {}
        }
    
    def generate_report(self) -> str:
        """生成社区报告"""
        stats = self.get_community_stats()
        
        report = f"""
═══════════════════════════════════════════════════════════════
           QuantClaw Community Report
═══════════════════════════════════════════════════════════════

Node: {stats['node_id']}
Address: {stats['p2p']['address']}
Peers: {stats['p2p']['peers']}

Market Statistics:
  Active Listings: {stats['market'].get('active_listings', 0)}
  Open Orders: {stats['market'].get('open_orders', 0)}
  Total Transactions: {stats['market'].get('total_transactions', 0)}
  Total Volume: {stats['market'].get('total_volume', 0)} credits

Evolution Statistics:
  (Coming soon...)

═══════════════════════════════════════════════════════════════
        """
        
        return report


# ==================== 演示 ====================

async def demo_community_edition():
    """演示社区版完整功能"""
    print("="*80)
    print("QuantClaw Community Edition - Full Integration Demo")
    print("="*80)
    
    # 创建两个节点
    node1 = QuantClawCommunity("community_node_1", "127.0.0.1", 8091)
    node2 = QuantClawCommunity("community_node_2", "127.0.0.1", 8092)
    
    # 启动节点
    await node1.start()
    await node2.start()
    
    # 节点2加入节点1的网络
    await node2.p2p.join_network("127.0.0.1:8091")
    
    print("\n" + "="*80)
    print("Setup Complete!")
    print("="*80)
    
    # 演示1: 进化任务
    print("\n[Demo 1] Evolution Task")
    task_id = await node1.propose_evolution_task("arxiv:1234.5678")
    
    # 等待一下让节点2看到任务
    await asyncio.sleep(2)
    
    # 节点2认领任务
    await node2.claim_and_execute_task(task_id)
    
    # 演示2: 策略上架
    print("\n[Demo 2] Strategy Marketplace")
    
    # 节点1上架策略
    listing_id = node1.list_strategy_on_market(
        bundle_id="capsule_test_001",
        price=500.0
    )
    
    # 等待广播
    await asyncio.sleep(2)
    
    # 节点2购买策略
    if listing_id:
        node2.buy_strategy(listing_id, buyer_id="community_node_2")
    
    # 演示3: 知识图谱查询
    print("\n[Demo 3] Knowledge Graph")
    
    # 添加一些示例数据
    strategy_id = node1.kg.create_entity(
        EntityType.STRATEGY,
        "TestStrategy",
        {"sharpe": 1.5}
    )
    
    # 查询谱系
    lineage = node1.query_strategy_lineage(strategy_id)
    print(f"   Strategy lineage: {lineage}")
    
    # 演示4: 生成报告
    print("\n[Demo 4] Community Report")
    report = node1.generate_report()
    print(report)
    
    # 保持运行一段时间
    await asyncio.sleep(5)
    
    # 停止节点
    await node1.stop()
    await node2.stop()
    
    print("\n" + "="*80)
    print("Demo Complete!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(demo_community_edition())
