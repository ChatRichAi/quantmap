#!/usr/bin/env python3
"""
多源数据整合器 - 整合 akshare、TradingView、新闻、舆情数据
"""

import json
import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from market_scanner import scan_market_anomalies, get_fund_flow
from tv_chart_capture import get_tv_analysis_summary
from technical_analyzer import TechnicalAnalyzer
from report_generator import generate_markdown_report, generate_html_report

def integrate_data(stock_code=None, stock_name=None, auto_scan=False):
    """
    整合多源数据并生成分析报告
    
    Args:
        stock_code: 指定股票代码（可选）
        stock_name: 股票名称（可选）
        auto_scan: 是否自动扫描市场异动
    
    Returns:
        dict: 包含报告路径和分析结果
    """
    
    results = []
    
    if auto_scan or stock_code is None:
        # 自动扫描市场异动
        print("🔍 启动市场异动扫描...")
        anomalies = scan_market_anomalies()
        target_stocks = anomalies[:5]  # 分析前5只
    else:
        # 指定股票
        target_stocks = [{
            'code': stock_code,
            'name': stock_name or stock_code,
            'type': '手动分析'
        }]
    
    analyzer = TechnicalAnalyzer()
    
    for stock in target_stocks:
        code = stock['code']
        name = stock['name']
        
        print(f"\n📊 正在分析: {name} ({code})")
        print("-" * 40)
        
        # 1. 获取基础数据
        print("  → 获取 akshare 数据...")
        fund_flow = get_fund_flow(code)
        
        # 2. 获取 TV 数据模板
        print("  → 准备 TradingView 分析...")
        tv_summary = get_tv_analysis_summary(code, name)
        tv_data = {
            '5m': {'trend': '待TradingView截图分析'},
            '15m': {'trend': '待TradingView截图分析'},
            '1h': {'trend': '待TradingView截图分析'},
            'key_levels': {'strong_support': None, 'strong_resistance': None}
        }
        
        # 3. 获取新闻数据（通过AI agent调用web_search）
        print("  → 新闻数据待获取...")
        news_data = []  # 实际使用时通过AI agent获取
        
        # 4. 获取舆情数据
        print("  → 舆情数据待获取...")
        sentiment = {}
        
        # 5. 执行技术分析
        print("  → 执行综合技术分析...")
        analysis_result = analyzer.analyze(
            stock_data=stock,
            tv_data=tv_data,
            fund_flow=fund_flow,
            news_data=news_data,
            sentiment=sentiment
        )
        
        # 6. 生成报告
        timestamp = Path(__file__).parent.parent.parent / 'output'
        timestamp.mkdir(exist_ok=True)
        
        md_path = timestamp / f"{code}_{name}_分析报告.md"
        html_path = timestamp / f"{code}_{name}_分析报告.html"
        
        print(f"  → 生成 Markdown 报告...")
        md_report = generate_markdown_report(stock, analysis_result, str(md_path))
        
        print(f"  → 生成 HTML 报告...")
        html_report = generate_html_report(stock, analysis_result, str(html_path))
        
        results.append({
            'code': code,
            'name': name,
            'score': analysis_result['total_score'],
            'rating': analysis_result['action_rating'],
            'md_report': str(md_path),
            'html_report': str(html_path)
        })
        
        print(f"  ✅ 分析完成: {name} - 评分 {analysis_result['total_score']}/10 - 建议: {analysis_result['action_rating']}")
    
    return results

def print_summary(results):
    """打印分析摘要"""
    print("\n" + "=" * 60)
    print("📈 股票狙击手 - 分析完成摘要")
    print("=" * 60)
    
    for r in results:
        emoji = "🟢" if r['score'] >= 7 else "🟡" if r['score'] >= 5 else "🔴"
        print(f"{emoji} {r['name']} ({r['code']})")
        print(f"   评分: {r['score']}/10 | 建议: {r['rating']}")
        print(f"   报告: {r['md_report']}")
        print()
    
    print("=" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='股票狙击手 - 多源数据整合分析')
    parser.add_argument('--code', '-c', help='指定股票代码')
    parser.add_argument('--name', '-n', help='股票名称')
    parser.add_argument('--scan', '-s', action='store_true', help='自动扫描市场异动')
    
    args = parser.parse_args()
    
    if args.code:
        results = integrate_data(stock_code=args.code, stock_name=args.name)
    elif args.scan:
        results = integrate_data(auto_scan=True)
    else:
        print("使用方式:")
        print("  python data_fusion.py --code 000001 --name 平安银行  # 分析指定股票")
        print("  python data_fusion.py --scan                        # 扫描市场异动")
        sys.exit(1)
    
    print_summary(results)
