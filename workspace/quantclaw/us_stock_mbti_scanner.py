"""
QuantClaw Pro - 美股MBTI股性扫描系统
持续扫描美股，构建股性数据库
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Set
import json
import logging
import time
import sqlite3
from pathlib import Path
from dataclasses import dataclass, asdict
import schedule
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('~/.openclaw/workspace/quantclaw/mbti_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

import sys
sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

# 设置日志
log_path = Path('~/.openclaw/workspace/quantclaw/mbti_scanner.log').expanduser()
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)

from perception_layer import PerceptionLayer
from cognition_layer import CognitionLayer
from decision_layer import DecisionLayer, MarketRegime


# 美股股票池
US_STOCK_UNIVERSE = {
    # 科技巨头
    'tech_giants': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX', 'AMD', 'INTC'],
    # 金融
    'finance': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'AXP'],
    # 医疗健康
    'healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'LLY', 'TMO', 'ABT'],
    # 消费
    'consumer': ['WMT', 'COST', 'HD', 'PG', 'KO', 'PEP', 'MCD', 'NKE', 'SBUX'],
    # 能源
    'energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'OXY'],
    # 工业
    'industrial': ['BA', 'CAT', 'GE', 'HON', 'UPS', 'RTX', 'LMT'],
    # 通信
    'telecom': ['VZ', 'T', 'TMUS'],
    # ETF
    'etfs': ['SPY', 'QQQ', 'IWM', 'VTI', 'VXX']
}

# 合并所有股票
ALL_US_STOCKS = []
for category, stocks in US_STOCK_UNIVERSE.items():
    ALL_US_STOCKS.extend(stocks)
ALL_US_STOCKS = list(set(ALL_US_STOCKS))


@dataclass
class StockPersonalityRecord:
    """股票性格记录"""
    ticker: str
    scan_date: date
    scan_time: datetime
    mbti_type: str
    mbti_name: str
    category: str
    risk_level: str
    confidence: float
    ie_score: float
    ns_score: float
    tf_score: float
    jp_score: float
    current_price: float
    period_return: float
    volatility: float
    avg_volume: int
    top_strategy: str
    signal_strength: str
    
    def to_dict(self) -> dict:
        return asdict(self)


class MBTIPersonalityDatabase:
    """
    MBTI股性数据库
    使用SQLite存储历史分析结果
    """
    
    def __init__(self, db_path: str = '~/.openclaw/workspace/quantclaw/mbti_personality.db'):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()
        
        # 主表：性格记录
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personality_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                scan_date DATE NOT NULL,
                scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mbti_type TEXT NOT NULL,
                mbti_name TEXT,
                category TEXT,
                risk_level TEXT,
                confidence REAL,
                ie_score REAL,
                ns_score REAL,
                tf_score REAL,
                jp_score REAL,
                current_price REAL,
                period_return REAL,
                volatility REAL,
                avg_volume INTEGER,
                top_strategy TEXT,
                signal_strength TEXT,
                UNIQUE(ticker, scan_date)
            )
        ''')
        
        # 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON personality_records(ticker)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON personality_records(scan_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mbti ON personality_records(mbti_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON personality_records(category)')
        
        # 统计表：每日汇总
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                date DATE PRIMARY KEY,
                total_scanned INTEGER,
                mbti_distribution TEXT,
                category_distribution TEXT,
                high_confidence_count INTEGER
            )
        ''')
        
        self.conn.commit()
        logger.info(f"Database initialized: {self.db_path}")
    
    def insert_record(self, record: StockPersonalityRecord) -> bool:
        """插入性格记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO personality_records 
                (ticker, scan_date, scan_time, mbti_type, mbti_name, category, 
                 risk_level, confidence, ie_score, ns_score, tf_score, jp_score,
                 current_price, period_return, volatility, avg_volume,
                 top_strategy, signal_strength)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.ticker, record.scan_date, record.scan_time,
                record.mbti_type, record.mbti_name, record.category,
                record.risk_level, record.confidence, 
                record.ie_score, record.ns_score, record.tf_score, record.jp_score,
                record.current_price, record.period_return, record.volatility,
                record.avg_volume, record.top_strategy, record.signal_strength
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to insert record: {e}")
            return False
    
    def get_personality_history(self, ticker: str, days: int = 30) -> List[dict]:
        """获取股票性格历史"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM personality_records 
            WHERE ticker = ? 
            AND scan_date >= date('now', '-{} days')
            ORDER BY scan_date DESC
        '''.format(days), (ticker,))
        
        columns = [description[0] for description in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        return results
    
    def get_mbti_distribution(self, start_date: Optional[date] = None) -> Dict[str, int]:
        """获取MBTI分布统计"""
        cursor = self.conn.cursor()
        
        if start_date:
            cursor.execute('''
                SELECT mbti_type, COUNT(*) as count 
                FROM personality_records 
                WHERE scan_date >= ?
                GROUP BY mbti_type
            ''', (start_date,))
        else:
            cursor.execute('''
                SELECT mbti_type, COUNT(*) as count 
                FROM personality_records 
                GROUP BY mbti_type
            ''')
        
        return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_latest_by_mbti(self, mbti_type: str, limit: int = 10) -> List[dict]:
        """获取最新某MBTI类型的股票"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM personality_records 
            WHERE mbti_type = ?
            ORDER BY scan_date DESC, confidence DESC
            LIMIT ?
        ''', (mbti_type, limit))
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_stable_personalities(self, min_days: int = 5) -> List[dict]:
        """获取性格稳定的股票（连续多天同一MBTI）"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT ticker, mbti_type, COUNT(*) as days,
                   AVG(confidence) as avg_confidence
            FROM personality_records 
            WHERE scan_date >= date('now', '-7 days')
            GROUP BY ticker, mbti_type
            HAVING COUNT(*) >= ?
            ORDER BY avg_confidence DESC
        ''', (min_days,))
        
        return [
            {'ticker': row[0], 'mbti_type': row[1], 'days': row[2], 'avg_confidence': row[3]}
            for row in cursor.fetchall()
        ]
    
    def get_all_latest(self) -> List[dict]:
        """获取所有股票最新性格"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT pr.* FROM personality_records pr
            INNER JOIN (
                SELECT ticker, MAX(scan_date) as max_date
                FROM personality_records
                GROUP BY ticker
            ) latest ON pr.ticker = latest.ticker AND pr.scan_date = latest.max_date
            ORDER BY pr.ticker
        ''')
        
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def export_to_json(self, filepath: str):
        """导出数据到JSON"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM personality_records ORDER BY scan_date DESC')
        
        columns = [description[0] for description in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Exported {len(data)} records to {filepath}")


class USStockMBTIScanner:
    """
    美股MBTI股性扫描器
    持续扫描美股，更新股性数据库
    """
    
    def __init__(self):
        self.db = MBTIPersonalityDatabase()
        self.perception = PerceptionLayer()
        self.cognition = CognitionLayer()
        self.decision = DecisionLayer()
        
        self.scan_count = 0
        self.success_count = 0
        self.fail_count = 0
    
    def scan_stock(self, ticker: str, period: str = '3mo') -> Optional[StockPersonalityRecord]:
        """扫描单只股票"""
        try:
            import yfinance as yf
            
            # 获取数据
            data = yf.download(ticker, period=period, interval='1d', progress=False)
            if data.empty or len(data) < 30:
                return None
            
            # 处理列名
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [c[0].lower().replace(' ', '_') for c in data.columns]
            else:
                data.columns = [c.lower().replace(' ', '_') for c in data.columns]
            
            # 提取特征
            feature_vector = self.perception.extract_features(ticker, data.tail(60))
            
            # 性格分类
            profile = self.cognition.classifier.classify(ticker, feature_vector.feature_dict)
            
            # 策略匹配
            recommendations = self.decision.matcher.match_strategies(
                profile.mbti_type.value,
                profile.dimension_scores.to_dict(),
                MarketRegime.SIDEWAYS,
                top_n=1
            )
            
            top_strategy = recommendations[0].strategy_name if recommendations else 'Unknown'
            
            # 计算信号强度
            if profile.confidence > 0.5:
                signal = 'Strong'
            elif profile.confidence > 0.3:
                signal = 'Medium'
            else:
                signal = 'Weak'
            
            # 创建记录
            record = StockPersonalityRecord(
                ticker=ticker,
                scan_date=date.today(),
                scan_time=datetime.now(),
                mbti_type=profile.mbti_type.value,
                mbti_name=profile.mbti_name,
                category=profile.category,
                risk_level=profile.risk_level,
                confidence=profile.confidence,
                ie_score=profile.dimension_scores.ie,
                ns_score=profile.dimension_scores.ns,
                tf_score=profile.dimension_scores.tf,
                jp_score=profile.dimension_scores.jp,
                current_price=data['close'].iloc[-1],
                period_return=(data['close'].iloc[-1] / data['close'].iloc[0] - 1) * 100,
                volatility=data['close'].pct_change().std() * np.sqrt(252) * 100,
                avg_volume=int(data['volume'].mean()),
                top_strategy=top_strategy,
                signal_strength=signal
            )
            
            # 保存到数据库
            self.db.insert_record(record)
            
            self.success_count += 1
            return record
            
        except Exception as e:
            logger.error(f"Error scanning {ticker}: {e}")
            self.fail_count += 1
            return None
    
    def scan_batch(self, tickers: List[str], delay: float = 1.0) -> List[StockPersonalityRecord]:
        """批量扫描"""
        logger.info(f"Starting batch scan for {len(tickers)} stocks...")
        
        results = []
        for i, ticker in enumerate(tickers, 1):
            logger.info(f"[{i}/{len(tickers)}] Scanning {ticker}...")
            
            record = self.scan_stock(ticker)
            if record:
                results.append(record)
                logger.info(f"  ✓ {ticker}: {record.mbti_type} (confidence: {record.confidence:.1%})")
            else:
                logger.warning(f"  ✗ {ticker}: Failed")
            
            self.scan_count += 1
            
            if delay > 0 and i < len(tickers):
                time.sleep(delay)
        
        logger.info(f"Batch scan complete: {len(results)}/{len(tickers)} succeeded")
        return results
    
    def scan_all(self, delay: float = 1.0):
        """扫描所有美股"""
        logger.info(f"Starting full market scan ({len(ALL_US_STOCKS)} stocks)...")
        
        start_time = datetime.now()
        results = self.scan_batch(ALL_US_STOCKS, delay)
        duration = (datetime.now() - start_time).total_seconds()
        
        # 生成报告
        self._generate_daily_report(results, duration)
        
        return results
    
    def scan_category(self, category: str, delay: float = 1.0):
        """扫描特定板块"""
        if category not in US_STOCK_UNIVERSE:
            logger.error(f"Unknown category: {category}")
            return []
        
        tickers = US_STOCK_UNIVERSE[category]
        logger.info(f"Scanning category '{category}' ({len(tickers)} stocks)...")
        
        return self.scan_batch(tickers, delay)
    
    def _generate_daily_report(self, results: List[StockPersonalityRecord], duration: float):
        """生成每日扫描报告"""
        if not results:
            return
        
        # 统计
        mbti_dist = {}
        category_dist = {}
        high_conf = 0
        
        for r in results:
            mbti_dist[r.mbti_type] = mbti_dist.get(r.mbti_type, 0) + 1
            category_dist[r.category] = category_dist.get(r.category, 0) + 1
            if r.confidence > 0.3:
                high_conf += 1
        
        report = []
        report.append("=" * 80)
        report.append("MBTI股性扫描日报")
        report.append("=" * 80)
        report.append(f"扫描日期: {date.today()}")
        report.append(f"扫描数量: {len(results)} 只股票")
        report.append(f"耗时: {duration:.1f} 秒")
        report.append(f"成功率: {self.success_count}/{self.scan_count} ({self.success_count/max(1,self.scan_count)*100:.1f}%)")
        report.append("")
        
        report.append("【MBTI类型分布】")
        for mbti, count in sorted(mbti_dist.items(), key=lambda x: -x[1]):
            report.append(f"  {mbti}: {count}只 ({count/len(results)*100:.1f}%)")
        report.append("")
        
        report.append("【性格类别分布】")
        for cat, count in sorted(category_dist.items(), key=lambda x: -x[1]):
            report.append(f"  {cat}: {count}只 ({count/len(results)*100:.1f}%)")
        report.append("")
        
        report.append(f"高置信度股票 (conf > 30%): {high_conf}只")
        report.append("")
        
        # 今日新增/变化的股票
        report.append("【今日最新股性】")
        for r in sorted(results, key=lambda x: -x.confidence)[:10]:
            report.append(f"  {r.ticker:<6} {r.mbti_type:<6} {r.mbti_name:<12} "
                         f"置信度:{r.confidence:>6.1%} 收益:{r.period_return:>6.1f}%")
        
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        print("\n" + report_text)
        
        # 保存报告
        report_path = Path('~/.openclaw/workspace/quantclaw/reports').expanduser()
        report_path.mkdir(parents=True, exist_ok=True)
        
        report_file = report_path / f"daily_report_{date.today()}.txt"
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        logger.info(f"Daily report saved: {report_file}")
    
    def run_continuous(self, scan_time: str = "09:30", categories: Optional[List[str]] = None):
        """
        持续运行扫描
        
        Args:
            scan_time: 每日扫描时间 (HH:MM)
            categories: 指定扫描板块，None则扫描全部
        """
        def daily_job():
            logger.info("=" * 80)
            logger.info(f"Starting scheduled scan at {datetime.now()}")
            logger.info("=" * 80)
            
            if categories:
                for category in categories:
                    self.scan_category(category, delay=0.5)
            else:
                self.scan_all(delay=0.5)
            
            # 导出数据
            export_path = Path('~/.openclaw/workspace/quantclaw/exports').expanduser()
            export_path.mkdir(parents=True, exist_ok=True)
            self.db.export_to_json(export_path / f"mbti_personality_{date.today()}.json")
            
            logger.info("Scheduled scan complete. Waiting for next run...")
        
        # 设置定时任务
        schedule.every().day.at(scan_time).do(daily_job)
        
        logger.info(f"Continuous scanner started. Will scan daily at {scan_time}")
        logger.info("Press Ctrl+C to stop")
        
        # 立即执行一次
        daily_job()
        
        # 保持运行
        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    """主函数"""
    print("=" * 80)
    print("QuantClaw Pro - 美股MBTI股性扫描系统")
    print("=" * 80)
    print()
    print("功能:")
    print("  1. 立即扫描 - 扫描所有美股")
    print("  2. 板块扫描 - 扫描特定板块")
    print("  3. 持续运行 - 每日定时扫描")
    print()
    
    scanner = USStockMBTIScanner()
    
    # 默认：立即扫描所有
    print("开始扫描所有美股...")
    scanner.scan_all(delay=0.5)
    
    # 显示统计
    print("\n" + "=" * 80)
    print("当前股性库统计")
    print("=" * 80)
    
    all_latest = scanner.db.get_all_latest()
    print(f"\n数据库中股票数量: {len(all_latest)}")
    
    if all_latest:
        mbti_dist = scanner.db.get_mbti_distribution()
        print("\nMBTI分布:")
        for mbti, count in sorted(mbti_dist.items(), key=lambda x: -x[1]):
            print(f"  {mbti}: {count}只")
        
        # 显示高置信度股票
        stable = scanner.db.get_stable_personalities(min_days=3)
        if stable:
            print(f"\n性格稳定的股票 (连续3天同一MBTI): {len(stable)}只")
            for s in stable[:5]:
                print(f"  {s['ticker']}: {s['mbti_type']} ({s['days']}天, 平均置信度{s['avg_confidence']:.1%})")


if __name__ == "__main__":
    main()
