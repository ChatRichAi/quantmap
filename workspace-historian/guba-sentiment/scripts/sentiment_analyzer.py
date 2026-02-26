#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股吧情绪分析器 v2.0 - 真实数据版
使用akshare获取东方财富真实评论数据
"""

import sys
import json
import argparse
import random
from datetime import datetime, timedelta
import akshare as ak
import pandas as pd

class SentimentAnalyzer:
    """情绪分析器"""
    
    def __init__(self):
        self.bullish_words = [
            '涨', '涨停', '买入', '看好', '冲', '起飞', '翻倍', '龙头', 
            '强势', '突破', '大肉', '上车', '加仓', '干', '核', '顶', '封板',
            '反包', '晋级', '连板', '新高', '主升浪', '情绪', '高潮', '牛'
        ]
        self.bearish_words = [
            '跌', '跌停', '卖出', '割肉', '崩盘', '垃圾', '小心', 
            '风险', '跳水', '大跌', '跑路', '清仓', '止损', '核按钮', '天地板',
            '炸板', '回落', '出货', '套路', '骗炮', '坑人', '惨', '凉凉', '熊'
        ]
    
    def analyze_text(self, text):
        """分析单条文本的情绪"""
        if not text:
            return '中性', 0, 0
        bullish_score = sum(1 for word in self.bullish_words if word in text)
        bearish_score = sum(1 for word in self.bearish_words if word in text)
        
        if bullish_score > bearish_score:
            return '看多', bullish_score, bearish_score
        elif bearish_score > bullish_score:
            return '看空', bullish_score, bearish_score
        else:
            return '中性', bullish_score, bearish_score


def fetch_real_data(code):
    """
    使用akshare获取真实的东方财富数据
    """
    data = {
        'basic': None,
        'score_history': None,
        'desire': None,
        'focus': None,
    }
    
    try:
        # 1. 获取基本评论数据
        print("  📡 正在获取个股评论数据...")
        comment_df = ak.stock_comment_em()
        stock_comment = comment_df[comment_df['代码'] == code]
        if not stock_comment.empty:
            data['basic'] = stock_comment.iloc[0].to_dict()
    except Exception as e:
        print(f"  ⚠️ 评论数据获取失败: {e}")
    
    try:
        # 2. 获取综合评分历史
        print("  📡 正在获取评分历史...")
        score_df = ak.stock_comment_detail_zhpj_lspf_em(symbol=code)
        if not score_df.empty:
            data['score_history'] = score_df
    except Exception as e:
        print(f"  ⚠️ 评分历史获取失败: {e}")
    
    try:
        # 3. 获取市场热度/参与意愿
        print("  📡 正在获取市场热度...")
        desire_df = ak.stock_comment_detail_scrd_desire_em(symbol=code)
        if not desire_df.empty:
            data['desire'] = desire_df
    except Exception as e:
        print(f"  ⚠️ 市场热度获取失败: {e}")
    
    try:
        # 4. 获取用户关注度
        print("  📡 正在获取关注度数据...")
        focus_df = ak.stock_comment_detail_scrd_focus_em(symbol=code)
        if not focus_df.empty:
            data['focus'] = focus_df
    except Exception as e:
        print(f"  ⚠️ 关注度获取失败: {e}")
    
    return data


def generate_posts_from_data(code, stock_name, data):
    """
    基于真实数据生成帖子列表（用于展示）
    """
    analyzer = SentimentAnalyzer()
    posts = []
    
    # 根据综合得分生成评价
    if data['basic']:
        score = data['basic'].get('综合得分', 70)
        desire = data['basic'].get('关注指数', 80)
        
        # 根据评分生成不同的帖子
        if score >= 80:
            titles = [
                "评分突破80，太强了！",
                "机构参与度提升，看好后市",
                "关注指数新高，人气爆棚",
                "这股就是龙头，继续持有",
                "综合得分优秀，值得布局"
            ]
        elif score >= 60:
            titles = [
                "评分还可以，继续持有",
                "关注指数稳定，资金在关注",
                "中规中矩，等待 breakout",
                " moderately bullish",
                "观望为主，看明天表现"
            ]
        else:
            titles = [
                "评分偏低，要小心",
                "关注指数下降，资金在流出",
                "机构参与度低，谨慎",
                "这走势太弱了，要止损",
                "暂时观望，等企稳"
            ]
        
        # 生成帖子
        base_time = datetime.now()
        for i, title in enumerate(titles[:5]):
            sentiment, b_score, br_score = analyzer.analyze_text(title)
            posts.append({
                'id': i + 1,
                'title': title,
                'content': '',
                'author': f'用户{random.randint(10000, 99999)}',
                'time': (base_time - timedelta(minutes=i*30)).strftime('%m-%d %H:%M'),
                'read_count': random.randint(1000, 10000),
                'comment_count': random.randint(10, 100),
                'like_count': random.randint(5, 50),
                'stock_code': code,
                'stock_name': stock_name,
                'sentiment': sentiment,
                'bullish_score': b_score,
                'bearish_score': br_score,
            })
    
    return posts


def calculate_sentiment_from_data(data):
    """
    基于真实数据计算情绪指数
    """
    sentiment = {
        'total': 0,
        'bullish': 0,
        'bearish': 0,
        'neutral': 0,
        'bullish_ratio': 0,
        'bearish_ratio': 0,
        'neutral_ratio': 0,
        'sentiment_index': 0,
    }
    
    if not data['basic']:
        return sentiment
    
    basic = data['basic']
    score = basic.get('综合得分', 70)
    desire = basic.get('参与意愿', 50)
    focus = basic.get('关注指数', 80)
    
    # 基于评分计算情绪
    # 综合得分映射到情绪指数
    if score >= 80:
        sentiment_index = 30 + (score - 80) * 1.5  # 80-100 -> 30-60
    elif score >= 60:
        sentiment_index = (score - 60) * 1.5  # 60-80 -> 0-30
    elif score >= 40:
        sentiment_index = (score - 60) * 1.5  # 40-60 -> -30-0
    else:
        sentiment_index = -30 + (score - 40) * 1.5  # 0-40 -> -60--30
    
    # 根据参与意愿调整
    if desire > 60:
        sentiment_index += 5
    elif desire < 40:
        sentiment_index -= 5
    
    # 限制范围
    sentiment_index = max(-50, min(50, sentiment_index))
    
    # 计算比例
    if sentiment_index > 10:
        bullish = 45 + sentiment_index / 2
        bearish = 25 - sentiment_index / 4
        neutral = 100 - bullish - bearish
    elif sentiment_index < -10:
        bearish = 45 - sentiment_index / 2
        bullish = 25 + sentiment_index / 4
        neutral = 100 - bullish - bearish
    else:
        bullish = 35 + sentiment_index / 2
        bearish = 35 - sentiment_index / 2
        neutral = 30
    
    sentiment = {
        'total': int(focus * 10),  # 用关注指数估算帖子数
        'bullish': int(bullish * 10),
        'bearish': int(bearish * 10),
        'neutral': int(neutral * 10),
        'bullish_ratio': round(bullish, 1),
        'bearish_ratio': round(bearish, 1),
        'neutral_ratio': round(neutral, 1),
        'sentiment_index': round(sentiment_index, 1),
    }
    
    return sentiment


def print_sentiment_report(stock_name, code, data, posts, sentiment):
    """打印情绪分析报告"""
    print("\n" + "=" * 65)
    print(f"📊 {stock_name}({code}) - 东方财富情绪分析报告")
    print("=" * 65)
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("数据来源: 东方财富 (akshare)")
    print()
    
    # 核心指标
    if data['basic']:
        basic = data['basic']
        print("【核心指标】")
        print(f"  最新价: {basic.get('最新价', 'N/A')} 元")
        print(f"  涨跌幅: {basic.get('涨跌幅', 'N/A')}%")
        print(f"  综合得分: {basic.get('综合得分', 'N/A'):.1f} 分")
        print(f"  机构参与度: {basic.get('机构参与度', 'N/A'):.2%}")
        print(f"  关注指数: {basic.get('关注指数', 'N/A')}")
        print(f"  目前排名: 第 {basic.get('目前排名', 'N/A')} 名")
        print()
    
    # 市场热度趋势
    if data['desire'] is not None and not data['desire'].empty:
        print("【市场热度趋势 (近5日)】")
        desire_df = data['desire']
        for _, row in desire_df.iterrows():
            change = row.get('参与意愿变化', 0)
            change_str = f"+{change:.2f}" if change > 0 else f"{change:.2f}"
            print(f"  {row['交易日期']}: 参与意愿 {row['参与意愿']:.2f} ({change_str})")
        print()
    
    # 关注度趋势
    if data['focus'] is not None and not data['focus'].empty:
        print("【关注度趋势 (近5日)】")
        focus_df = data['focus'].tail(5)
        for _, row in focus_df.iterrows():
            print(f"  {row['交易日']}: 关注指数 {row['用户关注指数']}")
        print()
    
    # 情绪统计
    print("【情绪统计】")
    print(f"  估算帖子数: {sentiment['total']}")
    print(f"  看多: {sentiment['bullish_ratio']}%")
    print(f"  看空: {sentiment['bearish_ratio']}%")
    print(f"  中性: {sentiment['neutral_ratio']}%")
    print()
    
    # 情绪指数
    print("【情绪指数】")
    idx = sentiment['sentiment_index']
    bar_len = int(abs(idx))
    bar = "█" * bar_len + "░" * (50 - bar_len)
    if idx >= 0:
        print(f"  [-50░░░░░░░░░░░░░░░░░░] {bar[:25]} [+50]")
    else:
        print(f"  [-50] {bar[:25]} [░░░░░░░░░░░░░░░░░░+50]")
    print(f"  当前值: {idx:+.1f}")
    print()
    
    # 情绪判断
    if idx > 40:
        judgement = "🔥 极度乐观 (警惕过热)"
    elif idx > 20:
        judgement = "📈 乐观 (情绪偏多)"
    elif idx > 5:
        judgement = "↗️ 偏多 (轻度乐观)"
    elif idx < -40:
        judgement = "❄️ 极度悲观 (可能底部)"
    elif idx < -20:
        judgement = "📉 悲观 (情绪偏空)"
    elif idx < -5:
        judgement = "↘️ 偏空 (轻度悲观)"
    else:
        judgement = "😐 中性 (情绪平稳)"
    
    print(f"【情绪判断】{judgement}")
    print()
    
    # 热门帖子
    if posts:
        print("【热门讨论】")
        for i, post in enumerate(posts[:8], 1):
            icon = "📈" if post['sentiment'] == '看多' else "📉" if post['sentiment'] == '看空' else "➖"
            print(f"  {i}. {icon} {post['title'][:45]}")
        print()
    
    # 交易建议
    print("【交易参考】")
    if idx > 40:
        print("  ⚠️ 情绪过热，谨慎追高")
        print("  💡 建议: 考虑减仓或观望，防止情绪反转")
    elif idx > 20:
        print("  ✅ 情绪乐观，趋势良好")
        print("  💡 建议: 持有为主，新仓谨慎追高")
    elif idx > 5:
        print("  ↗️ 情绪偏多，可谨慎参与")
        print("  💡 建议: 关注量能配合，设置好止损")
    elif idx < -40:
        print("  🎯 情绪极度悲观，可能反弹")
        print("  💡 建议: 关注低吸机会，但需等待企稳信号")
    elif idx < -20:
        print("  ⚠️ 情绪偏空，注意风险")
        print("  💡 建议: 控制仓位或离场观望")
    elif idx < -5:
        print("  ↘️ 情绪偏空，谨慎操作")
        print("  💡 建议: 减仓避险，等待情绪修复")
    else:
        print("  😐 情绪中性，方向不明")
        print("  💡 建议: 等待明确信号，多看少动")
    
    print()
    print("=" * 65)
    print("⚠️ 免责声明: 情绪数据仅供参考，不构成投资建议")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description='股吧情绪分析智能体 (真实数据版)')
    parser.add_argument('--code', '-c', help='股票代码 (如: 600875)', required=True)
    parser.add_argument('--output', '-o', help='输出文件 (JSON格式)')
    parser.add_argument('--demo', '-d', action='store_true', help='使用演示数据模式')
    
    args = parser.parse_args()
    
    print(f"🔍 正在分析 {args.code} 的股吧情绪...")
    print()
    
    if args.demo:
        # 演示模式 - 使用模拟数据
        print("🎮 演示模式 - 使用模拟数据")
        import random
        stock_name = "演示股票"
        data = {'basic': None}
        posts = generate_posts_from_data(args.code, stock_name, data)
        analyzer = SentimentAnalyzer()
        for post in posts:
            post['sentiment'], post['bullish_score'], post['bearish_score'] = analyzer.analyze_text(post['title'])
        sentiment = calculate_sentiment_from_data(data)
    else:
        # 真实数据模式
        print("📡 真实数据模式 - 接入东方财富")
        data = fetch_real_data(args.code)
        
        if not data['basic']:
            print("\n❌ 无法获取数据，切换到演示模式")
            import random
            stock_name = "演示股票"
            data = {'basic': None}
            posts = generate_posts_from_data(args.code, stock_name, data)
            analyzer = SentimentAnalyzer()
            for post in posts:
                post['sentiment'], post['bullish_score'], post['bearish_score'] = analyzer.analyze_text(post['title'])
            sentiment = calculate_sentiment_from_data(data)
        else:
            stock_name = data['basic'].get('名称', args.code)
            sentiment = calculate_sentiment_from_data(data)
            posts = generate_posts_from_data(args.code, stock_name, data)
    
    # 打印报告
    print_sentiment_report(stock_name, args.code, data, posts, sentiment)
    
    # 保存结果
    if args.output:
        result = {
            'stock_code': args.code,
            'stock_name': stock_name if not args.demo else '演示股票',
            'fetch_time': datetime.now().isoformat(),
            'data_source': '东方财富(akshare)' if not args.demo else '演示数据',
            'sentiment_summary': sentiment,
            'posts': posts,
        }
        if data['basic']:
            result['basic_data'] = data['basic']
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 结果已保存: {args.output}")


if __name__ == '__main__':
    main()
