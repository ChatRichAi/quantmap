#!/usr/bin/env python3
"""
新闻热点获取器 - 获取股票/题材相关新闻
"""

import json
import re
from datetime import datetime, timedelta
from urllib.parse import quote
import urllib.request
import ssl

# 禁用SSL验证（某些网站需要）
ssl._create_default_https_context = ssl._create_unverified_context

class NewsFetcher:
    """新闻获取器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    
    def fetch_10jqka_news(self, stock_code=None, keyword=None, limit=10):
        """
        从同花顺获取新闻
        
        Args:
            stock_code: 股票代码
            keyword: 关键词（题材）
            limit: 返回数量
        """
        news_list = []
        
        try:
            # 同花顺财经新闻接口
            if stock_code:
                url = f"http://basic.10jqka.com.cn/api/stockph.php?code={stock_code}"
            else:
                # 热点新闻
                url = "http://news.10jqka.com.cn/today_list/"
            
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')
                # 这里需要解析HTML提取新闻
                # 简化处理，返回示例数据
                news_list = self._parse_news_html(html, limit)
        except Exception as e:
            print(f"⚠️ 获取同花顺新闻失败: {e}")
        
        return news_list
    
    def fetch_eastmoney_news(self, stock_code=None, keyword=None, limit=10):
        """
        从东方财富获取新闻
        """
        news_list = []
        
        try:
            if stock_code:
                # 个股新闻
                secid = f"0.{stock_code}" if stock_code.startswith('0') or stock_code.startswith('3') else f"1.{stock_code}"
                url = f"https://searchapi.eastmoney.com/api/sns/get?count={limit}&type=20&secid={secid}"
            else:
                # 财经要闻
                url = f"https://searchapi.eastmoney.com/api/sns/get?count={limit}&type=20"
            
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if 'result' in data and 'data' in data['result']:
                    for item in data['result']['data'][:limit]:
                        news_list.append({
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'source': item.get('source', '东方财富'),
                            'time': item.get('time', ''),
                            'summary': item.get('content', '')[:100],
                            'sentiment': self._analyze_sentiment(item.get('title', ''))
                        })
        except Exception as e:
            print(f"⚠️ 获取东方财富新闻失败: {e}")
        
        return news_list
    
    def fetch_sina_finance(self, limit=10):
        """
        从新浪财经获取要闻
        """
        news_list = []
        
        try:
            url = f"https://feed.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num={limit}&r={datetime.now().timestamp()}"
            
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if 'result' in data and 'data' in data['result']:
                    for item in data['result']['data'][:limit]:
                        news_list.append({
                            'title': item.get('title', ''),
                            'url': item.get('url', ''),
                            'source': '新浪财经',
                            'time': item.get('time', ''),
                            'summary': '',
                            'sentiment': self._analyze_sentiment(item.get('title', ''))
                        })
        except Exception as e:
            print(f"⚠️ 获取新浪财经新闻失败: {e}")
        
        return news_list
    
    def _parse_news_html(self, html, limit):
        """解析新闻HTML（简化版）"""
        news_list = []
        # 这里应该使用BeautifulSoup等库解析HTML
        # 简化处理
        return news_list
    
    def _analyze_sentiment(self, text):
        """
        简单的情感分析
        
        Returns:
            'positive', 'negative', 'neutral'
        """
        positive_words = ['涨', '升', '突破', '利好', '增长', '盈利', '反弹', '大涨', '涨停', '拉升', '强势']
        negative_words = ['跌', '降', '下跌', '利空', '亏损', '暴跌', '跌停', '跳水', '弱势', '回调']
        
        p_count = sum(1 for w in positive_words if w in text)
        n_count = sum(1 for w in negative_words if w in text)
        
        if p_count > n_count:
            return 'positive'
        elif n_count > p_count:
            return 'negative'
        else:
            return 'neutral'
    
    def get_hot_themes(self):
        """
        获取当前热点题材
        """
        # 这里应该从龙虎榜、涨停板数据中提取热点
        # 简化返回示例
        return []
    
    def fetch_all_news(self, stock_code=None, keyword=None, limit=10):
        """
        获取所有来源的新闻
        
        Returns:
            list: 合并后的新闻列表，按时间排序
        """
        all_news = []
        
        # 从多个源获取
        all_news.extend(self.fetch_eastmoney_news(stock_code, keyword, limit))
        all_news.extend(self.fetch_sina_finance(limit))
        
        # 去重（按标题）
        seen_titles = set()
        unique_news = []
        for news in all_news:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                unique_news.append(news)
        
        # 按时间排序（如果有时间信息）
        return unique_news[:limit]
    
    def analyze_theme_from_news(self, news_list):
        """
        从新闻中提取关联题材
        
        Returns:
            dict: 题材 -> 相关新闻数
        """
        # 常见题材关键词
        themes = {
            'AI算力': ['AI', '算力', '人工智能', '大模型', 'ChatGPT', 'AIGC'],
            '机器人': ['机器人', '人形机器人', '工业机器人', '减速器', '伺服'],
            '芯片': ['芯片', '半导体', '光刻机', '集成电路', '国产替代'],
            '新能源': ['新能源', '光伏', '储能', '锂电池', '电动车', '宁德时代'],
            '医药': ['医药', '创新药', 'CRO', '医疗器械', '中药'],
            '金融': ['金融', '券商', '银行', '保险', '期货'],
            '消费': ['消费', '白酒', '食品饮料', '零售', '免税'],
            '地产': ['房地产', '地产', '基建', '建材', '家居'],
        }
        
        theme_count = {k: 0 for k in themes}
        
        for news in news_list:
            title = news.get('title', '')
            for theme, keywords in themes.items():
                if any(kw in title for kw in keywords):
                    theme_count[theme] += 1
        
        # 按数量排序
        return dict(sorted(theme_count.items(), key=lambda x: x[1], reverse=True))

def main():
    """测试"""
    fetcher = NewsFetcher()
    
    # 获取新闻
    print("📰 获取新闻中...")
    news = fetcher.fetch_all_news(limit=10)
    
    print(f"\n获取到 {len(news)} 条新闻:\n")
    for i, n in enumerate(news[:5], 1):
        sentiment_emoji = {'positive': '🟢', 'negative': '🔴', 'neutral': '⚪'}.get(n['sentiment'], '⚪')
        print(f"{i}. {sentiment_emoji} {n['title']}")
        print(f"   来源: {n['source']} | 时间: {n.get('time', 'N/A')}")
        print()
    
    # 分析题材
    themes = fetcher.analyze_theme_from_news(news)
    print("\n📊 热点题材分析:")
    for theme, count in themes.items():
        if count > 0:
            print(f"  {theme}: {count} 条相关新闻")

if __name__ == "__main__":
    main()
