"""
QuantClaw Pro - MBTI 股性分类系统
主入口模块 (Main Entry Point)
整合三层架构，提供统一API接口
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

# 导入三层架构
from perception_layer import PerceptionLayer, FeatureVector
from cognition_layer import CognitionLayer, PersonalityProfile, DimensionScores
from decision_layer import DecisionLayer, MarketRegime
from knowledge_graph import PersonalityKnowledgeGraph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QuantClawPro:
    """
    QuantClaw Pro 主类
    整合感知层、认知层、决策层和知识图谱
    """
    
    def __init__(self, 
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "password",
                 use_knowledge_graph: bool = True):
        """
        初始化QuantClaw Pro
        
        Args:
            neo4j_uri: Neo4j连接URI
            neo4j_user: Neo4j用户名
            neo4j_password: Neo4j密码
            use_knowledge_graph: 是否使用知识图谱
        """
        logger.info("Initializing QuantClaw Pro...")
        
        # 初始化三层架构
        self.perception = PerceptionLayer()
        self.cognition = CognitionLayer()
        self.decision = DecisionLayer()
        
        # 初始化知识图谱（可选）
        self.kg = None
        if use_knowledge_graph:
            try:
                self.kg = PersonalityKnowledgeGraph(neo4j_uri, neo4j_user, neo4j_password)
                # 初始化16型性格节点
                self.kg.initialize_personalities()
                logger.info("Knowledge graph initialized")
            except Exception as e:
                logger.warning(f"Knowledge graph not available: {e}")
        
        logger.info("QuantClaw Pro initialized successfully")
    
    def analyze_stock(self,
                     ticker: str,
                     price_data: pd.DataFrame,
                     flow_data: Optional[pd.DataFrame] = None,
                     market_index: Optional[pd.Series] = None,
                     current_price: Optional[float] = None,
                     market_regime: MarketRegime = MarketRegime.SIDEWAYS,
                     save_to_kg: bool = True) -> Dict[str, Any]:
        """
        完整分析一只股票
        
        流程: 感知层 → 认知层 → 决策层 → 知识图谱存储
        
        Args:
            ticker: 股票代码
            price_data: OHLCV价格数据
            flow_data: 资金流向数据（可选）
            market_index: 市场指数数据（可选）
            current_price: 当前价格
            market_regime: 市场环境
            save_to_kg: 是否保存到知识图谱
            
        Returns:
            完整分析报告
        """
        logger.info(f"Analyzing stock: {ticker}")
        
        result = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'perception': None,
            'cognition': None,
            'decision': None
        }
        
        try:
            # ========== Step 1: 感知层 - 特征提取 ==========
            logger.info("Step 1: Extracting features...")
            feature_vector = self.perception.extract_features(
                ticker=ticker,
                df=price_data,
                flow_df=flow_data,
                market_index=market_index
            )
            
            result['perception'] = {
                'confidence': round(feature_vector.confidence_score, 4),
                'feature_count': len(feature_vector.features),
                'features': {k: round(v, 4) for k, v in list(feature_vector.feature_dict.items())[:10]}
            }
            
            # ========== Step 2: 认知层 - 性格分类 ==========
            logger.info("Step 2: Classifying personality...")
            profile = self.cognition.classifier.classify(
                ticker=ticker,
                features=feature_vector.feature_dict
            )
            
            result['cognition'] = {
                'mbti_type': profile.mbti_type.value,
                'mbti_name': profile.mbti_name,
                'category': profile.category,
                'risk_level': profile.risk_level,
                'confidence': round(profile.confidence, 4),
                'dimensions': profile.dimension_scores.to_dict(),
                'recommended_strategies': profile.recommended_strategies
            }
            
            # ========== Step 3: 决策层 - 策略匹配 ==========
            logger.info("Step 3: Matching strategies...")
            
            if current_price is None:
                current_price = price_data['close'].iloc[-1]
            
            decision = self.decision.make_decision(
                ticker=ticker,
                mbti_type=profile.mbti_type.value,
                dimension_scores=profile.dimension_scores.to_dict(),
                current_price=current_price,
                market_data={'volume': price_data['volume'].iloc[-1]},
                market_regime=market_regime
            )
            
            result['decision'] = decision
            
            # ========== Step 4: 知识图谱存储 ==========
            if save_to_kg and self.kg:
                logger.info("Step 4: Saving to knowledge graph...")
                self._save_to_knowledge_graph(ticker, profile, feature_vector)
            
            logger.info(f"Analysis complete: {ticker} -> {profile.mbti_type.value}")
            
        except Exception as e:
            logger.error(f"Analysis failed for {ticker}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _save_to_knowledge_graph(self, ticker: str, profile: PersonalityProfile, 
                                 feature_vector: FeatureVector) -> None:
        """保存分析结果到知识图谱"""
        try:
            # 创建股票节点
            self.kg.create_stock(
                ticker=ticker,
                name=ticker,  # 简化处理
                sector="Unknown",
                market_cap=0
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
            
            logger.info(f"Saved to knowledge graph: {ticker}")
        except Exception as e:
            logger.warning(f"Failed to save to KG: {e}")
    
    def batch_analyze(self,
                     stock_data_dict: Dict[str, pd.DataFrame],
                     market_regime: MarketRegime = MarketRegime.SIDEWAYS) -> Dict[str, Dict]:
        """
        批量分析多只股票
        
        Args:
            stock_data_dict: {ticker: price_data} 字典
            market_regime: 市场环境
            
        Returns:
            {ticker: analysis_result} 字典
        """
        results = {}
        
        for ticker, price_data in stock_data_dict.items():
            try:
                result = self.analyze_stock(
                    ticker=ticker,
                    price_data=price_data,
                    market_regime=market_regime
                )
                results[ticker] = result
            except Exception as e:
                logger.error(f"Failed to analyze {ticker}: {e}")
                results[ticker] = {'error': str(e)}
        
        return results
    
    def get_personality_report(self, ticker: str) -> Optional[Dict]:
        """
        从知识图谱获取股票性格报告
        
        Args:
            ticker: 股票代码
            
        Returns:
            性格历史报告
        """
        if not self.kg:
            return None
        
        try:
            history = self.kg.get_personality_history(ticker, limit=10)
            
            if not history:
                return None
            
            # 分析性格稳定性
            personalities = [h['personality'] for h in history]
            stable = len(set(personalities)) == 1
            
            return {
                'ticker': ticker,
                'current_personality': personalities[0],
                'stable': stable,
                'history_count': len(history),
                'history': history
            }
        except Exception as e:
            logger.error(f"Failed to get personality report: {e}")
            return None
    
    def compare_stocks(self, tickers: List[str]) -> Dict[str, Any]:
        """
        比较多只股票的性格特征
        
        Args:
            tickers: 股票代码列表
            
        Returns:
            比较报告
        """
        reports = {}
        for ticker in tickers:
            report = self.get_personality_report(ticker)
            if report:
                reports[ticker] = report
        
        if not reports:
            return {'error': 'No data available'}
        
        # 统计性格分布
        personality_counts = {}
        for ticker, report in reports.items():
            p = report['current_personality']
            personality_counts[p] = personality_counts.get(p, 0) + 1
        
        return {
            'stocks_analyzed': len(reports),
            'personality_distribution': personality_counts,
            'details': reports
        }
    
    def generate_insights(self, ticker: str) -> List[str]:
        """
        生成股票性格洞察
        
        Args:
            ticker: 股票代码
            
        Returns:
            洞察列表
        """
        report = self.get_personality_report(ticker)
        if not report:
            return []
        
        insights = []
        current = report['current_personality']
        
        # 基于性格类型的洞察
        personality_insights = {
            'INTJ': ['长期趋势股，适合耐心持有', '机构主导，波动相对稳健'],
            'INTP': ['走势复杂，传统分析可能失效', '需要更 sophisticated 的量化模型'],
            'ENTJ': ['市场霸主，强者恒强', '机构抱团，估值可能偏高'],
            'ENTP': ['多空博弈激烈，波动大', '适合高风险偏好投资者'],
            'INFJ': ['逆向特征，可能提前见底', '适合左侧交易者'],
            'INFP': ['概念驱动，高弹性', '情绪化严重，快进快出'],
            'ENFJ': ['板块龙头，带动效应强', '机构必选标的'],
            'ENFP': ['创新先锋，高成长', '关注产业趋势变化'],
            'ISTJ': ['低波动，稳定分红', '熊市避风港'],
            'ISFJ': ['被低估的价值股', '需要耐心等待价值回归'],
            'ESTJ': ['跟随指数，Beta稳定', '适合指数增强策略'],
            'ESFJ': ['群体跟随者，同涨同跌', '缺乏独立行情'],
            'ISTP': ['高波动，技术性强', '适合波段操作'],
            'ISFP': ['随机漫步，难以预测', '量化难赚钱'],
            'ESTP': ['短线天堂，追涨杀跌', '严格止损纪律'],
            'ESFP': ['情绪化严重，消息敏感', '警惕情绪高点']
        }
        
        insights.extend(personality_insights.get(current, []))
        
        # 稳定性洞察
        if report['stable']:
            insights.append('性格稳定，策略可长期执行')
        else:
            insights.append('性格多变，注意策略调整')
        
        return insights


# ==================== 使用示例 ====================

def demo():
    """演示完整流程"""
    print("=" * 80)
    print("QuantClaw Pro - 完整演示")
    print("=" * 80)
    
    # 初始化系统
    print("\n【初始化】QuantClaw Pro...")
    claw = QuantClawPro(use_knowledge_graph=False)  # 不使用Neo4j进行演示
    
    # 生成测试数据
    print("\n【准备】生成测试数据...")
    
    def generate_test_data(n_days=100, trend='up', volatility=0.02):
        """生成测试价格数据"""
        np.random.seed(42)
        dates = pd.date_range(end='2024-01-01', periods=n_days, freq='D')
        
        if trend == 'up':
            drift = 0.001
        elif trend == 'down':
            drift = -0.001
        else:
            drift = 0
        
        returns = np.random.normal(drift, volatility, n_days)
        prices = 100 * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.005, n_days)),
            'high': prices * (1 + abs(np.random.normal(0, 0.01, n_days))),
            'low': prices * (1 - abs(np.random.normal(0, 0.01, n_days))),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, n_days)
        }, index=dates)
        
        return df
    
    # 模拟不同风格的股票
    test_stocks = {
        'AAPL': generate_test_data(trend='up', volatility=0.015),      # 稳健上涨
        'TSLA': generate_test_data(trend='up', volatility=0.04),       # 高波动
        'JNJ': generate_test_data(trend='sideways', volatility=0.01),  # 低波动
    }
    
    # 分析每只股票
    for ticker, data in test_stocks.items():
        print(f"\n{'='*80}")
        print(f"【分析】{ticker}")
        print('='*80)
        
        result = claw.analyze_stock(
            ticker=ticker,
            price_data=data,
            current_price=data['close'].iloc[-1],
            market_regime=MarketRegime.SIDEWAYS,
            save_to_kg=False
        )
        
        if 'error' in result:
            print(f"错误: {result['error']}")
            continue
        
        # 显示感知层结果
        print(f"\n📊 感知层 (特征提取)")
        print(f"  数据置信度: {result['perception']['confidence']:.2%}")
        print(f"  特征维度: {result['perception']['feature_count']}")
        
        # 显示认知层结果
        cog = result['cognition']
        print(f"\n🧠 认知层 (性格分类)")
        print(f"  MBTI类型: {cog['mbti_type']} ({cog['mbti_name']})")
        print(f"  所属类别: {cog['category']}")
        print(f"  风险等级: {cog['risk_level']}")
        print(f"  分类置信度: {cog['confidence']:.2%}")
        print(f"\n  四维分数:")
        dims = cog['dimensions']
        print(f"    I/E (内向/外向): {dims['ie']:.4f} ({'E' if dims['ie'] > 0.5 else 'I'})")
        print(f"    N/S (直觉/实感): {dims['ns']:.4f} ({'N' if dims['ns'] > 0.5 else 'S'})")
        print(f"    T/F (思考/情感): {dims['tf']:.4f} ({'F' if dims['tf'] > 0.5 else 'T'})")
        print(f"    J/P (判断/感知): {dims['jp']:.4f} ({'J' if dims['jp'] > 0.5 else 'P'})")
        
        # 显示决策层结果
        dec = result['decision']
        print(f"\n🎯 决策层 (策略匹配)")
        print(f"  市场环境: {dec['market_regime']}")
        print(f"  综合信号: {dec['composite_signal']['signal']}")
        print(f"  建议仓位: {dec['composite_signal']['suggested_position']:.0%}")
        
        print(f"\n  推荐策略:")
        for i, strategy in enumerate(dec['recommended_strategies'][:3], 1):
            print(f"    {i}. {strategy['name']}")
            print(f"       权重: {strategy['weight']:.1%} | "
                  f"兼容性: {strategy['compatibility']:.2%} | "
                  f"预期收益: {strategy['expected_return']:.1%}")
        
        # 显示风险管理
        if dec['risk_management']:
            rm = dec['risk_management']
            print(f"\n  风险管理:")
            print(f"    风险等级: {rm['risk_level']}")
            print(f"    最大仓位: {rm['max_position_size']:.0%}")
            if rm['suggested_stop_price']:
                print(f"    止损价格: ${rm['suggested_stop_price']}")
            if rm['suggested_target_price']:
                print(f"    目标价格: ${rm['suggested_target_price']}")
    
    # 批量比较
    print(f"\n\n{'='*80}")
    print("【批量比较】股票性格分布")
    print('='*80)
    
    comparison = claw.compare_stocks(list(test_stocks.keys()))
    if 'personality_distribution' in comparison:
        print(f"\n性格分布:")
        for personality, count in comparison['personality_distribution'].items():
            print(f"  {personality}: {count}只")
    
    # 生成洞察
    print(f"\n\n{'='*80}")
    print("【洞察】AAPL 性格分析")
    print('='*80)
    
    insights = claw.generate_insights('AAPL')
    for i, insight in enumerate(insights, 1):
        print(f"  {i}. {insight}")
    
    print(f"\n{'='*80}")
    print("演示完成!")
    print('='*80)


if __name__ == "__main__":
    demo()
