"""
QuantClaw Pro - 多时间维度分析系统
整合 15分钟 / 1小时 / 4小时 / 1天 数据
捕捉股票在不同时间尺度的"性格"
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeFrame(Enum):
    """时间维度枚举"""
    M15 = "15m"      # 15分钟
    H1 = "1h"        # 1小时
    H4 = "4h"        # 4小时
    D1 = "1d"        # 1天


@dataclass
class MultiTimeframeFeatures:
    """多时间维度特征"""
    m15_features: Optional[Dict[str, float]] = None
    h1_features: Optional[Dict[str, float]] = None
    h4_features: Optional[Dict[str, float]] = None
    d1_features: Optional[Dict[str, float]] = None
    
    def get_available_timeframes(self) -> List[TimeFrame]:
        """获取可用的时间维度"""
        available = []
        if self.m15_features:
            available.append(TimeFrame.M15)
        if self.h1_features:
            available.append(TimeFrame.H1)
        if self.h4_features:
            available.append(TimeFrame.H4)
        if self.d1_features:
            available.append(TimeFrame.D1)
        return available


class MultiTimeframeDataSource:
    """
    多时间维度数据源
    获取 15m/1h/4h/1d 数据
    """
    
    # yfinance 支持的间隔映射
    INTERVAL_MAP = {
        TimeFrame.M15: "15m",
        TimeFrame.H1: "1h",
        TimeFrame.H4: "1h",  # yfinance不支持4h，需要从1h聚合
        TimeFrame.D1: "1d"
    }
    
    # 数据周期（需要足够的历史数据）
    PERIOD_MAP = {
        TimeFrame.M15: "1mo",   # 15分钟需要1个月
        TimeFrame.H1: "3mo",    # 1小时需要3个月
        TimeFrame.H4: "6mo",    # 4小时需要6个月
        TimeFrame.D1: "1y"      # 1天需要1年
    }
    
    def __init__(self):
        self.cache: Dict[str, pd.DataFrame] = {}
    
    def fetch_multi_timeframe(self, ticker: str) -> Dict[TimeFrame, Optional[pd.DataFrame]]:
        """
        获取多时间维度数据
        
        Returns:
            {TimeFrame: DataFrame} 字典
        """
        results = {}
        
        try:
            import yfinance as yf
            
            # 获取日线数据
            logger.info(f"Fetching daily data for {ticker}...")
            daily = yf.download(ticker, period=self.PERIOD_MAP[TimeFrame.D1], 
                               interval=self.INTERVAL_MAP[TimeFrame.D1], 
                               progress=False)
            if not daily.empty:
                # 处理多级列名
                if isinstance(daily.columns, pd.MultiIndex):
                    daily.columns = [c[0].lower().replace(' ', '_') for c in daily.columns]
                else:
                    daily.columns = [c.lower().replace(' ', '_') for c in daily.columns]
                results[TimeFrame.D1] = daily
            
            # 获取1小时数据（用于4小时聚合）
            logger.info(f"Fetching hourly data for {ticker}...")
            hourly = yf.download(ticker, period="1mo", interval="1h", progress=False)
            if not hourly.empty:
                # 处理多级列名
                if isinstance(hourly.columns, pd.MultiIndex):
                    hourly.columns = [c[0].lower().replace(' ', '_') for c in hourly.columns]
                else:
                    hourly.columns = [c.lower().replace(' ', '_') for c in hourly.columns]
                results[TimeFrame.H1] = hourly
                
                # 聚合为4小时数据
                h4_data = self._aggregate_to_4h(hourly)
                if h4_data is not None:
                    results[TimeFrame.H4] = h4_data
            
            # 获取15分钟数据
            logger.info(f"Fetching 15-min data for {ticker}...")
            m15 = yf.download(ticker, period="5d", interval="15m", progress=False)
            if not m15.empty:
                # 处理多级列名
                if isinstance(m15.columns, pd.MultiIndex):
                    m15.columns = [c[0].lower().replace(' ', '_') for c in m15.columns]
                else:
                    m15.columns = [c.lower().replace(' ', '_') for c in m15.columns]
                results[TimeFrame.M15] = m15
            
        except Exception as e:
            logger.error(f"Error fetching multi-timeframe data: {e}")
        
        return results
    
    def _aggregate_to_4h(self, hourly_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """将1小时数据聚合为4小时数据"""
        try:
            # 每4小时聚合
            df = hourly_df.copy()
            df['hour_group'] = (df.index.hour // 4) * 4
            
            # 按日期和小时组聚合
            agg_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            
            # 重新采样为4小时
            h4 = df.resample('4h').agg(agg_dict).dropna()
            return h4
        except Exception as e:
            logger.error(f"Error aggregating to 4h: {e}")
            return None


class MultiTimeframeFeatureExtractor:
    """
    多时间维度特征提取器
    从不同时间尺度提取特征
    """
    
    def __init__(self):
        self.perception = None  # 将在导入后初始化
        
    def extract_all_timeframes(self, 
                               ticker: str,
                               data_dict: Dict[TimeFrame, pd.DataFrame],
                               lookback_periods: Optional[Dict[TimeFrame, int]] = None
                               ) -> MultiTimeframeFeatures:
        """
        从所有可用时间维度提取特征
        
        Args:
            ticker: 股票代码
            data_dict: {TimeFrame: DataFrame} 字典
            lookback_periods: 各时间维度的回看周期数
            
        Returns:
            MultiTimeframeFeatures 对象
        """
        # 延迟导入避免循环依赖
        from perception_layer import PerceptionLayer
        self.perception = PerceptionLayer()
        
        if lookback_periods is None:
            lookback_periods = {
                TimeFrame.M15: 96,    # 15分钟: 96个周期 = 1天
                TimeFrame.H1: 168,    # 1小时: 168个周期 = 1周
                TimeFrame.H4: 30,     # 4小时: 30个周期 = 5天
                TimeFrame.D1: 60      # 1天: 60个周期 = 2个月
            }
        
        features = MultiTimeframeFeatures()
        
        for tf, df in data_dict.items():
            if df is None or len(df) < lookback_periods[tf]:
                logger.warning(f"Insufficient data for {tf.value}: {len(df) if df is not None else 0} bars")
                continue
            
            try:
                # 提取该时间维度的特征
                lookback = lookback_periods[tf]
                feature_data = df.tail(lookback)
                
                feature_vector = self.perception.extract_features(
                    ticker=f"{ticker}_{tf.value}",
                    df=feature_data
                )
                
                # 添加时间维度前缀
                prefixed_features = {f"{tf.value}_{k}": v 
                                   for k, v in feature_vector.feature_dict.items()}
                
                if tf == TimeFrame.M15:
                    features.m15_features = prefixed_features
                elif tf == TimeFrame.H1:
                    features.h1_features = prefixed_features
                elif tf == TimeFrame.H4:
                    features.h4_features = prefixed_features
                elif tf == TimeFrame.D1:
                    features.d1_features = prefixed_features
                
                logger.info(f"Extracted {len(prefixed_features)} features from {tf.value}")
                
            except Exception as e:
                logger.error(f"Error extracting features for {tf.value}: {e}")
        
        return features


class MultiTimeframePersonalityAnalyzer:
    """
    多时间维度性格分析器
    融合多个时间维度的特征进行综合判断
    """
    
    # 时间维度权重（可根据经验调整）
    TIMEFRAME_WEIGHTS = {
        TimeFrame.M15: 0.15,   # 15分钟: 短期情绪
        TimeFrame.H1: 0.25,    # 1小时: 日内趋势
        TimeFrame.H4: 0.30,    # 4小时: 日间趋势（最重要）
        TimeFrame.D1: 0.30     # 1天: 长期结构
    }
    
    # 各时间维度关注的特征
    TIMEFRAME_FOCUS = {
        TimeFrame.M15: ['volatility', 'volume_price_corr', 'rsi_extreme_freq'],
        TimeFrame.H1: ['adx', 'trend_slope', 'ma_alignment'],
        TimeFrame.H4: ['hurst_exponent', 'direction_consistency', 'trend_efficiency'],
        TimeFrame.D1: ['market_correlation', 'support_distance', 'consolidation_ratio']
    }
    
    def __init__(self):
        self.cognition = None  # 延迟导入
    
    def analyze(self, ticker: str, mtf_features: MultiTimeframeFeatures) -> Dict:
        """
        多维度综合分析
        
        Args:
            ticker: 股票代码
            mtf_features: 多时间维度特征
            
        Returns:
            综合分析结果
        """
        from cognition_layer import CognitionLayer
        self.cognition = CognitionLayer()
        
        # 1. 分别分析各时间维度
        timeframe_results = {}
        
        for tf in mtf_features.get_available_timeframes():
            # 获取正确的属性名
            attr_map = {
                TimeFrame.M15: 'm15_features',
                TimeFrame.H1: 'h1_features',
                TimeFrame.H4: 'h4_features',
                TimeFrame.D1: 'd1_features'
            }
            attr_name = attr_map.get(tf)
            if not attr_name:
                continue
                
            features = getattr(mtf_features, attr_name)
            if features:
                # 移除时间维度前缀用于分析
                clean_features = {k.replace(f"{tf.value}_", ""): v 
                                for k, v in features.items()}
                
                profile = self.cognition.classifier.classify(ticker, clean_features)
                timeframe_results[tf] = {
                    'mbti': profile.mbti_type.value,
                    'dimensions': profile.dimension_scores.to_dict(),
                    'confidence': profile.confidence
                }
        
        # 2. 融合各时间维度的四维分数
        fused_dimensions = self._fuse_dimensions(timeframe_results)
        
        # 3. 基于融合后的维度重新分类
        fused_profile = self.cognition.classifier.classify(ticker, fused_dimensions)
        
        # 4. 检测时间维度一致性（共振/背离）
        consistency = self._analyze_timeframe_consistency(timeframe_results)
        
        return {
            'ticker': ticker,
            'fused_personality': {
                'mbti_type': fused_profile.mbti_type.value,
                'mbti_name': fused_profile.mbti_name,
                'category': fused_profile.category,
                'risk_level': fused_profile.risk_level,
                'confidence': fused_profile.confidence,
                'dimensions': fused_profile.dimension_scores.to_dict()
            },
            'timeframe_details': timeframe_results,
            'consistency_analysis': consistency,
            'trading_implications': self._generate_implications(consistency)
        }
    
    def _fuse_dimensions(self, timeframe_results: Dict) -> Dict[str, float]:
        """
        融合各时间维度的四维分数
        
        使用加权平均，不同时间维度有不同的权重
        """
        fused = {'ie': 0, 'ns': 0, 'tf': 0, 'jp': 0}
        total_weight = 0
        
        for tf, result in timeframe_results.items():
            weight = self.TIMEFRAME_WEIGHTS.get(tf, 0.25)
            dims = result['dimensions']
            
            fused['ie'] += dims['ie'] * weight
            fused['ns'] += dims['ns'] * weight
            fused['tf'] += dims['tf'] * weight
            fused['jp'] += dims['jp'] * weight
            total_weight += weight
        
        # 归一化
        if total_weight > 0:
            for key in fused:
                fused[key] /= total_weight
        
        return fused
    
    def _analyze_timeframe_consistency(self, timeframe_results: Dict) -> Dict:
        """
        分析时间维度一致性
        
        检测是否存在多周期共振或背离
        """
        if len(timeframe_results) < 2:
            return {'status': 'insufficient_data'}
        
        # 提取各时间维度的MBTI类型
        mbti_types = [r['mbti'] for r in timeframe_results.values()]
        
        # 检查是否一致
        if len(set(mbti_types)) == 1:
            consistency = 'perfect_alignment'  # 完全一致
        elif len(set(mbti_types)) == 2:
            consistency = 'partial_alignment'  # 部分一致
        else:
            consistency = 'divergence'  # 背离
        
        # 分析四维一致性
        dimension_variance = {}
        for dim in ['ie', 'ns', 'tf', 'jp']:
            values = [r['dimensions'][dim] for r in timeframe_results.values()]
            variance = np.var(values)
            dimension_variance[dim] = {
                'variance': variance,
                'consistency': 'high' if variance < 0.05 else ('medium' if variance < 0.1 else 'low')
            }
        
        return {
            'status': consistency,
            'mbti_types_by_timeframe': {tf.value: r['mbti'] 
                                        for tf, r in timeframe_results.items()},
            'dimension_variance': dimension_variance,
            'recommendation': self._consistency_recommendation(consistency)
        }
    
    def _consistency_recommendation(self, status: str) -> str:
        """根据一致性给出建议"""
        recommendations = {
            'perfect_alignment': '多周期共振，信号强，可大胆执行策略',
            'partial_alignment': '部分共振，信号中等，适当仓位参与',
            'divergence': '多周期背离，信号混乱，建议观望或降低仓位',
            'insufficient_data': '数据不足，无法判断多周期一致性'
        }
        return recommendations.get(status, '未知')
    
    def _generate_implications(self, consistency: Dict) -> List[str]:
        """生成交易启示"""
        implications = []
        
        status = consistency.get('status')
        
        if status == 'perfect_alignment':
            implications.extend([
                '✓ 多周期方向一致，趋势确认度高',
                '✓ 可以使用标准仓位或加仓',
                '✓ 止损可以适当放宽'
            ])
        elif status == 'partial_alignment':
            implications.extend([
                '△ 部分周期确认，趋势有待观察',
                '△ 使用标准仓位或降低仓位',
                '△ 严格执行止损'
            ])
        elif status == 'divergence':
            implications.extend([
                '✗ 多周期冲突，市场处于震荡或转折',
                '✗ 降低仓位或观望',
                '✗ 缩短持仓周期，快进快出'
            ])
        
        # 检查具体维度的一致性
        dim_var = consistency.get('dimension_variance', {})
        
        if dim_var.get('ns', {}).get('consistency') == 'low':
            implications.append('⚠ 趋势维度(N/S)分歧大，方向不明朗')
        
        if dim_var.get('jp', {}).get('consistency') == 'low':
            implications.append('⚠ 判断维度(J/P)分歧大，市场犹豫')
        
        return implications


# ==================== 使用示例 ====================

def demo_multi_timeframe():
    """多时间维度分析演示"""
    print("=" * 80)
    print("QuantClaw Pro - 多时间维度分析演示")
    print("=" * 80)
    print("\n分析维度: 15分钟 / 1小时 / 4小时 / 1天")
    print()
    
    # 初始化组件
    data_source = MultiTimeframeDataSource()
    feature_extractor = MultiTimeframeFeatureExtractor()
    analyzer = MultiTimeframePersonalityAnalyzer()
    
    # 选择股票
    tickers = ['AAPL', 'TSLA']
    
    for ticker in tickers:
        print(f"\n{'='*80}")
        print(f"【分析】{ticker}")
        print('='*80)
        
        # 1. 获取多时间维度数据
        print("\n📥 获取多时间维度数据...")
        data_dict = data_source.fetch_multi_timeframe(ticker)
        
        available = [tf.value for tf, df in data_dict.items() if df is not None]
        print(f"  可用维度: {', '.join(available)}")
        
        if not available:
            print("  ❌ 无可用数据")
            continue
        
        # 显示各维度数据量
        for tf, df in data_dict.items():
            if df is not None:
                print(f"  {tf.value}: {len(df)} 根K线")
        
        # 2. 提取多维度特征
        print("\n🔍 提取多时间维度特征...")
        mtf_features = feature_extractor.extract_all_timeframes(ticker, data_dict)
        
        # 3. 多维度综合分析
        print("\n🧠 多维度综合分析...")
        result = analyzer.analyze(ticker, mtf_features)
        
        # 显示结果
        fused = result['fused_personality']
        print(f"\n  融合性格: {fused['mbti_type']} ({fused['mbti_name']})")
        print(f"  所属类别: {fused['category']}")
        print(f"  风险等级: {fused['risk_level']}")
        print(f"  置信度: {fused['confidence']:.2%}")
        
        dims = fused['dimensions']
        print(f"\n  融合四维分数:")
        print(f"    I/E: {dims['ie']:.4f} ({'E外向' if dims['ie'] > 0.5 else 'I内向'})")
        print(f"    N/S: {dims['ns']:.4f} ({'N直觉' if dims['ns'] > 0.5 else 'S实感'})")
        print(f"    T/F: {dims['tf']:.4f} ({'F情感' if dims['tf'] > 0.5 else 'T思考'})")
        print(f"    J/P: {dims['jp']:.4f} ({'J判断' if dims['jp'] > 0.5 else 'P感知'})")
        
        # 显示各时间维度细分
        print(f"\n  各时间维度性格:")
        for tf, details in result['timeframe_details'].items():
            print(f"    {tf.value:4s}: {details['mbti']} (置信度: {details['confidence']:.1%})")
        
        # 显示一致性分析
        consistency = result['consistency_analysis']
        print(f"\n  多周期一致性: {consistency['status']}")
        print(f"  建议: {consistency['recommendation']}")
        
        # 显示交易启示
        print(f"\n  交易启示:")
        for impl in result['trading_implications']:
            print(f"    {impl}")
        
        # 检查维度方差
        if 'dimension_variance' in consistency:
            print(f"\n  维度一致性分析:")
            for dim, var in consistency['dimension_variance'].items():
                print(f"    {dim.upper()}: {var['consistency']} (方差: {var['variance']:.4f})")
    
    print(f"\n{'='*80}")
    print("多时间维度分析演示完成!")
    print("=" * 80)
    print("\n💡 多维度优势:")
    print("  • 15分钟: 捕捉日内情绪和短期波动")
    print("  • 1小时: 识别日内趋势和支撑阻力")
    print("  • 4小时: 确认日间趋势方向")
    print("  • 1天: 判断长期结构和主要趋势")
    print("  • 融合分析: 检测多周期共振/背离，提高信号可靠性")


if __name__ == "__main__":
    demo_multi_timeframe()
