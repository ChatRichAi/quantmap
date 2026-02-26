#!/usr/bin/env python3
"""
QuantClaw CLI - Command Line Interface for QuantClaw Pro
基于MBTI股性分类的量化交易系统

Usage:
    quantclaw analyze <ticker>     # 分析单只股票
    quantclaw portfolio <tickers>  # 分析投资组合
    quantclaw scan                 # 扫描市场
    quantclaw fetch                # 抓取论文
    quantclaw demo                 # 运行演示
    quantclaw -h                  # 显示帮助

Install:
    pip install -e .
    OR add to PATH and chmod +x quantclaw_cli.py
"""

import sys
import argparse
import os
from pathlib import Path
from typing import List, Optional

# Add project path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def print_header():
    print(f"""
{BOLD}{CYAN}
╔═══════════════════════════════════════════════════════════════════╗
║                    QuantClaw Pro v2.0                            ║
║           MBTI-Based Quantitative Trading System                 ║
╚═══════════════════════════════════════════════════════════════════╝
{RESET}
    """)

def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")


def cmd_analyze(ticker: str, full: bool = False):
    """Analyze a single stock"""
    import yfinance as yf
    import pandas as pd
    from quantclaw_research_edition import (
        QuantClawProResearch, 
        ResearchEnhancementConfig
    )
    
    print_info(f"Analyzing {ticker}...")
    
    # Fetch data
    df = yf.download(ticker, period='3mo', progress=False)
    if df.empty:
        print_error(f"Failed to fetch data for {ticker}")
        return
    
    # Handle columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower().replace(' ', '_') for c in df.columns]
    else:
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    
    # Analyze
    config = ResearchEnhancementConfig(
        use_advanced_features=True,
        feature_mode="hybrid" if full else "basic"
    )
    claw = QuantClawProResearch(config)
    
    if full:
        report = claw.generate_research_report(ticker, df)
        print(report)
    else:
        result = claw.analyze_stock_enhanced(ticker, df)
        cog = result['cognition']
        
        print(f"\n{BOLD}Analysis Result for {ticker}{RESET}")
        print("-" * 50)
        print(f"  MBTI Type: {GREEN}{cog['mbti_type']}{RESET} ({cog['mbti_name']})")
        print(f"  Category:  {cog['category']}")
        print(f"  Risk:      {cog['risk_level']}")
        print(f"  Confidence: {cog['confidence']:.2%}")
        
        # Strategy
        dec = result.get('decision', {})
        if dec and 'composite_signal' in dec:
            signal = dec['composite_signal'].get('signal', 'N/A')
            print(f"  Signal:    {signal}")
        
        print("-" * 50)


def cmd_portfolio(tickers: List[str], max_position: float = 0.25):
    """Analyze a portfolio of stocks"""
    import yfinance as yf
    import pandas as pd
    from quantclaw_pro import QuantClawPro
    from quantclaw_pro import QuantClawConfig
    
    print_info(f"Analyzing portfolio: {', '.join(tickers)}")
    
    # Fetch data
    data = {}
    for ticker in tickers:
        print_info(f"Fetching {ticker}...")
        df = yf.download(ticker, period='3mo', progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0].lower().replace(' ', '_') for c in df.columns]
            else:
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            data[ticker] = df
    
    if len(data) < 2:
        print_error("Need at least 2 stocks for portfolio analysis")
        return
    
    # Analyze portfolio
    config = QuantClawConfig(
        use_advanced_features=False,
        max_position=max_position
    )
    claw = QuantClawPro(config)
    
    result = claw.analyze_portfolio(tickers=list(data.keys()))
    
    print(f"\n{BOLD}Portfolio Analysis Results{RESET}")
    print("=" * 50)
    
    # Show individual stock analysis
    print(f"\n{GREEN}Individual Stock MBTI:{RESET}")
    for ticker, analysis in result.get('individual_analysis', {}).items():
        cog = analysis.get('cognition', {})
        mbti = cog.get('mbti_type', 'N/A')
        name = cog.get('mbti_name', '')
        risk = cog.get('risk_level', 'N/A')
        print(f"  {ticker:6} -> {mbti:4} ({name}) - Risk: {risk}")
    
    # Show portfolio allocation
    allocation = result.get('allocation', {})
    if allocation:
        print(f"\n{BLUE}Recommended Allocation:{RESET}")
        for ticker, weight in sorted(allocation.items(), key=lambda x: -x[1]):
            bar = "█" * int(weight * 20)
            print(f"  {ticker:6} {weight*100:5.1f}% {bar}")
    
    # Show recommendations
    if 'recommendations' in result:
        print(f"\n{YELLOW}Recommendations:{RESET}")
        for rec in result['recommendations']:
            print(f"  • {rec}")
    
    print("=" * 50)


