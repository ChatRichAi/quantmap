#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
淘股吧 (taoguba.com.cn) 情绪数据接口
短线交易者聚集地，适合获取超短交易者的观点和情绪
"""

import requests
import json
import re
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

class TaogubaAPI:
    """淘股吧API接口"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        })
    
    def get_stock_posts(self, code, page=1):
        """
        获取个股帖子
        淘股吧URL格式: https://www.taoguba.com.cn/stock/600875
        """
        url = f'https://www.taoguba.com.cn/stock/{code}'
        
        try:
            r = self.session.get(url, timeout=15)
            if r.status_code != 200:
                print(f"请求失败: {r.status_code}")
                return []
            
            # 淘股吧有反爬，可能需要特殊处理
            # 这里返回空列表，实际使用时需要实现更复杂的爬取逻辑
            return []
            
        except Exception as e:
            print(f"获取帖子失败: {e}")
            return []
    
    def get_hot_posts(self, page=1):
        """
        获取热门帖子
        """
        url = f'https://www.taoguba.com.cn/hotPost/{page}'
        
        try:
            r = self.session.get(url, timeout=15)
            if r.status_code != 200:
                return []
            
            return []
        except Exception as e:
            print(f"获取热门失败: {e}")
            return []
    
    def search_posts(self, keyword, page=1):
        """
        搜索帖子
        """
        url = 'https://www.taoguba.com.cn/search'
        params = {
            'key': keyword,
            'page': str(page),
        }
        
        try:
            r = self.session.get(url, params=params, timeout=15)
            if r.status_code != 200:
                return []
            
            return []
        except Exception as e:
            print(f"搜索失败: {e}")
            return []


def analyze_taoguba_sentiment(code, use_demo=False):
    """
    分析淘股吧情绪
    :param code: 股票代码
    :param use_demo: 使用演示数据
    :return: 情绪数据字典
    """
    print(f"\n📊 淘股吧情绪分析: {code}")
    print("-" * 50)
    
    if use_demo:
        return generate_taoguba_demo_data(code)
    
    # 尝试获取真实数据
    api = TaogubaAPI()
    posts = api.get_stock_posts(code)
    
    if posts:
        # 成功获取数据
        result = {
            'platform': '淘股吧',
            'code': code,
            'fetch_time': datetime.now().isoformat(),
            'data': {'posts': posts},
            'sentiment': calculate_taoguba_sentiment(posts),
        }
        return result
    else:
        # 获取失败，切换到演示模式
        print("  ⚠️ 无法获取淘股吧数据，切换到演示模式")
        print("  💡 提示: 淘股吧有反爬机制，需要额外的爬虫配置")
        return generate_taoguba_demo_data(code)


def calculate_taoguba_sentiment(posts):
    """
    基于淘股吧帖子计算情绪
    淘股吧用户更关注涨停、连板等超短指标
    """
    bullish_words = ['涨停', '连板', '龙头', '妖股', '打板', '接力', '晋级', '封板', '吃肉', '梭哈', '满仓']
    bearish_words = ['炸板', '天地板', '核按钮', '跌停', '割肉', '跑路', '崩盘', '完了', '凉凉']
    
    bullish = 0
    bearish = 0
    neutral = 0
    
    for post in posts:
        text = f"{post.get('title', '')} {post.get('content', '')}"
        
        b_score = sum(1 for w in bullish_words if w in text)
        br_score = sum(1 for w in bearish_words if w in text)
        
        if b_score > br_score:
            bullish += 1
        elif br_score > b_score:
            bearish += 1
        else:
            neutral += 1
    
    total = len(posts) if posts else 1
    sentiment_index = (bullish - bearish) / total * 50
    sentiment_index = max(-50, min(50, sentiment_index))
    
    return {
        'index': round(sentiment_index, 1),
        'posts_count': len(posts),
        'bullish': bullish,
        'bearish': bearish,
        'neutral': neutral,
        'sentiment_label': get_sentiment_label(sentiment_index),
    }


def get_sentiment_label(index):
    """获取情绪标签"""
    if index > 40: return '极度乐观'
    if index > 20: return '乐观'
    if index > 5: return '偏多'
    if index < -40: return '极度悲观'
    if index < -20: return '悲观'
    if index < -5: return '偏空'
    return '中性'


