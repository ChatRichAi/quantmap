#!/usr/bin/env python3
"""
QuantClaw Pro with Research Enhancement
基于学术论文增强的MBTI股性分类系统

Usage:
    python run_research.py [command]

Commands:
    demo        - 运行研究增强版演示
    fetch       - 抓取最新arXiv论文
    test        - 运行A/B测试对比
    analyze     - 分析指定股票
    server      - 启动持续扫描服务
"""

import sys
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def run_demo():
    """运行演示"""
    print("=" * 80)
    print("QuantClaw Pro Research Edition - Quick Demo")
    print("=" * 80)
    
    try:
        from quantclaw_research_edition import (
            QuantClawProResearch, 
            ResearchEnhancementConfig,
            demo_research_edition
        )
        demo_research_edition()
    except Exception as e:
        print(f"Error running demo: {e}")
        import traceback
        traceback.print_exc()

def run_fetch():
    """抓取论文"""
    from research.arxiv_crawler import ArxivPaperCrawler, PaperAnalyzer
    
    print("Fetching latest papers from arXiv...")
    crawler = ArxivPaperCrawler()
    papers = crawler.fetch_recent_papers(max_results=50)
    
    if papers:
        print(f"Fetched {len(papers)} papers. Analyzing...")
        analyzer = PaperAnalyzer()
        analyzer.batch_analyze(crawler, limit=30)
        print("Analysis complete!")
    else:
        print("No new papers found.")

def run_test():
    """运行A/B测试"""
    from research.ab_testing_framework import PaperValidationFramework
    
    print("Running A/B test: Baseline vs Research Features...")
    framework = PaperValidationFramework()
    results = framework.run_full_comparison()
    
    if 'improvements' in results:
        print("\nKey Improvements:")
        for metric, stats in results['improvements'].items():
            print(f"  {metric}: {stats['mean']*100:+.2f}%")

def run_analyze(ticker: str = "AAPL"):
    """分析股票"""
    import yfinance as yf
    from quantclaw_research_edition import (
        QuantClawProResearch, 
        ResearchEnhancementConfig
    )
    
    print(f"Analyzing {ticker} with research features...")
    
    # 获取数据
    df = yf.download(ticker, period='3mo', progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower().replace(' ', '_') for c in df.columns]
    else:
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    
    # 分析
    config = ResearchEnhancementConfig(use_advanced_features=True)
    claw = QuantClawProResearch(config)
    
    report = claw.generate_research_report(ticker, df)
    print(report)

def run_server():
    """启动服务"""
    from research.arxiv_crawler import ArxivPaperCrawler
    import schedule
    import time
    
    def daily_job():
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Running daily paper fetch...")
        crawler = ArxivPaperCrawler()
        papers = crawler.fetch_recent_papers(max_results=20)
        if papers:
            from research.arxiv_crawler import PaperAnalyzer
            analyzer = PaperAnalyzer()
            analyzer.batch_analyze(crawler, limit=20)
        print(f"Daily job complete. {len(papers)} papers processed.")
    
    # 每天9点运行
    schedule.every().day.at("09:00").do(daily_job)
    
    print("Research server started. Will fetch papers daily at 09:00.")
    print("Press Ctrl+C to stop.")
    
    # 立即运行一次
    daily_job()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def main():
    parser = argparse.ArgumentParser(
        description='QuantClaw Pro Research Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_research.py demo              # 运行演示
    python run_research.py fetch             # 抓取论文
    python run_research.py test              # A/B测试
    python run_research.py analyze AAPL      # 分析股票
    python run_research.py server            # 启动服务
        """
    )
    
    parser.add_argument('command', choices=['demo', 'fetch', 'test', 'analyze', 'server'],
                       help='Command to run')
    parser.add_argument('--ticker', default='AAPL', help='Stock ticker for analyze command')
    
    args = parser.parse_args()
    
    commands = {
        'demo': run_demo,
        'fetch': run_fetch,
        'test': run_test,
        'analyze': lambda: run_analyze(args.ticker),
        'server': run_server,
    }
    
    try:
        commands[args.command]()
    except KeyboardInterrupt:
        print("\nStopped by user.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import pandas as pd  # 提前导入避免后面出错
    main()
