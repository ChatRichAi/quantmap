"""
QuantClaw Pro - 真实数据回测系统
使用 Yahoo Finance 数据源进行批量回测分析
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入系统模块
import sys
sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from perception_layer import PerceptionLayer
from cognition_layer import CognitionLayer
from decision_layer import DecisionLayer, MarketRegime
from knowledge_graph import PersonalityKnowledgeGraph


@dataclass
class BacktestResult:
    """回测结果"""
    ticker: str
    analysis_date: date
    mbti_type: str
    mbti_name: str
    category: str
    risk_level: str
    confidence: float
    dimension_scores: Dict[str, float]
    recommended_strategies: List[Dict]
    price_stats: Dict[str, float]
    features: Dict[str, float]
    
    def to_dict(self) -> Dict:
        return {
            'ticker': self.ticker,
            'analysis_date': self.analysis_date.isoformat(),
            'mbti_type': self.mbti_type,
            'mbti_name': self.mbti_name,
            'category': self.category,
            'risk_level': self.risk_level,
            'confidence': self.confidence,
            'dimension_scores': self.dimension_scores,
            'recommended_strategies': self.recommended_strategies,
            'price_stats': self.price_stats,
            'features': {k: round(v, 4) for k, v in list(self.features.items())[:20]}
        }


class YahooFinanceDataSource:
    """Yahoo Finance 数据源"""
    
    def __init__(self):
        self.data_cache: Dict[str, pd.DataFrame] = {}
        
    def fetch_data(self, ticker: str, period: str = '1y', interval: str = '1d') -> Optional[pd.DataFrame]:
        """
        获取股票数据
        
        Args:
            ticker: 股票代码 (如 'AAPL', 'MSFT', 'NVDA')
            period: 时间周期 ('1mo', '3mo', '6mo', '1y', '2y', '5y')
            interval: 时间间隔 ('1d', '1wk', '1mo')
            
        Returns:
            OHLCV DataFrame 或 None
        """
        # 检查缓存
        cache_key = f"{ticker}_{period}_{interval}"
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        try:
            # 尝试导入 yfinance
            import yfinance as yf
            
            logger.info(f"Fetching data for {ticker}...")
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return None
            
            # 标准化列名
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # 移除最后一行（当天可能不完整）
            if interval == '1d':
                df = df.iloc[:-1]
            
            # 缓存数据
            self.data_cache[cache_key] = df
            
            logger.info(f"Fetched {len(df)} days of data for {ticker}")
            return df
            
        except ImportError:
            logger.error("yfinance not installed. Run: pip install yfinance")
            return None
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return None
    
    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """获取股票基本信息"""
        try:
            import yfinance as yf
            stock = yf.Ticker(ticker)
            info = stock.info
            
            return {
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'beta': info.get('beta', 1.0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0) or 0,
                'avg_volume': info.get('averageVolume', 0),
                'country': info.get('country', 'US')
            }
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return None


class RealDataBacktestEngine:
    """
    真实数据回测引擎
    批量分析股票池，挖掘实际股性特征
    """
    
    def __init__(self, 
                 output_dir: str = '~/.openclaw/workspace/quantclaw/backtest_results',
                 use_knowledge_graph: bool = False):
        """
        初始化回测引擎
        
        Args:
            output_dir: 结果输出目录
            use_knowledge_graph: 是否使用Neo4j知识图谱
        """
        self.data_source = YahooFinanceDataSource()
        self.perception = PerceptionLayer()
        self.cognition = CognitionLayer()
        self.decision = DecisionLayer()
        self.kg = None
        
        if use_knowledge_graph:
            try:
                self.kg = PersonalityKnowledgeGraph()
                self.kg.initialize_personalities()
            except Exception as e:
                logger.warning(f"Knowledge graph not available: {e}")
        
        # 设置输出目录
        self.output_dir = Path(output_dir).expanduser()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 结果存储
        self.results: List[BacktestResult] = []
        
    def analyze_stock(self, ticker: str, 
                     period: str = '1y',
                     lookback_days: int = 60,
                     market_regime: MarketRegime = MarketRegime.SIDEWAYS) -> Optional[BacktestResult]:
        """
        分析单只股票
        
        Args:
            ticker: 股票代码
            period: 数据周期
            lookback_days: 用于特征计算的回看天数
            market_regime: 市场环境
            
        Returns:
            BacktestResult 或 None
        """
        logger.info(f"Analyzing {ticker}...")
        
        # 获取数据
        df = self.data_source.fetch_data(ticker, period=period)
        if df is None or len(df) < lookback_days + 10:
            logger.warning(f"Insufficient data for {ticker}")
            return None
        
        # 获取股票信息
        stock_info = self.data_source.get_stock_info(ticker)
        
        try:
            # 提取特征 (使用最近lookback_days的数据)
            feature_data = df.tail(lookback_days)
            feature_vector = self.perception.extract_features(
                ticker=ticker,
                df=feature_data
            )
            
            # 性格分类
            profile = self.cognition.classifier.classify(
                ticker=ticker,
                features=feature_vector.feature_dict
            )
            
            # 策略匹配
            current_price = df['close'].iloc[-1]
            strategy_recs = self.decision.matcher.match_strategies(
                profile.mbti_type.value,
                profile.dimension_scores.to_dict(),
                market_regime,
                top_n=3
            )
            
            # 计算价格统计
            price_stats = {
                'current_price': round(current_price, 2),
                'start_price': round(df['close'].iloc[0], 2),
                'total_return': round((current_price / df['close'].iloc[0] - 1) * 100, 2),
                'volatility': round(df['close'].pct_change().std() * np.sqrt(252) * 100, 2),
                'avg_volume': int(df['volume'].mean()),
                'max_price': round(df['high'].max(), 2),
                'min_price': round(df['low'].min(), 2),
                'data_days': len(df)
            }
            
            # 构建结果
            result = BacktestResult(
                ticker=ticker,
                analysis_date=date.today(),
                mbti_type=profile.mbti_type.value,
                mbti_name=profile.mbti_name,
                category=profile.category,
                risk_level=profile.risk_level,
                confidence=profile.confidence,
                dimension_scores=profile.dimension_scores.to_dict(),
                recommended_strategies=[
                    {
                        'name': rec.strategy_name,
                        'weight': round(rec.weight, 4),
                        'compatibility': round(rec.compatibility_score, 4),
                        'expected_return': round(rec.expected_return, 4)
                    }
                    for rec in strategy_recs
                ],
                price_stats=price_stats,
                features=feature_vector.feature_dict
            )
            
            # 保存到知识图谱
            if self.kg:
                self._save_to_knowledge_graph(ticker, profile, stock_info)
            
            logger.info(f"Completed analysis: {ticker} -> {profile.mbti_type.value} "
                       f"(confidence: {profile.confidence:.2%})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}", exc_info=True)
            return None
    
    def run_backtest(self, 
                    tickers: List[str],
                    period: str = '1y',
                    lookback_days: int = 60,
                    delay: float = 0.5) -> List[BacktestResult]:
        """
        批量回测分析
        
        Args:
            tickers: 股票代码列表
            period: 数据周期
            lookback_days: 回看天数
            delay: 请求间隔(避免API限制)
            
        Returns:
            回测结果列表
        """
        logger.info(f"Starting backtest for {len(tickers)} stocks...")
        
        self.results = []
        success_count = 0
        fail_count = 0
        
        for i, ticker in enumerate(tickers, 1):
            logger.info(f"[{i}/{len(tickers)}] Processing {ticker}...")
            
            result = self.analyze_stock(ticker, period, lookback_days)
            
            if result:
                self.results.append(result)
                success_count += 1
            else:
                fail_count += 1
            
            # 延迟避免API限制
            if delay > 0 and i < len(tickers):
                time.sleep(delay)
        
        logger.info(f"Backtest completed: {success_count} succeeded, {fail_count} failed")
        
        # 保存结果
        self._save_results()
        
        return self.results
    
    def _save_to_knowledge_graph(self, ticker: str, profile, stock_info: Optional[Dict]):
        """保存到知识图谱"""
        try:
            # 创建股票节点
            if stock_info:
                self.kg.create_stock(
                    ticker=ticker,
                    name=stock_info.get('name', ticker),
                    sector=stock_info.get('sector', 'Unknown'),
                    market_cap=stock_info.get('market_cap', 0)
                )
            
            # 创建性格快照
            self.kg.create_personality_snapshot(
                ticker=ticker,
                ie_score=profile.dimension_scores.ie,
                ns_score=profile.dimension_scores.ns,
                tf_score=profile.dimension_scores.tf,
                jp_score=profile.dimension_scores.jp,
                confidence=profile.confidence
            )
        except Exception as e:
            logger.warning(f"Failed to save to KG: {e}")
    
    def _save_results(self):
        """保存回测结果到文件"""
        if not self.results:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON
        json_path = self.output_dir / f'backtest_results_{timestamp}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in self.results], f, 
                     indent=2, ensure_ascii=False)
        logger.info(f"Results saved to {json_path}")
        
        # 保存CSV摘要
        csv_path = self.output_dir / f'backtest_summary_{timestamp}.csv'
        summary_data = []
        for r in self.results:
            summary_data.append({
                'ticker': r.ticker,
                'date': r.analysis_date,
                'mbti_type': r.mbti_type,
                'mbti_name': r.mbti_name,
                'category': r.category,
                'risk_level': r.risk_level,
                'confidence': r.confidence,
                'current_price': r.price_stats['current_price'],
                'total_return': r.price_stats['total_return'],
                'volatility': r.price_stats['volatility'],
                'ie_score': r.dimension_scores['ie'],
                'ns_score': r.dimension_scores['ns'],
                'tf_score': r.dimension_scores['tf'],
                'jp_score': r.dimension_scores['jp'],
                'top_strategy': r.recommended_strategies[0]['name'] if r.recommended_strategies else ''
            })
        
        pd.DataFrame(summary_data).to_csv(csv_path, index=False)
        logger.info(f"Summary saved to {csv_path}")
    
    def generate_report(self) -> str:
        """生成回测报告"""
        if not self.results:
            return "No results to report."
        
        report = []
        report.append("=" * 80)
        report.append("QuantClaw Pro - 回测分析报告")
        report.append("=" * 80)
        report.append(f"分析日期: {date.today()}")
        report.append(f"股票数量: {len(self.results)}")
        report.append("")
        
        # 性格分布统计
        mbti_dist = {}
        category_dist = {}
        risk_dist = {}
        
        for r in self.results:
            mbti_dist[r.mbti_type] = mbti_dist.get(r.mbti_type, 0) + 1
            category_dist[r.category] = category_dist.get(r.category, 0) + 1
            risk_dist[r.risk_level] = risk_dist.get(r.risk_level, 0) + 1
        
        report.append("【MBTI类型分布】")
        for mbti, count in sorted(mbti_dist.items(), key=lambda x: -x[1]):
            report.append(f"  {mbti}: {count}只 ({count/len(self.results)*100:.1f}%)")
        report.append("")
        
        report.append("【性格类别分布】")
        for cat, count in sorted(category_dist.items(), key=lambda x: -x[1]):
            report.append(f"  {cat}: {count}只 ({count/len(self.results)*100:.1f}%)")
        report.append("")
        
        report.append("【风险等级分布】")
        for risk, count in sorted(risk_dist.items(), key=lambda x: -x[1]):
            report.append(f"  {risk}: {count}只 ({count/len(self.results)*100:.1f}%)")
        report.append("")
        
        # 详细列表
        report.append("【详细分析结果】")
        report.append(f"{'股票':<8} {'MBTI':<6} {'性格':<12} {'类别':<12} {'收益':<8} {'波动':<8} {'置信度':<8}")
        report.append("-" * 80)
        
        for r in sorted(self.results, key=lambda x: x.ticker):
            report.append(
                f"{r.ticker:<8} {r.mbti_type:<6} {r.mbti_name:<12} "
                f"{r.category:<12} {r.price_stats['total_return']:<8.1f} "
                f"{r.price_stats['volatility']:<8.1f} {r.confidence:<8.2%}"
            )
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


# 预定义股票池
STOCK_UNIVERSE = {
    'us_large_cap': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 
        'BRK.B', 'UNH', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA'
    ],
    'us_tech': [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA',
        'NFLX', 'AMD', 'CRM', 'ORCL', 'INTC', 'ADBE', 'CSCO'
    ],
    'us_value': [
        'BRK.B', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'BAC',
        'CVX', 'KO', 'PEP', 'MRK', 'ABBV', 'TMO', 'COST'
    ],
    'china_adr': [
        'BABA', 'JD', 'PDD', 'NIO', 'LI', 'XPEV', 'TME',
        'DIDI', 'BIDU', 'NTES', 'TCOM', 'BEKE', 'ZTO', 'YUMC'
    ]
}


def main():
    """主函数 - 运行真实数据回测"""
    print("=" * 80)
    print("QuantClaw Pro - 真实数据回测系统")
    print("=" * 80)
    print("\n注意: 需要安装 yfinance")
    print("      pip install yfinance")
    print()
    
    # 检查yfinance
    try:
        import yfinance as yf
    except ImportError:
        print("❌ yfinance 未安装")
        print("请运行: pip install yfinance")
        return
    
    # 初始化回测引擎
    engine = RealDataBacktestEngine(
        output_dir='~/.openclaw/workspace/quantclaw/backtest_results',
        use_knowledge_graph=False  # 暂不连接Neo4j
    )
    
    # 选择股票池
    print("可用股票池:")
    for key in STOCK_UNIVERSE:
        print(f"  - {key}: {len(STOCK_UNIVERSE[key])}只")
    print()
    
    # 使用示例股票池（避免API限制，先用少量股票）
    test_tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'JPM', 'JNJ', 'KO', 'WMT']
    
    print(f"将分析 {len(test_tickers)} 只股票:")
    print(f"  {', '.join(test_tickers)}")
    print()
    
    # 运行回测
    results = engine.run_backtest(
        tickers=test_tickers,
        period='1y',
        lookback_days=60,
        delay=1.0  # 1秒延迟避免API限制
    )
    
    # 生成报告
    print("\n" + "=" * 80)
    report = engine.generate_report()
    print(report)
    
    # 保存报告
    report_path = Path('~/.openclaw/workspace/quantclaw/backtest_results').expanduser()
    report_path.mkdir(parents=True, exist_ok=True)
    report_file = report_path / f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n报告已保存: {report_file}")


if __name__ == "__main__":
    main()
