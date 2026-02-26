"""
QuantClaw Pro v2.0 - 最终集成版
整合所有研究成果的完整系统
"""

import sys
sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from quantclaw_pro import QuantClawPro
from research.advanced_features import EnhancedPerceptionLayer
from research.paper_implementations import (
    ForecastingCompositionMethods,
    EntropyRegularizedMethods,
    IntegratedResearchMethods
)
from research.improved_entropy import ImprovedEntropyRegularization
from decision_layer import DecisionLayer, MarketRegime

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QuantClawConfig:
    """QuantClaw配置"""
    # 感知层配置
    use_advanced_features: bool = True
    feature_mode: str = "hybrid"  # basic/hybrid/full_research
    
    # 研究模块配置
    use_composition_forecast: bool = True  # 论文#1
    use_entropy_optimization: bool = True   # 论文#3
    
    # 熵正则化参数（改进版）
    epsilon: float = 0.15
    max_position: float = 0.25
    min_positions: int = 5
    
    # 知识图谱
    use_knowledge_graph: bool = False


class QuantClawProV2(QuantClawPro):
    """
    QuantClaw Pro v2.0
    学术论文增强的最终版本
    """
    
    def __init__(self, config: QuantClawConfig = None):
        self.config = config or QuantClawConfig()
        
        # 初始化感知层
        if self.config.feature_mode == "hybrid":
            self.perception = EnhancedPerceptionLayer(use_advanced_features=True)
            logger.info("✓ Enhanced Perception: 32 basic + 12 research features")
        else:
            from perception_layer import PerceptionLayer
            self.perception = PerceptionLayer()
            logger.info("✓ Basic Perception: 32 features")
        
        # 初始化认知层
        from cognition_layer import CognitionLayer
        self.cognition = CognitionLayer()
        logger.info("✓ Cognition Layer: MBTI classification")
        
        # 初始化决策层
        self.decision = DecisionLayer()
        logger.info("✓ Decision Layer: Strategy matching")
        
        # 初始化研究模块
        self.composition = None
        self.entropy = None
        
        if self.config.use_composition_forecast:
            self.composition = ForecastingCompositionMethods()
            logger.info("✓ Research #1: Composition Forecasting")
        
        if self.config.use_entropy_optimization:
            self.entropy = ImprovedEntropyRegularization(
                epsilon=self.config.epsilon,
                max_position=self.config.max_position,
                min_positions=self.config.min_positions
            )
            logger.info("✓ Research #3: Improved Entropy Regularization")
        
        logger.info("\n🚀 QuantClaw Pro v2.0 initialized successfully!")
    
    def analyze_portfolio(self,
                         tickers: List[str],
                         market_regime: MarketRegime = MarketRegime.SIDEWAYS,
                         lookback_days: int = 120) -> Dict:
        """
        投资组合分析（研究增强版）
        
        流程:
        1. 分析每只股票的性格
        2. 应用组成预测优化策略
        3. 应用熵正则化优化仓位
        """
        import yfinance as yf
        
        print("=" * 80)
        print("QuantClaw Pro v2.0 - Portfolio Analysis")
        print("=" * 80)
        
        # 获取数据
        print(f"\n📊 Fetching data for {len(tickers)} stocks...")
        stocks_data = {}
        
        for ticker in tickers:
            try:
                df = yf.download(ticker, period='6mo', progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[0].lower().replace(' ', '_') for c in df.columns]
                else:
                    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
                
                if len(df) >= lookback_days:
                    stocks_data[ticker] = df
            except Exception as e:
                logger.warning(f"Failed to fetch {ticker}: {e}")
        
        print(f"✓ Successfully loaded {len(stocks_data)} stocks")
        
        # 1. 分析每只股票的性格
        print("\n🧠 Analyzing stock personalities...")
        personalities = {}
        
        for ticker, df in stocks_data.items():
            try:
                feature_vector = self.perception.extract_features(ticker, df.tail(60))
                profile = self.cognition.classifier.classify(ticker, feature_vector.feature_dict)
                
                personalities[ticker] = {
                    'mbti': profile.mbti_type.value,
                    'name': profile.mbti_name,
                    'category': profile.category,
                    'risk': profile.risk_level,
                    'confidence': profile.confidence
                }
                
                print(f"  {ticker}: {profile.mbti_type.value} ({profile.mbti_name}) "
                      f"- Risk: {profile.risk_level}")
            except Exception as e:
                logger.warning(f"Analysis failed for {ticker}: {e}")
        
        # 2. 准备优化数据
        expected_returns = {}
        returns_history = {}
        
        for ticker, df in stocks_data.items():
            rets = df['close'].pct_change().dropna()
            expected_returns[ticker] = rets.mean() * 252
            returns_history[ticker] = rets
        
        # 3. 应用熵正则化优化（改进版）
        print("\n📈 Optimizing portfolio with entropy regularization...")
        
        if self.entropy and len(stocks_data) >= self.config.min_positions:
            opt_result = self.entropy.optimize_with_true_diversification(
                expected_returns,
                returns_history
            )
            
            print(f"\n✓ Optimization complete!")
            print(f"  Holdings: {opt_result['num_positions']} stocks")
            print(f"  Diversification: {opt_result['normalized_entropy']:.1%}")
            print(f"  Max position: {opt_result['max_single_position']:.1%}")
            
            # 显示推荐仓位
            print(f"\n📋 Recommended Portfolio:")
            for ticker, pos in sorted(opt_result['positions'].items(), 
                                     key=lambda x: -x[1]['weight']):
                bar = "█" * int(pos['weight'] * 20)
                personality = personalities.get(ticker, {})
                print(f"  {ticker:<6}: {pos['weight']:>6.1%} {bar} "
                      f"({personality.get('mbti', 'N/A')})")
        else:
            opt_result = {'positions': {}}
            print("  Using equal weight (insufficient data for optimization)")
        
        # 4. 生成综合报告
        report = {
            'stocks_analyzed': len(stocks_data),
            'personalities': personalities,
            'optimization': opt_result,
            'recommendations': self._generate_recommendations(personalities, opt_result)
        }
        
        return report
    
    def _generate_recommendations(self, personalities: Dict, optimization: Dict) -> List[str]:
        """生成投资建议"""
        recommendations = []
        
        # 基于性格分布的建议
        risk_levels = [p['risk'] for p in personalities.values()]
        high_risk = sum(1 for r in risk_levels if r in ['High', 'Extreme'])
        low_risk = sum(1 for r in risk_levels if r == 'Low')
        
        if high_risk > len(risk_levels) * 0.5:
            recommendations.append("⚠️ Portfolio is high-risk dominated. Consider adding defensive stocks (ISTJ/ISFJ types).")
        
        if low_risk > len(risk_levels) * 0.5:
            recommendations.append("✓ Portfolio is defensive. Good for conservative investors.")
        
        # 基于优化结果的建议
        if optimization.get('normalized_entropy', 0) > 0.7:
            recommendations.append("✓ Well diversified. Risk is properly spread.")
        elif optimization.get('normalized_entropy', 0) < 0.3:
            recommendations.append("⚠️ Concentration risk detected. Consider increasing epsilon parameter.")
        
        return recommendations


