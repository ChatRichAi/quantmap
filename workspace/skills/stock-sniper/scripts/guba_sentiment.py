#!/usr/bin/env python3
"""
股吧舆情获取器 - 获取东方财富股吧情绪数据
"""

import json
import re
import ssl
import urllib.request
from datetime import datetime
from urllib.parse import quote

ssl._create_default_https_context = ssl._create_unverified_context

class GubaSentimentAnalyzer:
    """股吧舆情分析器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Referer': 'https://guba.eastmoney.com/',
        }
    
    def fetch_guba_posts(self, stock_code, limit=50):
        """
        获取股吧帖子
        
        Args:
            stock_code: 股票代码
            limit: 获取帖子数量
        
        Returns:
            list: 帖子列表
        """
        posts = []
        
        try:
            # 东方财富股吧接口
            # code 格式: 0开头或3开头用 0.code，6开头用 1.code
            if stock_code.startswith('6'):
                secid = f"1.{stock_code}"
            else:
                secid = f"0.{stock_code}"
            
            # 股吧API
            url = f"https://guba.eastmoney.com/api/taobaolst?type=1&code={stock_code}&page=1"
            
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                posts = self._parse_guba_html(html, limit)
        except Exception as e:
            print(f"⚠️ 获取股吧数据失败: {e}")
        
        return posts
    
    def _parse_guba_html(self, html, limit):
        """解析股吧HTML"""
        posts = []
        
        try:
            # 简单的正则提取（实际需要更精确的解析）
            # 提取帖子标题和内容
            title_pattern = r'class="l3.*?">\s*<a[^>]*>(.*?)</a>'
            titles = re.findall(title_pattern, html, re.DOTALL)
            
            for title in titles[:limit]:
                # 清理HTML标签
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                if clean_title:
                    posts.append({
                        'title': clean_title,
                        'sentiment': self._analyze_post_sentiment(clean_title)
                    })
        except Exception as e:
            print(f"⚠️ 解析股吧数据失败: {e}")
        
        return posts
    
    def _analyze_post_sentiment(self, text):
        """
        分析单条帖子的情绪
        
        Returns:
            'bullish', 'bearish', 'neutral'
        """
        bullish_words = ['涨停', '大涨', '买入', '看好', '拉升', '突破', '牛股', '赚钱', '冲', '吃肉', '涨停']
        bearish_words = ['跌停', '大跌', '卖出', '看空', '跳水', '破位', '垃圾', '亏钱', '跑', '割肉', '跌停']
        
        b_count = sum(1 for w in bullish_words if w in text)
        be_count = sum(1 for w in bearish_words if w in text)
        
        if b_count > be_count:
            return 'bullish'
        elif be_count > b_count:
            return 'bearish'
        else:
            return 'neutral'
    
    def analyze_sentiment(self, stock_code, limit=50):
        """
        分析股票的整体舆情
        
        Returns:
            dict: 舆情分析结果
        """
        posts = self.fetch_guba_posts(stock_code, limit)
        
        if not posts:
            return {
                'stock_code': stock_code,
                'total_posts': 0,
                'bullish': 0,
                'bearish': 0,
                'neutral': 0,
                'bullish_ratio': 0,
                'bearish_ratio': 0,
                'sentiment_score': 5.0,  # 0-10分
                'overall': '中性',
                'hot_keywords': [],
                'sample_posts': []
            }
        
        # 统计
        total = len(posts)
        bullish = sum(1 for p in posts if p['sentiment'] == 'bullish')
        bearish = sum(1 for p in posts if p['sentiment'] == 'bearish')
        neutral = total - bullish - bearish
        
        bullish_ratio = bullish / total if total > 0 else 0
        bearish_ratio = bearish / total if total > 0 else 0
        
        # 情绪得分 (0-10分)
        sentiment_score = 5 + (bullish_ratio - bearish_ratio) * 5
        sentiment_score = max(0, min(10, sentiment_score))
        
        # 整体判断
        if sentiment_score >= 7:
            overall = '偏多'
        elif sentiment_score <= 3:
            overall = '偏空'
        else:
            overall = '中性'
        
        # 提取热门关键词
        hot_keywords = self._extract_keywords([p['title'] for p in posts])
        
        return {
            'stock_code': stock_code,
            'total_posts': total,
            'bullish': bullish,
            'bearish': bearish,
            'neutral': neutral,
            'bullish_ratio': round(bullish_ratio * 100, 1),
            'bearish_ratio': round(bearish_ratio * 100, 1),
            'sentiment_score': round(sentiment_score, 1),
            'overall': overall,
            'hot_keywords': hot_keywords[:10],
            'sample_posts': posts[:5]
        }
    
    def _extract_keywords(self, texts):
        """提取热门关键词"""
        # 简单的词频统计
        word_count = {}
        
        for text in texts:
            words = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
            for word in words:
                if len(word) >= 2:
                    word_count[word] = word_count.get(word, 0) + 1
        
        # 过滤常见词，按频率排序
        stop_words = {'今日', '怎么', '什么', '这个', '一个', '大家', '可以', '今天', '明天', '现在'}
        filtered = {k: v for k, v in word_count.items() if k not in stop_words and v >= 2}
        
        return sorted(filtered.keys(), key=lambda x: filtered[x], reverse=True)
    
    def get_hot_stocks_from_guba(self, limit=20):
        """
        获取股吧热门股票（按讨论热度）
        """
        hot_stocks = []
        
        try:
            url = "https://guba.eastmoney.com/rank/"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                # 解析热门股票列表
                # 简化处理
        except Exception as e:
            print(f"⚠️ 获取热门股票失败: {e}")
        
        return hot_stocks

def main():
    """测试"""
    analyzer = GubaSentimentAnalyzer()
    
    # 分析某只股票的舆情
    stock_code = "000001"  # 平安银行
    print(f"📊 分析 {stock_code} 股吧舆情...\n")
    
    result = analyzer.analyze_sentiment(stock_code)
    
    print(f"总帖数: {result['total_posts']}")
    print(f"看多: {result['bullish']} ({result['bullish_ratio']}%)")
    print(f"看空: {result['bearish']} ({result['bearish_ratio']}%)")
    print(f"中性: {result['neutral']}")
    print(f"\n情绪得分: {result['sentiment_score']}/10")
    print(f"整体判断: {result['overall']}")
    
    if result['hot_keywords']:
        print(f"\n热门关键词: {', '.join(result['hot_keywords'][:5])}")
    
    if result['sample_posts']:
        print("\n示例帖子:")
        for i, post in enumerate(result['sample_posts'][:3], 1):
            emoji = '🟢' if post['sentiment'] == 'bullish' else '🔴' if post['sentiment'] == 'bearish' else '⚪'
            print(f"  {i}. {emoji} {post['title'][:40]}...")

if __name__ == "__main__":
    main()
