#!/usr/bin/env python3
"""
股票狙击手 - 完整分析工作流
整合所有数据源，执行完整的分析流程
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import subprocess

# 添加脚本目录
sys.path.insert(0, str(Path(__file__).parent))

# 修复版: 使用直接请求API的版本 (akshare连接问题)
from market_scanner_fixed import scan_market_anomalies, get_fund_flow, get_stock_basic_info
# from market_scanner import scan_market_anomalies, get_fund_flow, get_stock_basic_info
from news_fetcher import NewsFetcher
from guba_sentiment import GubaSentimentAnalyzer
from tv_chart_capture import get_tv_analysis_summary, capture_tv_screenshots_guide
from technical_analyzer import TechnicalAnalyzer
from report_generator import generate_markdown_report, generate_html_report

class StockSniper:
    """股票狙击手主控类"""
    
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent.parent / 'output'
        self.output_dir.mkdir(exist_ok=True)
        
        self.news_fetcher = NewsFetcher()
        self.sentiment_analyzer = GubaSentimentAnalyzer()
        self.tech_analyzer = TechnicalAnalyzer()
    
    def analyze_stock(self, stock_code, stock_name=None, include_tv=False):
        """
        分析单只股票
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称（可选）
            include_tv: 是否包含TradingView分析
        
        Returns:
            dict: 分析结果和报告路径
        """
        print(f"\n{'='*60}")
        print(f"🎯 股票狙击手 - 分析 {stock_code} {stock_name or ''}")
        print(f"{'='*60}\n")
        
        # 1. 获取基础数据
        print("📊 [1/6] 获取基础数据...")
        if not stock_name:
            basic_info = get_stock_basic_info(stock_code)
            stock_name = basic_info.get('股票简称', stock_code)
        
        stock_data = {
            'code': stock_code,
            'name': stock_name,
            'type': '手动分析'
        }
        
        fund_flow = get_fund_flow(stock_code)
        print(f"  ✓ 资金流向: 主力净流入 {fund_flow.get('main_inflow', 'N/A')} 万元")
        
        # 2. 获取新闻热点
        print("\n📰 [2/6] 获取新闻热点...")
        news_data = self.news_fetcher.fetch_all_news(stock_code=stock_code, limit=15)
        print(f"  ✓ 获取到 {len(news_data)} 条相关新闻")
        
        # 分析关联题材
        themes = self.news_fetcher.analyze_theme_from_news(news_data)
        top_themes = [(k, v) for k, v in themes.items() if v > 0][:3]
        if top_themes:
            print(f"  ✓ 关联题材: {', '.join([f'{t[0]}({t[1]})' for t in top_themes])}")
        
        # 3. 获取股吧舆情
        print("\n💬 [3/6] 获取股吧舆情...")
        sentiment = self.sentiment_analyzer.analyze_sentiment(stock_code, limit=30)
        print(f"  ✓ 舆情分析: {sentiment['overall']} ({sentiment['sentiment_score']}/10)")
        print(f"  ✓ 看多: {sentiment['bullish_ratio']}% | 看空: {sentiment['bearish_ratio']}%")
        
        # 4. 获取TradingView数据
        print("\n📈 [4/6] 准备TradingView分析...")
        tv_summary = get_tv_analysis_summary(stock_code, stock_name)
        tv_data = {
            '5m': {'trend': '待TradingView截图分析', 'support': [], 'resistance': []},
            '15m': {'trend': '待TradingView截图分析', 'support': [], 'resistance': []},
            '1h': {'trend': '待TradingView截图分析', 'support': [], 'resistance': []},
            'key_levels': {'strong_support': None, 'strong_resistance': None}
        }
        
        if include_tv:
            print("  ⚠️ TradingView 分析需要手动截图")
            guide = capture_tv_screenshots_guide(stock_code, stock_name)
            tv_guide_path = self.output_dir / f"{stock_code}_TV截图指南.txt"
            tv_guide_path.write_text(guide, encoding='utf-8')
            print(f"  ✓ TV截图指南已保存: {tv_guide_path}")
        
        # 5. 执行技术分析
        print("\n⚡ [5/6] 执行技术分析...")
        analysis_result = self.tech_analyzer.analyze(
            stock_data=stock_data,
            tv_data=tv_data,
            fund_flow=fund_flow,
            news_data=news_data,
            sentiment=sentiment
        )
        
        # 添加新闻和舆情分析
        analysis_result['theme_analysis'] = self._format_theme_analysis(themes, news_data)
        analysis_result['sentiment_analysis'] = self._format_sentiment_analysis(sentiment)
        
        print(f"  ✓ 综合评分: {analysis_result['total_score']}/10")
        print(f"  ✓ 操作建议: {analysis_result['action_rating']}")
        
        # 6. 生成报告
        print("\n📝 [6/6] 生成分析报告...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        md_path = self.output_dir / f"{stock_code}_{stock_name}_{timestamp}_分析报告.md"
        html_path = self.output_dir / f"{stock_code}_{stock_name}_{timestamp}_分析报告.html"
        
        generate_markdown_report(stock_data, analysis_result, str(md_path))
        generate_html_report(stock_data, analysis_result, str(html_path))
        
        print(f"  ✓ Markdown报告: {md_path}")
        print(f"  ✓ HTML报告: {html_path}")
        
        # 保存原始数据
        data_path = self.output_dir / f"{stock_code}_{stock_name}_{timestamp}_raw_data.json"
        raw_data = {
            'stock_data': stock_data,
            'fund_flow': fund_flow,
            'news_data': news_data,
            'sentiment': sentiment,
            'analysis_result': analysis_result,
            'timestamp': datetime.now().isoformat()
        }
        data_path.write_text(json.dumps(raw_data, ensure_ascii=False, indent=2), encoding='utf-8')
        
        print(f"\n{'='*60}")
        print(f"✅ 分析完成! 综合评分: {analysis_result['total_score']}/10")
        print(f"{'='*60}\n")
        
        return {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'score': analysis_result['total_score'],
            'rating': analysis_result['action_rating'],
            'md_report': str(md_path),
            'html_report': str(html_path),
            'raw_data': str(data_path)
        }
    
    def scan_and_analyze(self, top_n=5, min_score=5.0):
        """
        扫描市场异动并分析
        
        Args:
            top_n: 分析前N只股票
            min_score: 最低评分阈值
        """
        print(f"\n{'='*60}")
        print(f"🎯 股票狙击手 - 市场异动扫描")
        print(f"{'='*60}\n")
        
        # 扫描市场
        print("🔍 扫描市场异动...")
        anomalies = scan_market_anomalies()
        print(f"✓ 发现 {len(anomalies)} 只异动股票\n")
        
        # 分析前N只
        results = []
        for i, stock in enumerate(anomalies[:top_n], 1):
            print(f"\n📌 分析第 {i}/{top_n} 只: {stock['name']} ({stock['code']})")
            try:
                result = self.analyze_stock(stock['code'], stock['name'])
                results.append(result)
            except Exception as e:
                print(f"❌ 分析失败: {e}")
        
        # 生成汇总报告
        self._generate_summary_report(results)
        
        return results
    
    def _format_theme_analysis(self, themes, news_data):
        """格式化题材分析"""
        lines = []
        top_themes = [(k, v) for k, v in themes.items() if v > 0][:5]
        
        if top_themes:
            lines.append("**关联题材排名:**")
            for theme, count in top_themes:
                lines.append(f"- {theme}: {count} 条相关新闻")
        
        # 添加最新新闻标题
        if news_data:
            lines.append("\n**最新相关新闻:**")
            for news in news_data[:3]:
                sentiment = news.get('sentiment', 'neutral')
                emoji = {'positive': '🟢', 'negative': '🔴', 'neutral': '⚪'}.get(sentiment, '⚪')
                lines.append(f"- {emoji} {news.get('title', '')}")
        
        return '\n'.join(lines) if lines else "暂无相关题材"
    
    def _format_sentiment_analysis(self, sentiment):
        """格式化舆情分析"""
        lines = [
            f"**整体情绪**: {sentiment['overall']} (得分: {sentiment['sentiment_score']}/10)",
            f"**帖子统计**: 看多 {sentiment['bullish_ratio']}% | 看空 {sentiment['bearish_ratio']}% | 中性 {100 - sentiment['bullish_ratio'] - sentiment['bearish_ratio']:.1f}%",
        ]
        
        if sentiment.get('hot_keywords'):
            lines.append(f"**热门关键词**: {', '.join(sentiment['hot_keywords'][:5])}")
        
        if sentiment.get('sample_posts'):
            lines.append("\n**热门帖子:**")
            for post in sentiment['sample_posts'][:3]:
                emoji = {'bullish': '🟢', 'bearish': '🔴', 'neutral': '⚪'}.get(post['sentiment'], '⚪')
                lines.append(f"- {emoji} {post['title'][:40]}...")
        
        return '\n'.join(lines)
    
    def _generate_summary_report(self, results):
        """生成汇总报告"""
        if not results:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_path = self.output_dir / f"汇总报告_{timestamp}.md"
        
        lines = [
            f"# 📊 股票狙击手 - 市场扫描汇总报告",
            f"",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 分析结果汇总",
            f"",
            f"| 排名 | 股票 | 代码 | 评分 | 建议 | 报告 |",
            f"|------|------|------|------|------|------|",
        ]
        
        for i, r in enumerate(results, 1):
            emoji = "🟢" if r['score'] >= 7 else "🟡" if r['score'] >= 5 else "🔴"
            lines.append(f"| {i} | {r['stock_name']} | {r['stock_code']} | {emoji} {r['score']}/10 | {r['rating']} | [查看]({r['html_report']}) |")
        
        lines.extend([
            f"",
            f"## 详细说明",
            f"",
            f"- 🟢 **高分股票** (≥7分): 建议重点关注，可能具备较好的交易机会",
            f"- 🟡 **中等股票** (5-7分): 可适度关注，需结合其他因素判断",
            f"- 🔴 **低分股票** (<5分): 建议回避或保持观望",
            f"",
            f"---",
            f"*报告生成 by 股票狙击手*",
        ])
        
        summary_path.write_text('\n'.join(lines), encoding='utf-8')
        print(f"\n✅ 汇总报告已生成: {summary_path}")

def main():
    parser = argparse.ArgumentParser(description='股票狙击手 - A股超短线智能分析系统')
    parser.add_argument('--code', '-c', help='指定股票代码')
    parser.add_argument('--name', '-n', help='股票名称')
    parser.add_argument('--scan', '-s', action='store_true', help='扫描市场异动')
    parser.add_argument('--top', '-t', type=int, default=5, help='扫描时分析前N只股票')
    parser.add_argument('--tv', action='store_true', help='包含TradingView分析')
    parser.add_argument('--output', '-o', help='输出目录')
    
    args = parser.parse_args()
    
    sniper = StockSniper(output_dir=args.output)
    
    if args.code:
        result = sniper.analyze_stock(args.code, args.name, include_tv=args.tv)
        print(f"\n分析结果:")
        print(f"  股票: {result['stock_name']} ({result['stock_code']})")
        print(f"  评分: {result['score']}/10")
        print(f"  建议: {result['rating']}")
        print(f"  报告: {result['html_report']}")
    elif args.scan:
        results = sniper.scan_and_analyze(top_n=args.top)
    else:
        print("使用方式:")
        print("  python stock_sniper.py --code 000001 --name 平安银行  # 分析指定股票")
        print("  python stock_sniper.py --scan                        # 扫描市场异动")
        print("  python stock_sniper.py --scan --top 10               # 扫描前10只")
        print("  python stock_sniper.py --code 000001 --tv            # 包含TV分析")
        sys.exit(1)

if __name__ == "__main__":
    main()