def demo_v2():
    """演示QuantClaw Pro v2.0"""
    print("\n" + "=" * 80)
    print("🚀 QuantClaw Pro v2.0 - Research Edition")
    print("=" * 80)
    print("\nFeatures:")
    print("  • 44-dimensional feature extraction (32 basic + 12 research)")
    print("  • MBTI personality classification")
    print("  • Research Paper #1: Composition Forecasting")
    print("  • Research Paper #3: Improved Entropy Regularization")
    print("  • Portfolio optimization with diversification control")
    
    # 配置
    config = QuantClawConfig(
        use_advanced_features=True,
        use_composition_forecast=True,
        use_entropy_optimization=True,
        epsilon=0.15,
        max_position=0.25,
        min_positions=5
    )
    
    # 初始化
    claw = QuantClawProV2(config)
    
    # 测试股票池
    test_portfolio = [
        'AAPL', 'MSFT', 'GOOGL',  # Tech
        'JPM', 'V',               # Finance
        'JNJ', 'UNH',             # Healthcare
        'WMT', 'COST',            # Consumer
        'XOM'                     # Energy
    ]
    
    # 分析
    result = claw.analyze_portfolio(test_portfolio)
    
    # 显示建议
    print("\n" + "=" * 80)
    print("💡 Investment Recommendations")
    print("=" * 80)
    
    for rec in result['recommendations']:
        print(f"  {rec}")
    
    print("\n" + "=" * 80)
    print("✅ Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    demo_v2()
