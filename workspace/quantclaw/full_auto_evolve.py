"""
QuantClaw Full Auto-Evolve - 完全自动进化系统
定时任务调度 + 全自动循环
"""

import asyncio
import schedule
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List
import sys

sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from community_edition import QuantClawCommunity
from research.auto_evolve import QuantClawAutoEvolve, AutoPaperEvaluator
from research.arxiv_crawler import ArxivPaperCrawler


class QuantClawFullAuto:
    """
    QuantClaw 完全自动进化系统
    
    功能:
    1. 定时抓取arXiv论文
    2. 自动评估和筛选
    3. 自动实现代码
    4. 自动A/B测试
    5. 自动上架市场
    6. 自动更新知识图谱
    
    调度:
    - 每4小时: 抓取论文
    - 每8小时: 运行进化周期
    - 每天: 生成报告
    """
    
    def __init__(self, node_id: str = "auto_evolve_node"):
        self.node_id = node_id
        
        # 初始化社区版
        self.community = QuantClawCommunity(node_id)
        
        # 初始化自动进化
        self.auto_evolve = QuantClawAutoEvolve(
            db_path=f"{node_id}_auto_evolve.db"
        )
        
        # 论文爬虫
        self.crawler = ArxivPaperCrawler()
        
        # 运行状态
        self.is_running = False
        self.evolution_count = 0
        self.success_count = 0
        
        print(f"🤖 QuantClaw Full Auto initialized: {node_id}")
    
    async def start(self):
        """启动全自动系统"""
        print("="*80)
        print("🚀 Starting QuantClaw Full Auto-Evolve System")
        print("="*80)
        
        # 启动社区网络
        await self.community.start()
        
        # 设置定时任务
        self._setup_schedule()
        
        # 启动调度器线程
        self.is_running = True
        scheduler_thread = threading.Thread(target=self._run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        print("\n✅ Full Auto-Evolve started!")
        print("   Schedule:")
        print("   - 00:00: Daily paper fetch")
        print("   - 04:00: Evolution cycle")
        print("   - 08:00: Paper fetch + Evolution")
        print("   - 12:00: Evolution cycle")
        print("   - 16:00: Paper fetch + Evolution")
        print("   - 20:00: Evolution cycle + Daily report")
        print("\nPress Ctrl+C to stop")
        print("="*80)
        
        # 保持运行
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await self.stop()
    
    async def stop(self):
        """停止系统"""
        print("\n🛑 Stopping Full Auto-Evolve...")
        self.is_running = False
        await self.community.stop()
        print("✅ Stopped")
    
    def _setup_schedule(self):
        """设置定时任务"""
        # 每4小时抓取论文
        schedule.every(4).hours.do(self._run_async_task, self.fetch_papers)
        
        # 每8小时运行进化周期
        schedule.every(8).hours.do(self._run_async_task, self.run_evolution_cycle)
        
        # 每天生成报告
        schedule.every().day.at("20:00").do(self._run_async_task, self.generate_daily_report)
        
        # 每小时同步到知识图谱
        schedule.every().hour.do(self._run_async_task, self.sync_to_knowledge_graph)
    
    def _run_scheduler(self):
        """运行调度器 (在单独线程)"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    def _run_async_task(self, async_func):
        """运行异步任务"""
        asyncio.create_task(async_func())
    
    # ==================== 自动任务 ====================
    
    async def fetch_papers(self):
        """自动抓取论文"""
        print(f"\n📚 [{datetime.now().strftime('%Y-%m-%d %H:%M')}] Fetching papers from arXiv...")
        
        try:
            papers = self.crawler.fetch_recent_papers(max_results=20)
            print(f"   Fetched {len(papers)} papers")
            
            # 自动分析
            for paper in papers:
                try:
                    self.crawler.analyze_paper(paper['arxiv_id'])
                except:
                    pass
            
            print(f"   Analysis complete")
            
        except Exception as e:
            print(f"   Error: {e}")
    
    async def run_evolution_cycle(self):
        """运行自动进化周期"""
        print(f"\n🧬 [{datetime.now().strftime('%Y-%m-%d %H:%M')}] Running evolution cycle...")
        
        self.evolution_count += 1
        
        try:
            # 运行进化周期
            cycle = self.auto_evolve.run_evolution_cycle(max_papers=5)
            
            if cycle.status == "success":
                self.success_count += 1
                
                print(f"   ✓ Cycle {cycle.cycle_id} completed")
                print(f"     Papers found: {cycle.papers_found}")
                print(f"     Implemented: {cycle.implementations_successful}")
                print(f"     Improvements: {cycle.improvements_found}")
                
                # 如果有改进，上架到市场
                if cycle.improvements_found > 0:
                    await self._deploy_improvements(cycle)
            else:
                print(f"   ✗ Cycle failed: {cycle.lessons_learned}")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    async def _deploy_improvements(self, cycle):
        """部署改进到市场"""
        print(f"\n📦 Deploying {cycle.improvements_found} improvements to marketplace...")
        
        # 获取最新的实现
        # 简化版: 直接上架
        # 实际应该查询数据库获取改进的策略
        
        listing_id = self.community.list_strategy_on_market(
            bundle_id=f"bundle_auto_{cycle.cycle_id}",
            price=500.0,
            seller_id=self.node_id
        )
        
        if listing_id:
            print(f"   Listed: {listing_id}")
    
    async def sync_to_knowledge_graph(self):
        """同步数据到知识图谱"""
        # 导入进化数据到知识图谱
        try:
            self.community.kg.import_from_evolution_ecosystem(
                f"{self.node_id}_evolution.db"
            )
        except:
            pass
    
    async def generate_daily_report(self):
        """生成每日报告"""
        print("\n" + "="*80)
        print(f"📊 DAILY REPORT - {datetime.now().strftime('%Y-%m-%d')}")
        print("="*80)
        
        stats = {
            "evolution_cycles": self.evolution_count,
            "successful_cycles": self.success_count,
            "success_rate": f"{(self.success_count/max(1,self.evolution_count))*100:.1f}%"
        }
        
        # 社区统计
        community_stats = self.community.get_community_stats()
        
        print(f"\nEvolution Statistics:")
        print(f"  Total cycles: {stats['evolution_cycles']}")
        print(f"  Successful: {stats['successful_cycles']}")
        print(f"  Success rate: {stats['success_rate']}")
        
        print(f"\nCommunity Statistics:")
        print(f"  Peers: {community_stats['p2p']['peers']}")
        print(f"  Market listings: {community_stats['market'].get('active_listings', 0)}")
        print(f"  Market volume: {community_stats['market'].get('total_volume', 0)} credits")
        
        print("\n" + "="*80)
        
        # 保存报告
        report_file = f"reports/daily_report_{datetime.now().strftime('%Y%m%d')}.txt"
        # 实际应该写入文件


# ==================== 一键启动 ====================

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='QuantClaw Full Auto-Evolve')
    parser.add_argument('--node-id', default='auto_node_1', help='Node ID')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    args = parser.parse_args()
    
    auto = QuantClawFullAuto(node_id=args.node_id)
    
    if args.once:
        # 运行一次进化周期
        await auto.fetch_papers()
        await auto.run_evolution_cycle()
        await auto.generate_daily_report()
    else:
        # 启动全自动模式
        await auto.start()


if __name__ == "__main__":
    asyncio.run(main())
