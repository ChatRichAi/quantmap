"""
QuantClaw Pro - MBTI 股性分类系统
决策层 (Decision Layer) - 策略匹配引擎
Phase 3: Week 5-6

根据股性档案匹配合适的交易策略，生成具体交易指令
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """市场环境枚举"""
    BULL = "bull"           # 牛市
    BEAR = "bear"           # 熊市
    SIDEWAYS = "sideways"   # 震荡市
    HIGH_VOL = "high_vol"   # 高波动
    LOW_VOL = "low_vol"     # 低波动


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    REDUCE = "reduce"


@dataclass
class StrategyParameters:
    """策略参数配置"""
    entry_conditions: Dict[str, Any]      # 入场条件
    exit_conditions: Dict[str, Any]       # 出场条件
    stop_loss: float                      # 止损比例
    take_profit: float                    # 止盈比例
    trailing_stop: Optional[float]        # 移动止损
    position_size: float                  # 仓位比例
    max_holding_days: int                 # 最大持有天数
    min_holding_days: int                 # 最小持有天数


@dataclass
class TradingSignal:
    """交易信号"""
    ticker: str
    signal_type: SignalType
    strategy_name: str
    confidence: float
    timestamp: datetime
    entry_price: Optional[float]          # 建议入场价格
    stop_loss_price: Optional[float]      # 止损价格
    take_profit_price: Optional[float]    # 止盈价格
    position_size: float                  # 建议仓位
    reason: str                           # 信号原因
    metadata: Dict[str, Any]              # 附加信息
    
    def to_dict(self) -> Dict:
        return {
            'ticker': self.ticker,
            'signal': self.signal_type.value,
            'strategy': self.strategy_name,
            'confidence': round(self.confidence, 4),
            'timestamp': self.timestamp.isoformat(),
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss_price,
            'take_profit': self.take_profit_price,
            'position_size': round(self.position_size, 2),
            'reason': self.reason,
            'metadata': self.metadata
        }


@dataclass
class StrategyRecommendation:
    """策略推荐"""
    strategy_name: str
    strategy_type: str
    weight: float
    compatibility_score: float
    expected_return: float
    risk_level: str
    parameters: StrategyParameters
    description: str


class StrategyLibrary:
    """
    策略库
    包含所有可用的交易策略及其参数配置
    """
    
    STRATEGIES = {
        # ========== 趋势跟踪类 ==========
        'trend_following': {
            'name': '趋势跟踪策略',
            'type': 'trend',
            'description': '跟随市场趋势进行交易，MA多头排列时入场',
            'base_params': {
                'entry_conditions': {
                    'ma_alignment': True,
                    'adx_threshold': 25,
                    'volume_spike': 1.3
                },
                'exit_conditions': {
                    'trend_break': True,
                    'ma_cross_down': True
                },
                'stop_loss': 0.10,
                'take_profit': 0.25,
                'trailing_stop': 0.08,
                'position_size': 1.0,
                'max_holding_days': 60,
                'min_holding_days': 5
            }
        },
        
        'momentum': {
            'name': '动量策略',
            'type': 'momentum',
            'description': '追涨强势股，利用价格动量',
            'base_params': {
                'entry_conditions': {
                    'price_breakout': True,
                    'volume_expansion': 1.5,
                    'rsi_range': [50, 70]
                },
                'exit_conditions': {
                    'momentum_decay': True,
                    'rsi_overbought': 75
                },
                'stop_loss': 0.08,
                'take_profit': 0.20,
                'trailing_stop': 0.06,
                'position_size': 0.8,
                'max_holding_days': 30,
                'min_holding_days': 3
            }
        },
        
        'breakout': {
            'name': '突破策略',
            'type': 'breakout',
            'description': '突破关键阻力位时入场',
            'base_params': {
                'entry_conditions': {
                    'resistance_break': True,
                    'volume_confirmation': 2.0,
                    'consolidation_before': True
                },
                'exit_conditions': {
                    'false_breakout': True,
                    'target_reached': True
                },
                'stop_loss': 0.06,
                'take_profit': 0.15,
                'trailing_stop': None,
                'position_size': 0.7,
                'max_holding_days': 20,
                'min_holding_days': 2
            }
        },
        
        # ========== 均值回归类 ==========
        'mean_reversion': {
            'name': '均值回归策略',
            'type': 'reversion',
            'description': '价格偏离均值时反向操作',
            'base_params': {
                'entry_conditions': {
                    'price_deviation': 2.0,  # 2个标准差
                    'rsi_extreme': True,
                    'oversold': True
                },
                'exit_conditions': {
                    'mean_reached': True,
                    'time_decay': 10
                },
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'trailing_stop': None,
                'position_size': 0.6,
                'max_holding_days': 15,
                'min_holding_days': 2
            }
        },
        
        # ========== 价值投资类 ==========
        'value': {
            'name': '价值投资策略',
            'type': 'value',
            'description': '买入低估股票，长期持有',
            'base_params': {
                'entry_conditions': {
                    'pe_low': True,
                    'pb_low': True,
                    'dividend_yield': 0.03
                },
                'exit_conditions': {
                    'valuation_recover': True,
                    'fundamental_change': True
                },
                'stop_loss': 0.15,
                'take_profit': 0.50,
                'trailing_stop': None,
                'position_size': 1.2,
                'max_holding_days': 252,  # 1年
                'min_holding_days': 63    # 3个月
            }
        },
        
        'dca': {
            'name': '定投策略',
            'type': 'dca',
            'description': '定期定额投资，分散风险',
            'base_params': {
                'entry_conditions': {
                    'time_based': True,
                    'fixed_amount': True
                },
                'exit_conditions': {
                    'long_term_target': True
                },
                'stop_loss': None,
                'take_profit': None,
                'trailing_stop': None,
                'position_size': 0.3,
                'max_holding_days': 504,  # 2年
                'min_holding_days': 126   # 6个月
            }
        },
        
        # ========== 事件驱动类 ==========
        'event_driven': {
            'name': '事件驱动策略',
            'type': 'event',
            'description': '利用重大事件带来的价格波动',
            'base_params': {
                'entry_conditions': {
                    'earnings_surprise': True,
                    'news_sentiment': 'positive',
                    'volume_spike': 3.0
                },
                'exit_conditions': {
                    'event_priced_in': True,
                    'time_decay': 5
                },
                'stop_loss': 0.06,
                'take_profit': 0.12,
                'trailing_stop': None,
                'position_size': 0.5,
                'max_holding_days': 10,
                'min_holding_days': 1
            }
        },
        
        # ========== 技术策略类 ==========
        'technical_breakout': {
            'name': '技术突破策略',
            'type': 'technical',
            'description': '基于技术指标突破入场',
            'base_params': {
                'entry_conditions': {
                    'macd_golden_cross': True,
                    'rsi_breakout': True,
                    'volume_confirmation': 1.5
                },
                'exit_conditions': {
                    'macd_dead_cross': True,
                    'rsi_divergence': True
                },
                'stop_loss': 0.07,
                'take_profit': 0.18,
                'trailing_stop': 0.05,
                'position_size': 0.8,
                'max_holding_days': 25,
                'min_holding_days': 3
            }
        },
        
        # ========== 高频/短线类 ==========
        'swing_trading': {
            'name': '波段交易策略',
            'type': 'swing',
            'description': '捕捉短期波段机会',
            'base_params': {
                'entry_conditions': {
                    'support_bounce': True,
                    'short_term_momentum': True
                },
                'exit_conditions': {
                    'resistance_hit': True,
                    'momentum_fade': True
                },
                'stop_loss': 0.05,
                'take_profit': 0.10,
                'trailing_stop': 0.03,
                'position_size': 0.6,
                'max_holding_days': 10,
                'min_holding_days': 2
            }
        },
        
        'contrarian': {
            'name': '逆向投资策略',
            'type': 'contrarian',
            'description': '与市场情绪反向操作',
            'base_params': {
                'entry_conditions': {
                    'extreme_fear': True,
                    'rsi_oversold': 30,
                    'volume_climax': True
                },
                'exit_conditions': {
                    'sentiment_normalize': True,
                    'profit_target': 0.15
                },
                'stop_loss': 0.08,
                'take_profit': 0.20,
                'trailing_stop': None,
                'position_size': 0.7,
                'max_holding_days': 45,
                'min_holding_days': 10
            }
        }
    }
    
    # MBTI类型到策略的映射（性格-策略兼容性矩阵）
    MBTI_STRATEGY_MAPPING = {
        'INTJ': ['trend_following', 'momentum', 'breakout'],
        'INTP': ['technical_breakout', 'mean_reversion', 'event_driven'],
        'ENTJ': ['value', 'trend_following', 'dca'],
        'ENTP': ['event_driven', 'contrarian', 'swing_trading'],
        'INFJ': ['contrarian', 'value', 'mean_reversion'],
        'INFP': ['event_driven', 'momentum', 'swing_trading'],
        'ENFJ': ['trend_following', 'momentum', 'breakout'],
        'ENFP': ['momentum', 'breakout', 'event_driven'],
        'ISTJ': ['value', 'dca', 'trend_following'],
        'ISFJ': ['value', 'dca', 'contrarian'],
        'ESTJ': ['trend_following', 'value', 'dca'],
        'ESFJ': ['trend_following', 'dca', 'value'],
        'ISTP': ['swing_trading', 'technical_breakout', 'mean_reversion'],
        'ISFP': ['mean_reversion', 'swing_trading', 'contrarian'],
        'ESTP': ['swing_trading', 'breakout', 'momentum'],
        'ESFP': ['event_driven', 'momentum', 'swing_trading']
    }
    
    # 市场环境对策略的影响系数
    REGIME_ADJUSTMENTS = {
        MarketRegime.BULL: {
            'trend_following': 1.3,
            'momentum': 1.4,
            'breakout': 1.2,
            'value': 1.0,
            'contrarian': 0.7,
            'mean_reversion': 0.8
        },
        MarketRegime.BEAR: {
            'trend_following': 0.7,
            'momentum': 0.6,
            'breakout': 0.8,
            'value': 1.2,
            'contrarian': 1.4,
            'mean_reversion': 1.1
        },
        MarketRegime.SIDEWAYS: {
            'trend_following': 0.8,
            'momentum': 0.9,
            'breakout': 0.9,
            'value': 1.0,
            'contrarian': 1.1,
            'mean_reversion': 1.3
        },
        MarketRegime.HIGH_VOL: {
            'trend_following': 0.9,
            'momentum': 1.1,
            'breakout': 1.3,
            'value': 0.8,
            'contrarian': 1.2,
            'mean_reversion': 1.1
        },
        MarketRegime.LOW_VOL: {
            'trend_following': 1.1,
            'momentum': 0.9,
            'breakout': 0.8,
            'value': 1.1,
            'contrarian': 0.9,
            'mean_reversion': 0.9
        }
    }
    
    @classmethod
    def get_strategy(cls, strategy_id: str) -> Optional[Dict]:
        """获取策略配置"""
        return cls.STRATEGIES.get(strategy_id)
    
    @classmethod
    def get_strategies_for_mbti(cls, mbti_type: str) -> List[str]:
        """获取MBTI类型推荐的策略列表"""
        return cls.MBTI_STRATEGY_MAPPING.get(mbti_type, ['trend_following'])
    
    @classmethod
    def adjust_for_regime(cls, strategy_id: str, regime: MarketRegime) -> float:
        """获取市场环境对策略的影响系数"""
        adjustments = cls.REGIME_ADJUSTMENTS.get(regime, {})
        return adjustments.get(strategy_id, 1.0)


class StrategyMatcher:
    """
    策略匹配器
    根据股性档案和市场环境匹配最佳策略
    """
    
    def __init__(self):
        self.strategy_lib = StrategyLibrary()
    
    def match_strategies(self, 
                        mbti_type: str,
                        dimension_scores: Dict[str, float],
                        market_regime: MarketRegime = MarketRegime.SIDEWAYS,
                        top_n: int = 3) -> List[StrategyRecommendation]:
        """
        匹配策略
        
        Args:
            mbti_type: MBTI类型代码
            dimension_scores: 四维分数
            market_regime: 市场环境
            top_n: 返回前N个策略
            
        Returns:
            策略推荐列表
        """
        # 获取该MBTI类型兼容的策略
        compatible_strategies = self.strategy_lib.get_strategies_for_mbti(mbti_type)
        
        recommendations = []
        
        for strategy_id in compatible_strategies:
            strategy_info = self.strategy_lib.get_strategy(strategy_id)
            if not strategy_info:
                continue
            
            # 计算兼容性得分
            base_compatibility = self._calculate_compatibility(
                mbti_type, strategy_id, dimension_scores
            )
            
            # 根据市场环境调整
            regime_adjustment = self.strategy_lib.adjust_for_regime(strategy_id, market_regime)
            adjusted_score = base_compatibility * regime_adjustment
            
            # 获取策略参数
            base_params = strategy_info['base_params'].copy()
            
            # 根据风险等级调整仓位
            risk_level = self._get_risk_level(mbti_type)
            position_adjustment = self._adjust_position_for_risk(risk_level)
            base_params['position_size'] *= position_adjustment
            
            recommendation = StrategyRecommendation(
                strategy_name=strategy_info['name'],
                strategy_type=strategy_info['type'],
                weight=0.0,  # 稍后计算
                compatibility_score=adjusted_score,
                expected_return=self._estimate_return(strategy_id, adjusted_score),
                risk_level=risk_level,
                parameters=StrategyParameters(**base_params),
                description=strategy_info['description']
            )
            
            recommendations.append(recommendation)
        
        # 按兼容性得分排序
        recommendations.sort(key=lambda x: x.compatibility_score, reverse=True)
        
        # 计算权重（归一化）
        if recommendations:
            total_score = sum(r.compatibility_score for r in recommendations[:top_n])
            for rec in recommendations[:top_n]:
                rec.weight = rec.compatibility_score / total_score if total_score > 0 else 0
        
        return recommendations[:top_n]
    
    def _calculate_compatibility(self, mbti_type: str, strategy_id: str, 
                                 dimension_scores: Dict[str, float]) -> float:
        """计算性格-策略兼容性得分"""
        
        # 基础兼容性（基于MBTI-策略映射）
        compatible_strategies = self.strategy_lib.get_strategies_for_mbti(mbti_type)
        if strategy_id in compatible_strategies:
            base_score = 0.7
            # 排名越靠前，得分越高
            rank = compatible_strategies.index(strategy_id)
            base_score += (2 - rank) * 0.1  # 第一名+0.2, 第二名+0.1
        else:
            base_score = 0.3
        
        # 根据四维分数微调
        ie = dimension_scores.get('ie', 0.5)
        ns = dimension_scores.get('ns', 0.5)
        tf = dimension_scores.get('tf', 0.5)
        jp = dimension_scores.get('jp', 0.5)
        
        # 策略特定的维度偏好
        dimension_bonus = 0.0
        
        if strategy_id == 'trend_following':
            dimension_bonus = (ns - 0.5) * 0.1 + (jp - 0.5) * 0.1  # 偏好N和J
        elif strategy_id == 'mean_reversion':
            dimension_bonus = (0.5 - ns) * 0.1  # 偏好S
        elif strategy_id == 'momentum':
            dimension_bonus = (ns - 0.5) * 0.15 + (ie - 0.5) * 0.05  # 偏好N和E
        elif strategy_id == 'contrarian':
            dimension_bonus = (0.5 - ie) * 0.1 + (0.5 - tf) * 0.1  # 偏好I和T
        elif strategy_id == 'value':
            dimension_bonus = (0.5 - ie) * 0.1 + (jp - 0.5) * 0.1  # 偏好I和J
        
        return min(base_score + dimension_bonus, 1.0)
    
    def _get_risk_level(self, mbti_type: str) -> str:
        """获取MBTI类型的风险等级"""
        risk_map = {
            'INTJ': 'High', 'INTP': 'High', 'ENTJ': 'Medium', 'ENTP': 'High',
            'INFJ': 'High', 'INFP': 'Extreme', 'ENFJ': 'Medium', 'ENFP': 'High',
            'ISTJ': 'Low', 'ISFJ': 'Low', 'ESTJ': 'Medium', 'ESFJ': 'Medium',
            'ISTP': 'High', 'ISFP': 'Extreme', 'ESTP': 'Extreme', 'ESFP': 'Extreme'
        }
        return risk_map.get(mbti_type, 'Medium')
    
    def _adjust_position_for_risk(self, risk_level: str) -> float:
        """根据风险等级调整仓位"""
        adjustments = {
            'Low': 1.3,
            'Medium': 1.0,
            'High': 0.8,
            'Extreme': 0.6
        }
        return adjustments.get(risk_level, 1.0)
    
    def _estimate_return(self, strategy_id: str, compatibility: float) -> float:
        """估算预期收益（简化版）"""
        base_returns = {
            'trend_following': 0.15,
            'momentum': 0.18,
            'breakout': 0.12,
            'mean_reversion': 0.08,
            'value': 0.12,
            'dca': 0.10,
            'event_driven': 0.15,
            'technical_breakout': 0.14,
            'swing_trading': 0.10,
            'contrarian': 0.18
        }
        base = base_returns.get(strategy_id, 0.10)
        # 兼容性越高，预期收益越高
        return base * (0.8 + compatibility * 0.4)


class DecisionLayer:
    """
    决策层
    整合策略匹配和信号生成，输出最终交易决策
    """
    
    def __init__(self):
        self.matcher = StrategyMatcher()
        self.last_signals: Dict[str, datetime] = {}  # 记录上次信号时间
    
    def make_decision(self,
                     ticker: str,
                     mbti_type: str,
                     dimension_scores: Dict[str, float],
                     current_price: float,
                     market_data: Dict[str, Any],
                     market_regime: MarketRegime = MarketRegime.SIDEWAYS,
                     portfolio: Optional[Dict] = None) -> Dict[str, Any]:
        """
        生成交易决策
        
        Args:
            ticker: 股票代码
            mbti_type: MBTI类型
            dimension_scores: 四维分数
            current_price: 当前价格
            market_data: 市场数据
            market_regime: 市场环境
            portfolio: 当前持仓信息
            
        Returns:
            完整决策报告
        """
        # 匹配策略
        recommendations = self.matcher.match_strategies(
            mbti_type, dimension_scores, market_regime, top_n=3
        )
        
        # 生成交易信号
        signals = []
        for rec in recommendations:
            signal = self._generate_signal(
                ticker, rec, current_price, market_data, portfolio
            )
            if signal:
                signals.append(signal)
        
        # 构建决策报告
        decision = {
            'ticker': ticker,
            'timestamp': datetime.now(),
            'mbti_type': mbti_type,
            'market_regime': market_regime.value,
            'recommended_strategies': [
                {
                    'name': rec.strategy_name,
                    'weight': round(rec.weight, 4),
                    'compatibility': round(rec.compatibility_score, 4),
                    'expected_return': round(rec.expected_return, 4),
                    'risk_level': rec.risk_level,
                    'parameters': asdict(rec.parameters)
                }
                for rec in recommendations
            ],
            'trading_signals': [s.to_dict() for s in signals],
            'composite_signal': self._compute_composite_signal(signals),
            'risk_management': self._generate_risk_management(
                recommendations, current_price
            )
        }
        
        return decision
    
    def _generate_signal(self,
                        ticker: str,
                        recommendation: StrategyRecommendation,
                        current_price: float,
                        market_data: Dict[str, Any],
                        portfolio: Optional[Dict]) -> Optional[TradingSignal]:
        """生成单个交易信号"""
        
        params = recommendation.parameters
        
        # 检查入场条件（简化版，实际应更复杂）
        should_enter = self._check_entry_conditions(
            recommendation.strategy_type, market_data, params.entry_conditions
        )
        
        if not should_enter:
            return None
        
        # 检查是否已有持仓
        if portfolio and portfolio.get('position', 0) > 0:
            return None
        
        # 检查信号冷却期
        if ticker in self.last_signals:
            time_since_last = datetime.now() - self.last_signals[ticker]
            if time_since_last < timedelta(hours=24):
                return None
        
        # 计算具体价格
        entry_price = current_price
        stop_loss_price = entry_price * (1 - params.stop_loss) if params.stop_loss else None
        take_profit_price = entry_price * (1 + params.take_profit) if params.take_profit else None
        
        # 确定信号类型
        signal_type = SignalType.BUY
        
        signal = TradingSignal(
            ticker=ticker,
            signal_type=signal_type,
            strategy_name=recommendation.strategy_name,
            confidence=recommendation.compatibility_score,
            timestamp=datetime.now(),
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price,
            position_size=params.position_size,
            reason=f"基于{recommendation.strategy_name}的入场条件满足",
            metadata={
                'strategy_type': recommendation.strategy_type,
                'expected_return': recommendation.expected_return,
                'risk_level': recommendation.risk_level
            }
        )
        
        self.last_signals[ticker] = datetime.now()
        return signal
    
    def _check_entry_conditions(self,
                               strategy_type: str,
                               market_data: Dict[str, Any],
                               conditions: Dict[str, Any]) -> bool:
        """检查入场条件（简化实现）"""
        # 实际实现中应基于market_data检查所有条件
        # 这里简化处理，假设有50%概率满足条件
        return np.random.random() > 0.5
    
    def _compute_composite_signal(self, signals: List[TradingSignal]) -> Dict[str, Any]:
        """计算综合信号"""
        if not signals:
            return {'signal': 'hold', 'confidence': 0.0}
        
        # 加权计算
        total_confidence = sum(s.confidence for s in signals)
        avg_position = sum(s.position_size * s.confidence for s in signals) / total_confidence
        
        # 确定综合信号
        if avg_position > 0.8:
            composite = 'strong_buy'
        elif avg_position > 0.5:
            composite = 'buy'
        elif avg_position > 0.3:
            composite = 'weak_buy'
        else:
            composite = 'hold'
        
        return {
            'signal': composite,
            'confidence': round(total_confidence / len(signals), 4),
            'suggested_position': round(avg_position, 2)
        }
    
    def _generate_risk_management(self,
                                 recommendations: List[StrategyRecommendation],
                                 current_price: float) -> Dict[str, Any]:
        """生成风险管理建议"""
        if not recommendations:
            return {}
        
        # 取第一个（最优）策略的风险参数
        best_strategy = recommendations[0]
        params = best_strategy.parameters
        
        return {
            'max_position_size': round(params.position_size, 2),
            'stop_loss_pct': round(params.stop_loss * 100, 2) if params.stop_loss else None,
            'take_profit_pct': round(params.take_profit * 100, 2) if params.take_profit else None,
            'max_holding_days': params.max_holding_days,
            'risk_level': best_strategy.risk_level,
            'suggested_stop_price': round(current_price * (1 - params.stop_loss), 2) if params.stop_loss else None,
            'suggested_target_price': round(current_price * (1 + params.take_profit), 2) if params.take_profit else None
        }


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("QuantClaw Pro - 决策层测试")
    print("=" * 70)
    
    # 创建决策层
    decision_layer = DecisionLayer()
    
    # 测试数据
    test_cases = [
        {
            'ticker': 'AAPL',
            'mbti_type': 'INTJ',
            'dimensions': {'ie': 0.35, 'ns': 0.68, 'tf': 0.42, 'jp': 0.71},
            'price': 185.50,
            'regime': MarketRegime.BULL
        },
        {
            'ticker': 'TSLA',
            'mbti_type': 'ESTP',
            'dimensions': {'ie': 0.75, 'ns': 0.72, 'tf': 0.65, 'jp': 0.35},
            'price': 240.30,
            'regime': MarketRegime.HIGH_VOL
        },
        {
            'ticker': 'JNJ',
            'mbti_type': 'ISTJ',
            'dimensions': {'ie': 0.25, 'ns': 0.35, 'tf': 0.45, 'jp': 0.75},
            'price': 158.20,
            'regime': MarketRegime.SIDEWAYS
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n【测试案例 {i}】{test['ticker']} ({test['mbti_type']})")
        print("-" * 70)
        
        decision = decision_layer.make_decision(
            ticker=test['ticker'],
            mbti_type=test['mbti_type'],
            dimension_scores=test['dimensions'],
            current_price=test['price'],
            market_data={},
            market_regime=test['regime']
        )
        
        print(f"\n市场环境: {decision['market_regime']}")
        print(f"推荐策略数量: {len(decision['recommended_strategies'])}")
        
        print("\n策略推荐:")
        for j, strategy in enumerate(decision['recommended_strategies'], 1):
            print(f"  {j}. {strategy['name']}")
            print(f"     权重: {strategy['weight']:.1%}")
            print(f"     兼容性: {strategy['compatibility']:.2%}")
            print(f"     预期收益: {strategy['expected_return']:.1%}")
            print(f"     仓位: {strategy['parameters']['position_size']:.0%}")
            print(f"     止损: {strategy['parameters']['stop_loss']:.1%}")
        
        print(f"\n综合信号: {decision['composite_signal']['signal']}")
        print(f"建议仓位: {decision['composite_signal']['suggested_position']:.0%}")
        
        if decision['risk_management']:
            rm = decision['risk_management']
            print(f"\n风险管理:")
            print(f"  风险等级: {rm['risk_level']}")
            print(f"  最大仓位: {rm['max_position_size']:.0%}")
            print(f"  止损价格: ${rm['suggested_stop_price']}")
            print(f"  目标价格: ${rm['suggested_target_price']}")
    
    print("\n" + "=" * 70)
    print("决策层测试完成!")
    print("=" * 70)