def generate_taoguba_demo_data(code):
    """生成淘股吧演示数据"""
    import random
    
    # 淘股吧风格的帖子标题
    titles_bullish = [
        '东方电气今日涨停，明天继续冲！',
        '这股是电力龙头，持有到翻倍',
        '打板成功，明天有肉吃',
        '机构大买，游资接力，走妖了',
        '核电概念爆发，东电是龙头',
        '今天板上加仓，明天躺赢',
        '突破新高，主升浪开启',
        '大资金进场，要搞事情',
    ]
    
    titles_bearish = [
        '尾盘炸板，明天要小心',
        '今天追高的明天要割肉了',
        '核按钮预警，注意风险',
        '这位置太高了，不敢上',
        '散户太多，主力要出货',
        '涨停放巨量，明天低开',
        '感觉要天地板，先撤了',
        '这票太套路了，不玩了',
    ]
    
    titles_neutral = [
        '东方电气明天怎么看？',
        '今天这个板封得如何？',
        '有老师分析下吗',
        '成本多少，还能拿吗',
        '明天开盘预期讨论',
        '这股基本面怎么样',
        '电力板块还能炒多久',
    ]
    
    posts = []
    base_time = datetime.now()
    
    # 生成看多帖子
    for i in range(4):
        posts.append({
            'title': random.choice(titles_bullish),
            'author': f'短线王{random.randint(100, 999)}',
            'time': (base_time - timedelta(minutes=random.randint(10, 300))).strftime('%H:%M'),
            'view_count': random.randint(1000, 20000),
            'reply_count': random.randint(5, 100),
            'sentiment': '看多',
        })
    
    # 生成看空帖子
    for i in range(3):
        posts.append({
            'title': random.choice(titles_bearish),
            'author': f'超短选手{random.randint(100, 999)}',
            'time': (base_time - timedelta(minutes=random.randint(10, 300))).strftime('%H:%M'),
            'view_count': random.randint(800, 15000),
            'reply_count': random.randint(3, 80),
            'sentiment': '看空',
        })
    
    # 生成中性帖子
    for i in range(3):
        posts.append({
            'title': random.choice(titles_neutral),
            'author': f'新手{random.randint(100, 999)}',
            'time': (base_time - timedelta(minutes=random.randint(10, 300))).strftime('%H:%M'),
            'view_count': random.randint(500, 10000),
            'reply_count': random.randint(2, 50),
            'sentiment': '中性',
        })
    
    # 随机打乱
    random.shuffle(posts)
    
    # 计算情绪
    bullish = sum(1 for p in posts if p['sentiment'] == '看多')
    bearish = sum(1 for p in posts if p['sentiment'] == '看空')
    neutral = len(posts) - bullish - bearish
    
    sentiment_index = (bullish - bearish) / len(posts) * 35  # 淘股吧情绪波动更大
    
    return {
        'platform': '淘股吧',
        'code': code,
        'fetch_time': datetime.now().isoformat(),
        'data': {
            'posts': posts,
            'note': '演示数据模式（淘股吧需要额外配置爬取）',
        },
        'sentiment': {
            'index': round(sentiment_index, 1),
            'posts_count': len(posts),
            'bullish': bullish,
            'bearish': bearish,
            'neutral': neutral,
            'sentiment_label': get_sentiment_label(sentiment_index),
        },
    }


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='淘股吧情绪分析')
    parser.add_argument('--code', '-c', default='600875', help='股票代码')
    parser.add_argument('--demo', '-d', action='store_true', help='使用演示数据')
    
    args = parser.parse_args()
    
    result = analyze_taoguba_sentiment(args.code, use_demo=args.demo)
    
    print("\n" + "=" * 50)
    print(f"📊 淘股吧情绪分析结果: {args.code}")
    print("=" * 50)
    print(f"情绪指数: {result['sentiment']['index']:+.1f}")
    print(f"情绪判断: {result['sentiment']['sentiment_label']}")
    print(f"帖子数量: {result['sentiment']['posts_count']}")
    print(f"看多: {result['sentiment']['bullish']} | 看空: {result['sentiment']['bearish']} | 中性: {result['sentiment']['neutral']}")
    
    if 'posts' in result['data']:
        print("\n热门帖子:")
        for i, post in enumerate(result['data']['posts'][:5], 1):
            icon = '📈' if post.get('sentiment') == '看多' else '📉' if post.get('sentiment') == '看空' else '➖'
            print(f"  {i}. {icon} {post['title'][:40]}")