def cmd_scan(market: str = "sp500", limit: int = 20):
    """Scan market for stock MBTI types"""
    import yfinance as yf
    import pandas as pd
    from quantclaw_research_edition import (
        QuantClawProResearch, 
        ResearchEnhancementConfig
    )
    
    # Sample tickers (in production, would use a full list)
    SAMPLE_TICKERS = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM',
        'V', 'UNH', 'JNJ', 'WMT', 'PG', 'MA', 'HD', 'CVX', 'MRK', 'ABBV',
        'PEP', 'KO', 'COST', 'AVGO', 'TMO', 'CSCO', 'MCD', 'ACN', 'ABT'
    ]
    
    print_info(f"Scanning {market} - analyzing {len(SAMPLE_TICKERS)} stocks...")
    
    config = ResearchEnhancementConfig(use_advanced_features=False)
    claw = QuantClawProResearch(config)
    
    results = []
    for ticker in SAMPLE_TICKERS:
        try:
            df = yf.download(ticker, period='3mo', progress=False)
            if df.empty:
                continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0].lower().replace(' ', '_') for c in df.columns]
            else:
                df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            
            result = claw.analyze_stock_enhanced(ticker, df)
            cog = result['cognition']
            
            results.append({
                'ticker': ticker,
                'mbti': cog['mbti_type'],
                'name': cog['mbti_name'],
                'risk': cog['risk_level'],
                'confidence': cog['confidence']
            })
            print_success(f"{ticker}: {cog['mbti_type']} ({cog['mbti_name']})")
        except Exception as e:
            print_warning(f"{ticker}: Failed - {str(e)[:50]}")
    
    if results:
        print(f"\n{BOLD}Scan Summary (Top {limit}){RESET}")
        print("-" * 60)
        
        # Group by MBTI
        mbti_groups = {}
        for r in results:
            mbti = r['mbti']
            if mbti not in mbti_groups:
                mbti_groups[mbti] = []
            mbti_groups[mbti].append(r)
        
        for mbti, stocks in sorted(mbti_groups.items()):
            print(f"\n{GREEN}{mbti}{RESET} ({len(stocks)} stocks):")
            for s in stocks[:5]:
                print(f"  {s['ticker']:6} - {s['name']} (Risk: {s['risk']}, Conf: {s['confidence']:.0%})")
        
        print("-" * 60)


def cmd_fetch(max_results: int = 50):
    """Fetch latest papers from arXiv"""
    from research.arxiv_crawler import ArxivPaperCrawler, PaperAnalyzer
    
    print_info(f"Fetching {max_results} papers from arXiv...")
    
    crawler = ArxivPaperCrawler()
    papers = crawler.fetch_recent_papers(max_results=max_results)
    
    if papers:
        print_success(f"Fetched {len(papers)} papers")
        
        print_info("Analyzing papers...")
        analyzer = PaperAnalyzer()
        analyzer.batch_analyze(crawler, limit=min(30, len(papers)))
        
        print_success("Analysis complete!")
    else:
        print_warning("No new papers found")


def cmd_demo():
    """Run demonstration"""
    from quantclaw_research_edition import demo_research_edition
    demo_research_edition()


def main():
    parser = argparse.ArgumentParser(
        description=f'{BOLD}QuantClaw Pro{RESET} - MBTI-Based Quantitative Trading System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  {GREEN}quantclaw analyze AAPL{RESET}          # Analyze single stock
  {GREEN}quantclaw analyze AAPL --full{RESET}   # Full research analysis
  {GREEN}quantclaw portfolio AAPL MSFT GOOGL{RESET}  # Portfolio analysis
  {GREEN}quantclaw scan{RESET}                  # Scan market
  {GREEN}quantclaw fetch{RESET}                # Fetch papers
  {GREEN}quantclaw demo{RESET}                  # Run demo
        """
    )
    
    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('args', nargs='*', help='Arguments for command')
    parser.add_argument('--full', action='store_true', help='Full analysis with research features')
    parser.add_argument('--max-position', type=float, default=0.25, help='Max position size')
    parser.add_argument('--limit', type=int, default=20, help='Limit for scan results')
    parser.add_argument('--max-results', type=int, help='Max papers default=50, to fetch')
    
    args = parser.parse_args()
    
    if not args.command:
        print_header()
        parser.print_help()
        return
    
    try:
        if args.command == 'analyze':
            if not args.args:
                print_error("Ticker required: quantclaw analyze <ticker>")
                return
            cmd_analyze(args.args[0], full=args.full)
            
        elif args.command == 'portfolio':
            if len(args.args) < 2:
                print_error("At least 2 tickers required: quantclaw portfolio <ticker1> <ticker2> ...")
                return
            cmd_portfolio(args.args, max_position=args.max_position)
            
        elif args.command == 'scan':
            cmd_scan(limit=args.limit)
            
        elif args.command == 'fetch':
            cmd_fetch(max_results=args.max_results)
            
        elif args.command == 'demo':
            cmd_demo()
            
        else:
            print_error(f"Unknown command: {args.command}")
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
