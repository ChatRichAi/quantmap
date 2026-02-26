"""
QuantClaw Pro - MBTI 股性分类系统
感知层 (Perception Layer) - 32维特征工程实现
Phase 1: Week 1-2
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


@dataclass
class FeatureVector:
    """特征向量输出结构"""
    ticker: str
    timestamp: datetime
    features: np.ndarray  # 32维标准化特征
    feature_dict: Dict[str, float]  # 具名特征字典
    confidence_score: float  # 数据质量置信度
    feature_categories: Dict[str, List[str]]  # 特征分类


class VolatilityFeatures:
    """波动特征提取器 - 8维"""
    
    @staticmethod
    def calculate(df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """
        计算波动特征
        
        Args:
            df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume']
            window: 计算窗口
            
        Returns:
            8维波动特征字典
        """
        features = {}
        returns = df['close'].pct_change().dropna()
        
        # 1. 年化波动率
        features['volatility_20d'] = returns.rolling(window).std().iloc[-1] * np.sqrt(252)
        
        # 2. ATR比率 (Average True Range)
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window).mean()
        features['atr_ratio'] = (atr / df['close']).iloc[-1]
        
        # 3. GARCH条件波动率 (简化实现)
        features['garch_vol'] = VolatilityFeatures._garch_estimate(returns, window)
        
        # 4. 波动率状态 (高/中/低)
        vol_percentile = stats.percentileofscore(
            returns.rolling(window).std().dropna(), 
            returns.rolling(window).std().iloc[-1]
        )
        features['vol_regime'] = vol_percentile / 100
        
        # 5. 平均日波幅
        daily_range = (df['high'] - df['low']) / df['close']
        features['max_daily_range'] = daily_range.rolling(window).mean().iloc[-1]
        
        # 6. 跳空频率
        features['gap_frequency'] = VolatilityFeatures._gap_frequency(df, window)
        
        # 7. 肥尾风险 (峰度)
        features['tail_risk'] = returns.rolling(window).kurt().iloc[-1] / 10  # 标准化
        
        # 8. 波动聚集性 (ARCH效应简化)
        features['vol_persistence'] = VolatilityFeatures._vol_clustering(returns, window)
        
        return features
    
    @staticmethod
    def _garch_estimate(returns: pd.Series, window: int) -> float:
        """GARCH(1,1) 简化估计"""
        try:
            var = returns.rolling(window).var().dropna()
            if len(var) < 2:
                return 0.5
            # 简化GARCH: 当前方差 = 0.1*长期方差 + 0.85*上期方差 + 0.05*上期收益平方
            long_term_var = var.mean()
            current_var = 0.1 * long_term_var + 0.85 * var.iloc[-1] + 0.05 * (returns.iloc[-1] ** 2)
            return min(np.sqrt(current_var) / np.sqrt(long_term_var), 2.0) / 2  # 标准化到0-1
        except:
            return 0.5
    
    @staticmethod
    def _gap_frequency(df: pd.Series, window: int) -> float:
        """计算跳空频率"""
        gaps = abs(df['open'] - df['close'].shift(1)) / df['close'].shift(1)
        gap_freq = (gaps > 0.02).rolling(window).mean().iloc[-1]  # 2%以上跳空
        return min(gap_freq * 5, 1.0)  # 标准化
    
    @staticmethod
    def _vol_clustering(returns: pd.Series, window: int) -> float:
        """波动聚集性 (ARCH效应)"""
        try:
            squared_returns = returns ** 2
            autocorr = squared_returns.rolling(window).apply(
                lambda x: x.autocorr(lag=1) if len(x) > 1 else 0
            ).iloc[-1]
            return (autocorr + 1) / 2  # 标准化到0-1
        except:
            return 0.5


class TrendFeatures:
    """趋势特征提取器 - 8维"""
    
    @staticmethod
    def calculate(df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """计算趋势特征"""
        features = {}
        
        # 1. ADX (Average Directional Index)
        features['adx'] = TrendFeatures._calculate_adx(df, window) / 100
        
        # 2. 价格斜率 (线性回归)
        features['trend_slope'] = TrendFeatures._linear_slope(df['close'], window)
        
        # 3. 均线排列得分
        features['ma_alignment'] = TrendFeatures._ma_alignment(df)
        
        # 4. 价格相对位置
        features['price_position'] = TrendFeatures._price_position(df, window)
        
        # 5. 趋势持续时间
        features['trend_duration'] = TrendFeatures._trend_duration(df, window)
        
        # 6. 方向一致性
        features['direction_consistency'] = TrendFeatures._direction_consistency(df, window)
        
        # 7. 突破频率
        features['breakout_frequency'] = TrendFeatures._breakout_frequency(df, window)
        
        # 8. 趋势效率
        features['trend_efficiency'] = TrendFeatures._trend_efficiency(df, window)
        
        return features
    
    @staticmethod
    def _calculate_adx(df: pd.DataFrame, period: int = 14) -> float:
        """计算ADX"""
        try:
            high, low, close = df['high'], df['low'], df['close']
            
            # +DM和-DM
            plus_dm = high.diff()
            minus_dm = -low.diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
            plus_dm[plus_dm <= minus_dm] = 0
            minus_dm[minus_dm <= plus_dm] = 0
            
            # TR
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # ATR
            atr = tr.rolling(period).mean()
            
            # +DI和-DI
            plus_di = 100 * plus_dm.rolling(period).mean() / atr
            minus_di = 100 * minus_dm.rolling(period).mean() / atr
            
            # DX和ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(period).mean()
            
            return adx.iloc[-1] if not pd.isna(adx.iloc[-1]) else 25
        except:
            return 25
    
    @staticmethod
    def _linear_slope(prices: pd.Series, window: int) -> float:
        """线性回归斜率"""
        try:
            y = prices.tail(window).values
            x = np.arange(len(y))
            slope, _, _, _, _ = stats.linregress(x, y)
            # 标准化: 斜率/价格 转换为年化百分比
            normalized_slope = slope * 252 / prices.iloc[-1]
            return np.clip(normalized_slope * 10 + 0.5, 0, 1)  # 标准化到0-1
        except:
            return 0.5
    
    @staticmethod
    def _ma_alignment(df: pd.DataFrame) -> float:
        """均线排列得分 (多头排列=1, 空头排列=0)"""
        try:
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            ma10 = df['close'].rolling(10).mean().iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma60 = df['close'].rolling(60).mean().iloc[-1]
            
            # 多头排列: MA5 > MA10 > MA20 > MA60
            score = 0
            if ma5 > ma10: score += 0.25
            if ma10 > ma20: score += 0.25
            if ma20 > ma60: score += 0.25
            if df['close'].iloc[-1] > ma5: score += 0.25
            
            return score
        except:
            return 0.5
    
    @staticmethod
    def _price_position(df: pd.DataFrame, window: int) -> float:
        """价格在近期区间的位置"""
        try:
            high_20d = df['high'].rolling(window).max().iloc[-1]
            low_20d = df['low'].rolling(window).min().iloc[-1]
            current = df['close'].iloc[-1]
            
            if high_20d == low_20d:
                return 0.5
            
            position = (current - low_20d) / (high_20d - low_20d)
            return np.clip(position, 0, 1)
        except:
            return 0.5
    
    @staticmethod
    def _trend_duration(df: pd.DataFrame, window: int) -> float:
        """当前趋势持续时间 (标准化)"""
        try:
            returns = df['close'].pct_change()
            direction = np.sign(returns.rolling(5).mean().iloc[-1])
            
            duration = 0
            for i in range(1, min(window, len(returns))):
                if np.sign(returns.iloc[-i]) == direction:
                    duration += 1
                else:
                    break
            
            return min(duration / 10, 1.0)  # 10天以上视为最大
        except:
            return 0.0
    
    @staticmethod
    def _direction_consistency(df: pd.DataFrame, window: int) -> float:
        """价格方向一致性"""
        try:
            returns = df['close'].pct_change().tail(window)
            positive_ratio = (returns > 0).sum() / len(returns)
            # 偏离0.5的程度表示一致性
            consistency = abs(positive_ratio - 0.5) * 2
            return consistency
        except:
            return 0.0
    
    @staticmethod
    def _breakout_frequency(df: pd.DataFrame, window: int) -> float:
        """突破频率"""
        try:
            # 计算布林带突破
            ma20 = df['close'].rolling(20).mean()
            std20 = df['close'].rolling(20).std()
            upper = ma20 + 2 * std20
            lower = ma20 - 2 * std20
            
            breakouts = ((df['close'] > upper) | (df['close'] < lower)).rolling(window).sum()
            return min(breakouts.iloc[-1] / 5, 1.0)  # 5次以上突破视为高频
        except:
            return 0.0
    
    @staticmethod
    def _trend_efficiency(df: pd.DataFrame, window: int) -> float:
        """趋势效率 (终点变动/总路程)"""
        try:
            prices = df['close'].tail(window)
            total_change = abs(prices.iloc[-1] - prices.iloc[0])
            total_distance = abs(prices.diff()).sum()
            
            if total_distance == 0:
                return 0.5
            
            efficiency = total_change / total_distance
            return np.clip(efficiency, 0, 1)
        except:
            return 0.5


class SentimentFeatures:
    """情绪特征提取器 - 8维"""
    
    @staticmethod
    def calculate(df: pd.DataFrame, flow_df: Optional[pd.DataFrame] = None, window: int = 20) -> Dict[str, float]:
        """
        计算情绪特征
        
        Args:
            df: 价格数据
            flow_df: 资金流向数据 (可选)
        """
        features = {}
        
        # 1. RSI极端值频率
        features['rsi_extreme_freq'] = SentimentFeatures._rsi_extreme_frequency(df, window)
        
        # 2. 量价相关系数
        features['volume_price_corr'] = SentimentFeatures._volume_price_correlation(df, window)
        
        # 3. 换手率分位数
        features['turnover_percentile'] = SentimentFeatures._turnover_percentile(df, window)
        
        # 4. 主力流入占比 (如果有资金流向数据)
        if flow_df is not None:
            features['fund_flow_ratio'] = SentimentFeatures._fund_flow_ratio(flow_df)
            features['retail_participation'] = SentimentFeatures._retail_participation(flow_df)
        else:
            features['fund_flow_ratio'] = 0.5
            features['retail_participation'] = 0.5
        
        # 5. 动量震荡
        features['momentum_oscillation'] = SentimentFeatures._momentum_oscillation(df, window)
        
        # 6. 恐惧贪婪指数
        features['fear_greed_index'] = SentimentFeatures._fear_greed_score(df, window)
        
        # 7. 羊群效应
        features['herding_effect'] = SentimentFeatures._herding_coefficient(df, window)
        
        # 8. 异常成交量 (补充特征)
        features['volume_anomaly'] = SentimentFeatures._volume_anomaly(df, window)
        
        return features
    
    @staticmethod
    def _rsi_extreme_frequency(df: pd.DataFrame, window: int) -> float:
        """RSI极端值频率"""
        try:
            # 计算RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 极端值 (>70或<30)
            extreme = ((rsi > 70) | (rsi < 30)).rolling(window).mean()
            return extreme.iloc[-1] if not pd.isna(extreme.iloc[-1]) else 0.0
        except:
            return 0.0
    
    @staticmethod
    def _volume_price_correlation(df: pd.DataFrame, window: int) -> float:
        """量价相关系数"""
        try:
            price_change = df['close'].pct_change()
            volume = df['volume']
            corr = price_change.rolling(window).corr(volume).iloc[-1]
            return (corr + 1) / 2 if not pd.isna(corr) else 0.5  # 标准化到0-1
        except:
            return 0.5
    
    @staticmethod
    def _turnover_percentile(df: pd.DataFrame, window: int) -> float:
        """换手率分位数 (如果数据中有volume和market_cap)"""
        try:
            # 简化: 使用成交量的历史分位
            vol_percentile = stats.percentileofscore(
                df['volume'].tail(window * 3),
                df['volume'].iloc[-1]
            )
            return vol_percentile / 100
        except:
            return 0.5
    
    @staticmethod
    def _fund_flow_ratio(flow_df: pd.DataFrame) -> float:
        """主力流入占比"""
        try:
            # 假设flow_df有'main_inflow'和'total_inflow'列
            if 'main_inflow' in flow_df.columns and 'total_inflow' in flow_df.columns:
                ratio = flow_df['main_inflow'].iloc[-1] / flow_df['total_inflow'].iloc[-1]
                return np.clip((ratio + 1) / 2, 0, 1)  # 标准化
            return 0.5
        except:
            return 0.5
    
    @staticmethod
    def _retail_participation(flow_df: pd.DataFrame) -> float:
        """散户参与度"""
        try:
            if 'retail_inflow' in flow_df.columns and 'total_inflow' in flow_df.columns:
                ratio = flow_df['retail_inflow'].iloc[-1] / flow_df['total_inflow'].iloc[-1]
                return np.clip(ratio, 0, 1)
            return 0.5
        except:
            return 0.5
    
    @staticmethod
    def _momentum_oscillation(df: pd.DataFrame, window: int) -> float:
        """动量震荡程度"""
        try:
            returns = df['close'].pct_change().tail(window)
            # 动量变化的标准差
            momentum_change = returns.diff().std()
            return np.clip(momentum_change * 10, 0, 1)
        except:
            return 0.5
    
    @staticmethod
    def _fear_greed_score(df: pd.DataFrame, window: int) -> float:
        """恐惧贪婪指数 (0=极度恐惧, 1=极度贪婪)"""
        try:
            # 基于RSI、价格位置、动量的综合指标
            rsi = SentimentFeatures._calculate_rsi(df)
            price_pos = TrendFeatures._price_position(df, window)
            
            # 综合评分
            score = (rsi / 100 * 0.4 + price_pos * 0.6)
            return score
        except:
            return 0.5
    
    @staticmethod
    def _calculate_rsi(df: pd.DataFrame, period: int = 14) -> float:
        """计算RSI"""
        try:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        except:
            return 50
    
    @staticmethod
    def _herding_coefficient(df: pd.DataFrame, window: int) -> float:
        """羊群效应系数"""
        try:
            # 基于收益率的横截面相关性简化计算
            returns = df['close'].pct_change().tail(window)
            # 高波动 + 高成交量 = 可能的羊群行为
            vol = returns.std()
            volume_spike = df['volume'].iloc[-1] / df['volume'].rolling(window).mean().iloc[-1]
            
            herding = min(vol * 10 * (volume_spike - 1), 1.0) if volume_spike > 1 else 0
            return max(herding, 0)
        except:
            return 0.0
    
    @staticmethod
    def _volume_anomaly(df: pd.DataFrame, window: int) -> float:
        """成交量异常"""
        try:
            vol_ma = df['volume'].rolling(window).mean().iloc[-1]
            vol_std = df['volume'].rolling(window).std().iloc[-1]
            current_vol = df['volume'].iloc[-1]
            
            if vol_std == 0:
                return 0.0
            
            z_score = (current_vol - vol_ma) / vol_std
            return np.clip(abs(z_score) / 3, 0, 1)  # 3个标准差视为最大异常
        except:
            return 0.0


class StructureFeatures:
    """结构特征提取器 - 8维"""
    
    @staticmethod
    def calculate(df: pd.DataFrame, market_index: Optional[pd.Series] = None, window: int = 20) -> Dict[str, float]:
        """计算结构特征"""
        features = {}
        
        # 1. 支撑位距离
        features['support_distance'] = StructureFeatures._support_distance(df, window)
        
        # 2. 阻力位距离
        features['resistance_distance'] = StructureFeatures._resistance_distance(df, window)
        
        # 3. 通道宽度
        features['channel_width'] = StructureFeatures._channel_width(df, window)
        
        # 4. 盘整时间占比
        features['consolidation_ratio'] = StructureFeatures._consolidation_ratio(df, window)
        
        # 5. 形态复杂度
        features['pattern_complexity'] = StructureFeatures._pattern_complexity(df, window)
        
        # 6. 分形维度
        features['fractal_dimension'] = StructureFeatures._fractal_dimension(df['close'])
        
        # 7. 赫斯特指数
        features['hurst_exponent'] = StructureFeatures._hurst_exponent(df['close'], window)
        
        # 8. 市场相关性 (Beta)
        if market_index is not None:
            features['market_correlation'] = StructureFeatures._market_correlation(df, market_index, window)
        else:
            features['market_correlation'] = 0.5
        
        return features
    
    @staticmethod
    def _support_distance(df: pd.DataFrame, window: int) -> float:
        """距离最近支撑位的距离"""
        try:
            # 简化: 使用近期低点作为支撑
            recent_lows = df['low'].tail(window).nsmallest(3)
            nearest_support = recent_lows.mean()
            current = df['close'].iloc[-1]
            
            distance = (current - nearest_support) / current
            return np.clip(distance * 5, 0, 1)  # 标准化
        except:
            return 0.5
    
    @staticmethod
    def _resistance_distance(df: pd.DataFrame, window: int) -> float:
        """距离最近阻力位的距离"""
        try:
            # 简化: 使用近期高点作为阻力
            recent_highs = df['high'].tail(window).nlargest(3)
            nearest_resistance = recent_highs.mean()
            current = df['close'].iloc[-1]
            
            distance = (nearest_resistance - current) / current
            return np.clip(distance * 5, 0, 1)  # 标准化
        except:
            return 0.5
    
    @staticmethod
    def _channel_width(df: pd.DataFrame, window: int) -> float:
        """价格波动通道宽度"""
        try:
            high_max = df['high'].tail(window).max()
            low_min = df['low'].tail(window).min()
            current = df['close'].iloc[-1]
            
            width = (high_max - low_min) / current
            return np.clip(width * 2, 0, 1)  # 标准化
        except:
            return 0.5
    
    @staticmethod
    def _consolidation_ratio(df: pd.DataFrame, window: int) -> float:
        """盘整时间占比 (价格在5%区间内波动)"""
        try:
            prices = df['close'].tail(window)
            price_range = (prices.max() - prices.min()) / prices.mean()
            
            # 小于5%波动视为盘整
            if price_range < 0.05:
                return 1.0
            
            # 计算在5%区间内的天数
            in_range = (abs(prices.pct_change()) < 0.02).sum()
            return in_range / len(prices)
        except:
            return 0.5
    
    @staticmethod
    def _pattern_complexity(df: pd.DataFrame, window: int) -> float:
        """价格形态复杂度"""
        try:
            # 使用价格转折点的数量衡量复杂度
            prices = df['close'].tail(window)
            diff = prices.diff()
            
            # 计算方向变化的次数
            direction_changes = ((diff > 0) != (diff.shift(1) > 0)).sum()
            complexity = direction_changes / (window / 5)  # 平均每5天一次转向为中等复杂
            
            return np.clip(complexity / 2, 0, 1)
        except:
            return 0.5
    
    @staticmethod
    def _fractal_dimension(prices: pd.Series, max_lag: int = 20) -> float:
        """Higuchi分形维度估计"""
        try:
            # 简化实现
            lags = range(2, min(max_lag, len(prices) // 4))
            tau = [np.std(np.subtract(prices[lag:], prices[:-lag])) for lag in lags]
            
            if len(tau) < 2 or any(t == 0 for t in tau):
                return 0.5
            
            # 线性拟合估计Hurst指数
            log_lags = np.log(list(lags))
            log_tau = np.log(tau)
            
            slope, _, _, _, _ = stats.linregress(log_lags, log_tau)
            hurst = -slope
            
            # 分形维度 = 2 - Hurst
            fractal_dim = 2 - hurst
            return np.clip((fractal_dim - 1) / 1.5, 0, 1)  # 标准化到0-1
        except:
            return 0.5
    
    @staticmethod
    def _hurst_exponent(prices: pd.Series, window: int) -> float:
        """赫斯特指数 (R/S分析简化)"""
        try:
            returns = prices.pct_change().dropna().tail(window)
            
            if len(returns) < 10:
                return 0.5
            
            # R/S分析
            mean_return = returns.mean()
            cumsum = (returns - mean_return).cumsum()
            R = cumsum.max() - cumsum.min()
            S = returns.std()
            
            if S == 0:
                return 0.5
            
            RS = R / S
            hurst = np.log(RS) / np.log(len(returns))
            
            return np.clip(hurst, 0, 1)
        except:
            return 0.5
    
    @staticmethod
    def _market_correlation(df: pd.DataFrame, market_index: pd.Series, window: int) -> float:
        """与市场指数的相关性 (Beta)"""
        try:
            stock_returns = df['close'].pct_change().tail(window)
            market_returns = market_index.pct_change().tail(window)
            
            corr = stock_returns.corr(market_returns)
            return (corr + 1) / 2 if not pd.isna(corr) else 0.5  # 标准化到0-1
        except:
            return 0.5


class PerceptionLayer:
    """
    感知层: 整合所有特征提取器，输出32维标准化特征向量
    """
    
    def __init__(self):
        self.volatility_extractor = VolatilityFeatures()
        self.trend_extractor = TrendFeatures()
        self.sentiment_extractor = SentimentFeatures()
        self.structure_extractor = StructureFeatures()
        
        # 特征名称列表
        self.feature_names = (
            ['volatility_20d', 'atr_ratio', 'garch_vol', 'vol_regime', 
             'max_daily_range', 'gap_frequency', 'tail_risk', 'vol_persistence'] +
            ['adx', 'trend_slope', 'ma_alignment', 'price_position',
             'trend_duration', 'direction_consistency', 'breakout_frequency', 'trend_efficiency'] +
            ['rsi_extreme_freq', 'volume_price_corr', 'turnover_percentile', 'fund_flow_ratio',
             'retail_participation', 'momentum_oscillation', 'fear_greed_index', 'herding_effect'] +
            ['support_distance', 'resistance_distance', 'channel_width', 'consolidation_ratio',
             'pattern_complexity', 'fractal_dimension', 'hurst_exponent', 'market_correlation']
        )
    
    def extract_features(self, 
                        ticker: str,
                        df: pd.DataFrame, 
                        flow_df: Optional[pd.DataFrame] = None,
                        market_index: Optional[pd.Series] = None,
                        window: int = 20) -> FeatureVector:
        """
        提取完整的32维特征向量
        
        Args:
            ticker: 股票代码
            df: OHLCV数据
            flow_df: 资金流向数据 (可选)
            market_index: 市场指数数据 (可选)
            window: 计算窗口
            
        Returns:
            FeatureVector对象
        """
        # 确保数据足够
        if len(df) < window + 10:
            raise ValueError(f"数据不足，需要至少 {window + 10} 条记录")
        
        # 提取各类特征
        vol_features = self.volatility_extractor.calculate(df, window)
        trend_features = self.trend_extractor.calculate(df, window)
        sentiment_features = self.sentiment_extractor.calculate(df, flow_df, window)
        structure_features = self.structure_extractor.calculate(df, market_index, window)
        
        # 合并所有特征
        all_features = {}
        all_features.update(vol_features)
        all_features.update(trend_features)
        all_features.update(sentiment_features)
        all_features.update(structure_features)
        
        # 构建特征向量
        feature_vector = np.array([all_features.get(name, 0.5) for name in self.feature_names])
        
        # 处理异常值
        feature_vector = np.clip(feature_vector, 0, 1)
        
        # 计算数据质量置信度
        confidence = self._calculate_confidence(df, feature_vector)
        
        # 特征分类
        feature_categories = {
            'volatility': list(vol_features.keys()),
            'trend': list(trend_features.keys()),
            'sentiment': list(sentiment_features.keys()),
            'structure': list(structure_features.keys())
        }
        
        return FeatureVector(
            ticker=ticker,
            timestamp=datetime.now(),
            features=feature_vector,
            feature_dict=all_features,
            confidence_score=confidence,
            feature_categories=feature_categories
        )
    
    def _calculate_confidence(self, df: pd.DataFrame, features: np.ndarray) -> float:
        """计算数据质量置信度"""
        confidence_factors = []
        
        # 1. 数据完整性
        completeness = 1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
        confidence_factors.append(completeness)
        
        # 2. 特征值分布正常性 (避免太多极端值)
        extreme_ratio = np.mean((features < 0.05) | (features > 0.95))
        confidence_factors.append(1 - extreme_ratio)
        
        # 3. 数据长度充足性
        length_score = min(len(df) / 60, 1.0)  # 60天视为充足
        confidence_factors.append(length_score)
        
        # 4. 特征间相关性合理性 (避免所有特征都相同)
        feature_variance = np.std(features)
        confidence_factors.append(min(feature_variance * 5, 1.0))
        
        return np.mean(confidence_factors)
    
    def batch_extract(self, 
                     data_dict: Dict[str, pd.DataFrame],
                     flow_dict: Optional[Dict[str, pd.DataFrame]] = None,
                     market_index: Optional[pd.Series] = None,
                     window: int = 20) -> Dict[str, FeatureVector]:
        """
        批量提取特征
        
        Args:
            data_dict: {ticker: df} 字典
            flow_dict: {ticker: flow_df} 字典 (可选)
            market_index: 市场指数
            window: 计算窗口
            
        Returns:
            {ticker: FeatureVector} 字典
        """
        results = {}
        flow_dict = flow_dict or {}
        
        for ticker, df in data_dict.items():
            try:
                flow_df = flow_dict.get(ticker)
                feature_vector = self.extract_features(ticker, df, flow_df, market_index, window)
                results[ticker] = feature_vector
            except Exception as e:
                print(f"提取 {ticker} 特征失败: {e}")
                continue
        
        return results


# ==================== 测试代码 ====================

if __name__ == "__main__":
    # 生成测试数据
    np.random.seed(42)
    n_days = 100
    
    # 模拟价格数据
    dates = pd.date_range(end='2024-01-01', periods=n_days, freq='D')
    returns = np.random.normal(0.001, 0.02, n_days)
    prices = 100 * np.exp(np.cumsum(returns))
    
    test_df = pd.DataFrame({
        'open': prices * (1 + np.random.normal(0, 0.005, n_days)),
        'high': prices * (1 + abs(np.random.normal(0, 0.01, n_days))),
        'low': prices * (1 - abs(np.random.normal(0, 0.01, n_days))),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n_days)
    }, index=dates)
    
    # 测试特征提取
    perception = PerceptionLayer()
    
    print("=" * 60)
    print("QuantClaw Pro - 感知层特征提取测试")
    print("=" * 60)
    
    feature_vector = perception.extract_features("TEST", test_df)
    
    print(f"\n股票代码: {feature_vector.ticker}")
    print(f"提取时间: {feature_vector.timestamp}")
    print(f"数据置信度: {feature_vector.confidence_score:.2%}")
    print(f"\n特征向量维度: {len(feature_vector.features)}")
    print(f"特征向量范围: [{feature_vector.features.min():.3f}, {feature_vector.features.max():.3f}]")
    
    print("\n" + "-" * 60)
    print("各类特征统计:")
    print("-" * 60)
    
    for category, feature_list in feature_vector.feature_categories.items():
        print(f"\n【{category.upper()}】({len(feature_list)}维)")
        for feat_name in feature_list[:4]:  # 只显示前4个
            value = feature_vector.feature_dict.get(feat_name, 0)
            print(f"  {feat_name:25s}: {value:.4f}")
        if len(feature_list) > 4:
            print(f"  ... 等共 {len(feature_list)} 个特征")
    
    print("\n" + "=" * 60)
    print("特征提取完成!")
    print("=" * 60)
