#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雪球网 (xueqiu.com) 情绪数据接口
高质量投资者社区，适合获取专业投资者观点
"""

import requests
import json
import time
from datetime import datetime
from urllib.parse import quote

class XueqiuAPI:
    """雪球API接口"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://xueqiu.com/',
        })
        self._init_cookies()
    
    def _init_cookies(self):
        """初始化cookies - 雪球需要cookie才能访问API"""
        try:
            self.session.get('https://xueqiu.com/', timeout=10)
            time.sleep(0.5)
        except:
            pass
    
    def get_stock_info(self, symbol):
        """
        获取股票基本信息
        :param symbol: SH600875 或 SZ000001
        """
        url = f'https://stock.xueqiu.com/v5/stock/app/stock/{symbol}/detail.json'
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except Exception as e:
            print(f"获取股票信息失败: {e}")
            return None
    
    def get_stock_articles(self, symbol, count=20):
        """
        获取股票相关文章/讨论
        :param symbol: SH600875
        :param count: 数量
        """
        url = 'https://xueqiu.com/query/v1/search.json'
        params = {
            'q': symbol,
            'count': str(count),
            'sort': 'time',
        }
        
        try:
            r = self.session.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('success'):
                    return data.get('list', [])
            return []
        except Exception as e:
            print(f"获取文章失败: {e}")
            return []
    
    def get_stock_timeline(self, symbol, count=20):
        """
        获取股票时间线动态
        """
        url = 'https://xueqiu.com/statuses/search.json'
        params = {
            'symbol': symbol,
            'count': str(count),
            'page': '1',
            'comment': '0',
        }
        
        try:
            r = self.session.get(url, params=params, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except Exception as e:
            print(f"获取时间线失败: {e}")
            return None
    
    def get_hot_stocks(self):
        """
        获取热门股票
        """
        url = 'https://stock.xueqiu.com/v5/stock/hot_stock/list.json'
        try:
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
            return None
        except Exception as e:
            print(f"获取热门股票失败: {e}")
            return None


def convert_code_to_symbol(code):
    """
    将股票代码转换为雪球格式
    600875 -> SH600875
    000001 -> SZ000001
    """
    code = str(code).strip()
    if code.startswith('6'):
        return f'SH{code}'
    elif code.startswith(('0', '3')):
        return f'SZ{code}'
    elif code.startswith(('8', '4')):
        return f'BJ{code}'
    return code


def analyze_xueqiu_sentiment(code, use_demo=False):
    """
    分析雪球情绪
    :param code: 股票代码
    :param use_demo: 使用演示数据
    :return: 情绪数据字典
    """
    print(f"\n📊 雪球网情绪分析: {code}")
    print("-" * 50)
    
    if use_demo:
        # 演示模式
        return generate_xueqiu_demo_data(code)
    
    # 真实数据模式
    api = XueqiuAPI()
    symbol = convert_code_to_symbol(code)
    
    result = {
        'platform': '雪球',
        'code': code,
        'symbol': symbol,
        'fetch_time': datetime.now().isoformat(),
        'data': {},
        'sentiment': {},
    }
    
    # 获取数据
    print("  🔄 正在获取数据...")
    
    # 1. 股票信息
    stock_info = api.get_stock_info(symbol)
    if stock_info:
        result['data']['stock_info'] = stock_info
        print("  ✅ 股票信息获取成功")
    else:
        print("  ⚠️ 股票信息获取失败，切换到演示模式")
        return generate_xueqiu_demo_data(code)
    
    # 2. 相关文章
    articles = api.get_stock_articles(symbol, count=10)
    if articles:
        result['data']['articles'] = articles
        print(f"  ✅ 获取到 {len(articles)} 篇文章")
    else:
        print("  ⚠️ 文章获取失败")
    
    # 3. 计算情绪
    sentiment = calculate_xueqiu_sentiment(result['data'])
    result['sentiment'] = sentiment
    
    return result


def calculate_xueqiu_sentiment(data):
    """
    基于雪球数据计算情绪
    """
    # 基础情绪值
    base_score = 50  # 中性
    
    # 根据文章分析
    articles = data.get('articles', [])
    if articles:
        bullish = sum(1 for a in articles if any(w in a.get('title', '') for w in ['涨', '突破', '看好']))
        bearish = sum(1 for a in articles if any(w in a.get('title', '') for w in ['跌', '风险', '谨慎']))
        total = len(articles)
        
        if total > 0:
            sentiment_index = (bullish - bearish) / total * 50
        else:
            sentiment_index = 0
    else:
        sentiment_index = 0
    
    final_index = base_score + sentiment_index - 50  # 映射到-50到+50
    final_index = max(-50, min(50, final_index))
    
    return {
        'index': round(final_index, 1),
        'articles_count': len(articles),
        'sentiment_label': get_sentiment_label(final_index),
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


def generate_xueqiu_demo_data(code):
    """生成雪球演示数据"""
    import random
    
    sentiments = ['看多', '看空', '中性']
    titles = [
        '东方电气基本面分析：核电业务迎来新机遇',
        '短期涨幅过大，注意回调风险',
        '从技术面看，突破前期高点',
        '机构调研频繁，值得关注',
        '电力设备龙头，长期看好',
        '估值偏高，建议谨慎',
        '新能源政策利好，业绩有望爆发',
        '短期震荡整理，等待方向',
    ]
    
    articles = []
    for i in range(8):
        title = random.choice(titles)
        sentiment = '看多' if any(w in title for w in ['机遇', '突破', '看好', '利好', '爆发']) else \
                   '看空' if any(w in title for w in ['风险', '回调', '谨慎', '偏高']) else '中性'
        
        articles.append({
            'title': title,
            'author': f'大V_{random.randint(1000, 9999)}',
            'time': (datetime.now() - timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M'),
            'view_count': random.randint(1000, 50000),
            'like_count': random.randint(10, 500),
            'sentiment': sentiment,
        })
    
    bullish = sum(1 for a in articles if a['sentiment'] == '看多')
    bearish = sum(1 for a in articles if a['sentiment'] == '看空')
    neutral = len(articles) - bullish - bearish
    
    sentiment_index = (bullish - bearish) / len(articles) * 30
    
    return {
        'platform': '雪球',
        'code': code,
        'symbol': convert_code_to_symbol(code),
        'fetch_time': datetime.now().isoformat(),
        'data': {
            'articles': articles,
            'note': '演示数据模式',
        },
        'sentiment': {
            'index': round(sentiment_index, 1),
            'articles_count': len(articles),
            'bullish': bullish,
            'bearish': bearish,
            'neutral': neutral,
            'sentiment_label': get_sentiment_label(sentiment_index),
        },
    }


from datetime import timedelta


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='雪球情绪分析')
    parser.add_argument('--code', '-c', default='600875', help='股票代码')
    parser.add_argument('--demo', '-d', action='store_true', help='使用演示数据')
    
    args = parser.parse_args()
    
    result = analyze_xueqiu_sentiment(args.code, use_demo=args.demo)
    
    print("\n" + "=" * 50)
    print(f"📊 雪球情绪分析结果: {args.code}")
    print("=" * 50)
    print(f"情绪指数: {result['sentiment']['index']:+.1f}")
    print(f"情绪判断: {result['sentiment']['sentiment_label']}")
    print(f"文章数量: {result['sentiment']['articles_count']}")
    
    if 'articles' in result['data']:
        print("\n热门文章:")
        for i, article in enumerate(result['data']['articles'][:5], 1):
            icon = '📈' if article.get('sentiment') == '看多' else '📉' if article.get('sentiment') == '看空' else '➖'
            print(f"  {i}. {icon} {article['title'][:40]}")
