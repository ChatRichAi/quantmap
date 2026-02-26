"""
QuantClaw Pro - MBTI 股性分类系统
认知层 (Cognition Layer) - 四维度计算器 + 16型分类器
Phase 2: Week 3-4

将32维特征向量映射到MBTI四维性格，完成16型分类
"""

import numpy as np
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum


class MBTIType(Enum):
    """MBTI 16型枚举"""
    INTJ = "INTJ"
    INTP = "INTP"
    ENTJ = "ENTJ"
    ENTP = "ENTP"
    INFJ = "INFJ"
    INFP = "INFP"
    ENFJ = "ENFJ"
    ENFP = "ENFP"
    ISTJ = "ISTJ"
    ISFJ = "ISFJ"
    ESTJ = "ESTJ"
    ESFJ = "ESFJ"
    ISTP = "ISTP"
    ISFP = "ISFP"
    ESTP = "ESTP"
    ESFP = "ESFP"


@dataclass
class DimensionScores:
    """四维性格分数"""
    ie: float  # 内向(0) / 外向(1)
    ns: float  # 实感(0) / 直觉(1)
    tf: float  # 思考(0) / 情感(1)
    jp: float  # 感知(0) / 判断(1)
    
    def to_mbti_code(self) -> str:
        """转换为MBTI代码"""
        code = ""
        code += "E" if self.ie > 0.5 else "I"
        code += "N" if self.ns > 0.5 else "S"
        code += "F" if self.tf > 0.5 else "T"
        code += "J" if self.jp > 0.5 else "P"
        return code
    
    def to_mbti_type(self) -> MBTIType:
        """转换为MBTI枚举类型"""
        return MBTIType(self.to_mbti_code())
    
    def confidence(self) -> float:
        """
        计算分类置信度
        基于四维分数与0.5的距离，距离越远置信度越高
        """
        distances = [
            abs(self.ie - 0.5),
            abs(self.ns - 0.5),
            abs(self.tf - 0.5),
            abs(self.jp - 0.5)
        ]
        # 最小距离决定置信度，乘以2归一化到[0,1]
        return min(distances) * 2
    
    def dimension_confidence(self) -> Dict[str, float]:
        """每个维度的置信度"""
        return {
            'ie': abs(self.ie - 0.5) * 2,
            'ns': abs(self.ns - 0.5) * 2,
            'tf': abs(self.tf - 0.5) * 2,
            'jp': abs(self.jp - 0.5) * 2
        }
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'ie': round(self.ie, 4),
            'ns': round(self.ns, 4),
            'tf': round(self.tf, 4),
            'jp': round(self.jp, 4),
            'mbti_code': self.to_mbti_code(),
            'confidence': round(self.confidence(), 4)
        }


@dataclass
class PersonalityProfile:
    """股性档案"""
    ticker: str
    timestamp: datetime
    dimension_scores: DimensionScores
    mbti_type: MBTIType
    mbti_name: str
    category: str
    confidence: float
    risk_level: str
    recommended_strategies: List[Dict]
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'ticker': self.ticker,
            'timestamp': self.timestamp.isoformat(),
            'mbti_type': self.mbti_type.value,
            'mbti_name': self.mbti_name,
            'category': self.category,
            'dimension_scores': self.dimension_scores.to_dict(),
            'confidence': round(self.confidence, 4),
            'risk_level': self.risk_level,
            'recommended_strategies': self.recommended_strategies
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class DimensionCalculator:
    """
    四维度计算器
    将32维特征向量映射到MBTI四维性格分数
    """
    
    def __init__(self, use_standardization: bool = True):
        """
        初始化计算器
        
        Args:
            use_standardization: 是否使用标准化（需要历史统计数据）
        """
        self.use_standardization = use_standardization
        
        # 历史统计数据（用于标准化）
        # 基于大量股票历史数据计算得出
        self.stats = {
            'ie': {'mean': 0.45, 'std': 0.20},
            'ns': {'mean': 0.52, 'std': 0.18},
            'tf': {'mean': 0.48, 'std': 0.22},
            'jp': {'mean': 0.50, 'std': 0.19}
        }
        
        # 特征权重配置
        self.weights = {
            'ie': {
                'market_correlation': 0.30,
                'turnover_percentile': 0.25,
                'volume_price_corr': 0.20,
                'retail_participation': 0.15,
                'fund_flow_ratio': 0.10
            },
            'ns': {
                'adx': 0.35,
                'trend_duration': 0.25,
                'hurst_exponent': 0.20,
                'breakout_frequency': 0.15,
                'consolidation_ratio': 0.05
            },
            'tf': {
                'volume_price_corr': 0.30,
                'fund_flow_ratio': 0.25,
                'rsi_extreme_freq': 0.20,
                'herding_effect': 0.15,
                'fear_greed_index': 0.10
            },
            'jp': {
                'direction_consistency': 0.35,
                'trend_efficiency': 0.25,
                'ma_alignment': 0.20,
                'pattern_complexity': 0.15,
                'consolidation_ratio': 0.05
            }
        }
    
    def calculate_ie(self, features: Dict[str, float]) -> float:
        """
        计算I/E维度 (内向/外向)
        
        I (内向, <0.5): 独立走势、低关注度、不受大盘影响
        E (外向, >0.5): 高换手率、高关注度、资金博弈激烈
        """
        w = self.weights['ie']
        
        raw_score = (
            (1 - features.get('market_correlation', 0.5)) * w['market_correlation'] +
            (1 - features.get('turnover_percentile', 0.5)) * w['turnover_percentile'] +
            features.get('volume_price_corr', 0.5) * w['volume_price_corr'] +
            features.get('retail_participation', 0.5) * w['retail_participation'] +
            (1 - abs(features.get('fund_flow_ratio', 0.5) - 0.5) * 2) * w['fund_flow_ratio']
        )
        
        if self.use_standardization:
            return self._standardize(raw_score, 'ie')
        return np.clip(raw_score, 0, 1)
    
    def calculate_ns(self, features: Dict[str, float]) -> float:
        """
        计算N/S维度 (直觉/实感)
        
        N (直觉, >0.5): 趋势性强、动量持久、突破倾向
        S (实感, <0.5): 均值回归、区间明确、可预测
        """
        w = self.weights['ns']
        
        raw_score = (
            features.get('adx', 0.5) * w['adx'] +
            features.get('trend_duration', 0.5) * w['trend_duration'] +
            features.get('hurst_exponent', 0.5) * w['hurst_exponent'] +
            features.get('breakout_frequency', 0.5) * w['breakout_frequency'] +
            (1 - features.get('consolidation_ratio', 0.5)) * w['consolidation_ratio']
        )
        
        if self.use_standardization:
            return self._standardize(raw_score, 'ns')
        return np.clip(raw_score, 0, 1)
    
    def calculate_tf(self, features: Dict[str, float]) -> float:
        """
        计算T/F维度 (思考/情感)
        
        T (思考, <0.5): 量价配合、机构主导、逻辑清晰
        F (情感, >0.5): 情绪化、消息敏感、散户博弈
        """
        w = self.weights['tf']
        
        # 情绪偏离度（距离0.5的程度）
        emotion_deviation = abs(features.get('fear_greed_index', 0.5) - 0.5) * 2
        
        raw_score = (
            features.get('rsi_extreme_freq', 0.5) * w['rsi_extreme_freq'] +
            features.get('herding_effect', 0.5) * w['herding_effect'] +
            emotion_deviation * w['fear_greed_index'] +
            (1 - abs(features.get('volume_price_corr', 0.5) - 0.5) * 2) * w['volume_price_corr'] +
            (1 - features.get('fund_flow_ratio', 0.5)) * w['fund_flow_ratio']
        )
        
        if self.use_standardization:
            return self._standardize(raw_score, 'tf')
        return np.clip(raw_score, 0, 1)
    
    def calculate_jp(self, features: Dict[str, float]) -> float:
        """
        计算J/P维度 (判断/感知)
        
        J (判断, >0.5): 趋势明确、方向一致、执行力强
        P (感知, <0.5): 灵活、震荡、多方向试探
        """
        w = self.weights['jp']
        
        raw_score = (
            features.get('direction_consistency', 0.5) * w['direction_consistency'] +
            features.get('trend_efficiency', 0.5) * w['trend_efficiency'] +
            features.get('ma_alignment', 0.5) * w['ma_alignment'] +
            (1 - features.get('pattern_complexity', 0.5)) * w['pattern_complexity'] +
            (1 - features.get('consolidation_ratio', 0.5)) * w['consolidation_ratio']
        )
        
        if self.use_standardization:
            return self._standardize(raw_score, 'jp')
        return np.clip(raw_score, 0, 1)
    
    def _standardize(self, raw_score: float, dimension: str) -> float:
        """
        使用Sigmoid函数进行标准化
        将原始分数映射到[0,1]区间
        """
        mean = self.stats[dimension]['mean']
        std = self.stats[dimension]['std']
        
        # Z-score标准化
        z_score = (raw_score - mean) / std
        
        # Sigmoid映射
        normalized = 1 / (1 + np.exp(-z_score))
        
        return float(np.clip(normalized, 0, 1))
    
    def calculate_all(self, features: Dict[str, float]) -> DimensionScores:
        """计算所有四个维度"""
        return DimensionScores(
            ie=self.calculate_ie(features),
            ns=self.calculate_ns(features),
            tf=self.calculate_tf(features),
            jp=self.calculate_jp(features)
        )
    
    def update_stats(self, dimension: str, mean: float, std: float):
        """更新历史统计数据"""
        self.stats[dimension]['mean'] = mean
        self.stats[dimension]['std'] = std
    
    def get_feature_importance(self, dimension: str) -> Dict[str, float]:
        """获取指定维度的特征重要性（权重）"""
        return self.weights.get(dimension, {})


class PersonalityClassifier:
    """
    16型股性分类器
    基于四维分数输出完整的股性档案
    """
    
    # 16型性格定义
    PERSONALITY_DEFINITIONS = {
        MBTIType.INTJ: {
            'name': '战略大师',
            'category': 'Analysts',
            'description': '长周期趋势、强逻辑驱动、独立判断、高Alpha',
            'risk_level': 'High',
            'typical_stocks': ['NVDA', 'AAPL', 'MSFT', 'AMD']
        },
        MBTIType.INTP: {
            'name': '逻辑解谜者',
            'category': 'Analysts',
            'description': '复杂走势、难以预测、需深度分析、反身性',
            'risk_level': 'High',
            'typical_stocks': ['复杂衍生品', '小盘科技股']
        },
        MBTIType.ENTJ: {
            'name': '霸道总裁',
            'category': 'Analysts',
            'description': '强势上涨、高Alpha、统治力强、机构抱团',
            'risk_level': 'Medium',
            'typical_stocks': ['MSFT', 'AAPL', 'BRK.B', 'JNJ']
        },
        MBTIType.ENTP: {
            'name': '辩论家',
            'category': 'Analysts',
            'description': '高争议、多空博弈激烈、波动大、观点分歧',
            'risk_level': 'High',
            'typical_stocks': ['GME', 'AMC', 'TSLA(争议期)']
        },
        MBTIType.INFJ: {
            'name': '逆向先知',
            'category': 'Diplomats',
            'description': '反人性走势、提前见底/见顶、独立思考',
            'risk_level': 'High',
            'typical_stocks': ['逆势龙头股', '被错杀价值股']
        },
        MBTIType.INFP: {
            'name': '梦想家',
            'category': 'Diplomats',
            'description': '概念驱动、高弹性、情绪化、估值难定',
            'risk_level': 'Extreme',
            'typical_stocks': ['题材股', '概念股']
        },
        MBTIType.ENFJ: {
            'name': '魅力领袖',
            'category': 'Diplomats',
            'description': '板块龙头、带动效应强、资金聚焦',
            'risk_level': 'Medium',
            'typical_stocks': ['行业一哥', '板块核心标的']
        },
        MBTIType.ENFP: {
            'name': '创新先锋',
            'category': 'Diplomats',
            'description': '高成长、颠覆性、叙事驱动、想象力',
            'risk_level': 'High',
            'typical_stocks': ['新能源股', 'AI概念股']
        },
        MBTIType.ISTJ: {
            'name': '稳健守护者',
            'category': 'Sentinels',
            'description': '低波动、高确定性、趋势稳定、分红稳定',
            'risk_level': 'Low',
            'typical_stocks': ['公用事业股', 'REITs']
        },
        MBTIType.ISFJ: {
            'name': '价值守望者',
            'category': 'Sentinels',
            'description': '低估、防御性强、业绩可预期、安全边际',
            'risk_level': 'Low',
            'typical_stocks': ['银行股', '消费蓝筹']
        },
        MBTIType.ESTJ: {
            'name': '效率机器',
            'category': 'Sentinels',
            'description': '强执行力、机构主导、走势规范、Beta稳定',
            'risk_level': 'Medium',
            'typical_stocks': ['大盘蓝筹股', '指数成分股']
        },
        MBTIType.ESFJ: {
            'name': '群体领袖',
            'category': 'Sentinels',
            'description': '跟随指数、Beta高、同涨同跌、流动性好',
            'risk_level': 'Medium',
            'typical_stocks': ['行业ETF']
        },
        MBTIType.ISTP: {
            'name': '敏捷猎手',
            'category': 'Explorers',
            'description': '高波动、快速反应、技术性强、盈亏比高',
            'risk_level': 'High',
            'typical_stocks': ['小盘科技股']
        },
        MBTIType.ISFP: {
            'name': '艺术玩家',
            'category': 'Explorers',
            'description': '随机漫步、无明显趋势、噪声多、难以预测',
            'risk_level': 'Extreme',
            'typical_stocks': ['ST股', '壳资源']
        },
        MBTIType.ESTP: {
            'name': '短线狂徒',
            'category': 'Explorers',
            'description': '高换手、追涨杀跌、资金博弈、热点追逐',
            'risk_level': 'Extreme',
            'typical_stocks': ['热门概念股']
        },
        MBTIType.ESFP: {
            'name': '派对动物',
            'category': 'Explorers',
            'description': '消息面敏感、大起大落、群众情绪、流动性',
            'risk_level': 'Extreme',
            'typical_stocks': ['网红股', 'Meme股']
        }
    }
    
    # 策略配置
    STRATEGY_CONFIGS = {
        MBTIType.INTJ: [
            {'name': '成长股动量', 'weight': 0.40, 'type': 'trend_following'},
            {'name': '趋势跟踪', 'weight': 0.35, 'type': 'momentum'},
            {'name': '突破买入', 'weight': 0.25, 'type': 'breakout'}
        ],
        MBTIType.INTP: [
            {'name': '机器学习多因子', 'weight': 0.50, 'type': 'ml_multi_factor'},
            {'name': '统计套利', 'weight': 0.30, 'type': 'stat_arb'},
            {'name': '波动率交易', 'weight': 0.20, 'type': 'volatility'}
        ],
        MBTIType.ENTJ: [
            {'name': '核心资产持有', 'weight': 0.50, 'type': 'core_asset'},
            {'name': '趋势跟踪', 'weight': 0.30, 'type': 'trend_following'},
            {'name': '定投策略', 'weight': 0.20, 'type': 'dca'}
        ],
        MBTIType.ENTP: [
            {'name': '配对交易', 'weight': 0.40, 'type': 'pairs_trading'},
            {'name': '多空策略', 'weight': 0.35, 'type': 'long_short'},
            {'name': '事件驱动', 'weight': 0.25, 'type': 'event_driven'}
        ],
        MBTIType.INFJ: [
            {'name': '逆向投资', 'weight': 0.45, 'type': 'contrarian'},
            {'name': '左侧交易', 'weight': 0.35, 'type': 'left_side'},
            {'name': '均值回归', 'weight': 0.20, 'type': 'mean_reversion'}
        ],
        MBTIType.INFP: [
            {'name': '事件驱动', 'weight': 0.40, 'type': 'event_driven'},
            {'name': '主题炒作', 'weight': 0.35, 'type': 'theme_rotation'},
            {'name': '动量爆发', 'weight': 0.25, 'type': 'momentum_burst'}
        ],
        MBTIType.ENFJ: [
            {'name': '龙头股策略', 'weight': 0.45, 'type': 'leader_following'},
            {'name': '板块联动', 'weight': 0.35, 'type': 'sector_rotation'},
            {'name': '趋势跟随', 'weight': 0.20, 'type': 'momentum'}
        ],
        MBTIType.ENFP: [
            {'name': '主题投资', 'weight': 0.40, 'type': 'theme_breakout'},
            {'name': '趋势突破', 'weight': 0.35, 'type': 'breakout'},
            {'name': '成长股策略', 'weight': 0.25, 'type': 'growth'}
        ],
        MBTIType.ISTJ: [
            {'name': '趋势跟踪', 'weight': 0.40, 'type': 'trend_following'},
            {'name': '红利再投资', 'weight': 0.35, 'type': 'dividend'},
            {'name': '防御配置', 'weight': 0.25, 'type': 'defensive'}
        ],
        MBTIType.ISFJ: [
            {'name': '价值投资', 'weight': 0.50, 'type': 'value'},
            {'name': '定投策略', 'weight': 0.30, 'type': 'dca'},
            {'name': '安全边际', 'weight': 0.20, 'type': 'margin_of_safety'}
        ],
        MBTIType.ESTJ: [
            {'name': '指数增强', 'weight': 0.45, 'type': 'index_enhancement'},
            {'name': 'ETF轮动', 'weight': 0.35, 'type': 'etf_rotation'},
            {'name': '大盘股策略', 'weight': 0.20, 'type': 'large_cap'}
        ],
        MBTIType.ESFJ: [
            {'name': '行业轮动', 'weight': 0.45, 'type': 'sector_rotation'},
            {'name': 'Beta策略', 'weight': 0.35, 'type': 'beta'},
            {'name': '指数跟踪', 'weight': 0.20, 'type': 'index_tracking'}
        ],
        MBTIType.ISTP: [
            {'name': '波段操作', 'weight': 0.40, 'type': 'swing_trading'},
            {'name': '日内交易', 'weight': 0.35, 'type': 'intraday'},
            {'name': '技术突破', 'weight': 0.25, 'type': 'technical_breakout'}
        ],
        MBTIType.ISFP: [
            {'name': '均值回归', 'weight': 0.50, 'type': 'mean_reversion'},
            {'name': '高频套利', 'weight': 0.30, 'type': 'high_frequency'},
            {'name': '事件博弈', 'weight': 0.20, 'type': 'event_gamble'}
        ],
        MBTIType.ESTP: [
            {'name': '打板策略', 'weight': 0.40, 'type': 'limit_up'},
            {'name': '游资跟随', 'weight': 0.35, 'type': 'hot_money'},
            {'name': '热点追逐', 'weight': 0.25, 'type': 'hot_theme'}
        ],
        MBTIType.ESFP: [
            {'name': '情绪交易', 'weight': 0.45, 'type': 'sentiment'},
            {'name': '新闻驱动', 'weight': 0.35, 'type': 'news_driven'},
            {'name': '动量追逐', 'weight': 0.20, 'type': 'momentum_chasing'}
        ]
    }
    
    def __init__(self):
        self.dimension_calculator = DimensionCalculator()
    
    def classify(self, ticker: str, features: Dict[str, float]) -> PersonalityProfile:
        """
        对股票进行MBTI分类
        
        Args:
            ticker: 股票代码
            features: 32维特征字典
            
        Returns:
            PersonalityProfile对象
        """
        # 计算四维分数
        dimension_scores = self.dimension_calculator.calculate_all(features)
        
        # 确定MBTI类型
        mbti_type = dimension_scores.to_mbti_type()
        
        # 获取性格定义
        personality_def = self.PERSONALITY_DEFINITIONS[mbti_type]
        
        # 获取推荐策略
        recommended_strategies = self.STRATEGY_CONFIGS[mbti_type]
        
        # 创建股性档案
        profile = PersonalityProfile(
            ticker=ticker,
            timestamp=datetime.now(),
            dimension_scores=dimension_scores,
            mbti_type=mbti_type,
            mbti_name=personality_def['name'],
            category=personality_def['category'],
            confidence=dimension_scores.confidence(),
            risk_level=personality_def['risk_level'],
            recommended_strategies=recommended_strategies
        )
        
        return profile
    
    def batch_classify(self, features_dict: Dict[str, Dict[str, float]]) -> Dict[str, PersonalityProfile]:
        """
        批量分类
        
        Args:
            features_dict: {ticker: features} 字典
            
        Returns:
            {ticker: PersonalityProfile} 字典
        """
        results = {}
        for ticker, features in features_dict.items():
            try:
                profile = self.classify(ticker, features)
                results[ticker] = profile
            except Exception as e:
                print(f"分类 {ticker} 失败: {e}")
                continue
        return results
    
    def get_personality_info(self, mbti_type: MBTIType) -> Dict:
        """获取性格类型详细信息"""
        return self.PERSONALITY_DEFINITIONS.get(mbti_type, {})
    
    def get_strategies(self, mbti_type: MBTIType) -> List[Dict]:
        """获取推荐策略"""
        return self.STRATEGY_CONFIGS.get(mbti_type, [])
    
    def get_all_personalities(self) -> List[Dict]:
        """获取所有16型性格定义"""
        return [
            {
                'type': mbti_type.value,
                **self.PERSONALITY_DEFINITIONS[mbti_type]
            }
            for mbti_type in MBTIType
        ]


class CognitionLayer:
    """
    认知层: 整合四维度计算器和16型分类器
    提供简洁的API接口
    """
    
    def __init__(self):
        self.calculator = DimensionCalculator()
        self.classifier = PersonalityClassifier()
    
    def analyze(self, ticker: str, features: Dict[str, float]) -> PersonalityProfile:
        """
        分析股票性格
        
        Args:
            ticker: 股票代码
            features: 32维特征字典（来自感知层）
            
        Returns:
            完整的股性档案
        """
        return self.classifier.classify(ticker, features)
    
    def get_dimension_details(self, features: Dict[str, float]) -> Dict:
        """获取四维度的详细计算结果"""
        scores = self.calculator.calculate_all(features)
        
        return {
            'scores': scores.to_dict(),
            'dimension_confidence': scores.dimension_confidence(),
            'interpretation': {
                'ie': '外向(E)' if scores.ie > 0.5 else '内向(I)',
                'ns': '直觉(N)' if scores.ns > 0.5 else '实感(S)',
                'tf': '情感(F)' if scores.tf > 0.5 else '思考(T)',
                'jp': '判断(J)' if scores.jp > 0.5 else '感知(P)'
            }
        }


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 70)
    print("QuantClaw Pro - 认知层测试")
    print("=" * 70)
    
    # 创建认知层
    cognition = CognitionLayer()
    
    # 模拟特征数据（来自感知层）
    test_features = {
        # 波动特征
        'volatility_20d': 0.35,
        'atr_ratio': 0.40,
        'garch_vol': 0.30,
        'vol_regime': 0.25,
        'max_daily_range': 0.45,
        'gap_frequency': 0.20,
        'tail_risk': 0.30,
        'vol_persistence': 0.35,
        
        # 趋势特征
        'adx': 0.72,
        'trend_slope': 0.68,
        'ma_alignment': 0.80,
        'price_position': 0.75,
        'trend_duration': 0.60,
        'direction_consistency': 0.70,
        'breakout_frequency': 0.55,
        'trend_efficiency': 0.65,
        
        # 情绪特征
        'rsi_extreme_freq': 0.25,
        'volume_price_corr': 0.60,
        'turnover_percentile': 0.40,
        'fund_flow_ratio': 0.70,
        'retail_participation': 0.30,
        'momentum_oscillation': 0.35,
        'fear_greed_index': 0.55,
        'herding_effect': 0.25,
        
        # 结构特征
        'support_distance': 0.40,
        'resistance_distance': 0.35,
        'channel_width': 0.30,
        'consolidation_ratio': 0.20,
        'pattern_complexity': 0.35,
        'fractal_dimension': 0.45,
        'hurst_exponent': 0.68,
        'market_correlation': 0.55
    }
    
    # 测试单只股票分析
    print("\n【测试1】单只股票性格分析")
    print("-" * 70)
    
    profile = cognition.analyze("AAPL", test_features)
    
    print(f"\n股票代码: {profile.ticker}")
    print(f"分析时间: {profile.timestamp}")
    print(f"\nMBTI类型: {profile.mbti_type.value}")
    print(f"性格名称: {profile.mbti_name}")
    print(f"所属类别: {profile.category}")
    print(f"风险等级: {profile.risk_level}")
    print(f"分类置信度: {profile.confidence:.2%}")
    
    print(f"\n四维分数:")
    print(f"  I/E (内向/外向): {profile.dimension_scores.ie:.4f} " + 
          f"({'E' if profile.dimension_scores.ie > 0.5 else 'I'})")
    print(f"  N/S (直觉/实感): {profile.dimension_scores.ns:.4f} " +
          f"({'N' if profile.dimension_scores.ns > 0.5 else 'S'})")
    print(f"  T/F (思考/情感): {profile.dimension_scores.tf:.4f} " +
          f"({'F' if profile.dimension_scores.tf > 0.5 else 'T'})")
    print(f"  J/P (判断/感知): {profile.dimension_scores.jp:.4f} " +
          f"({'J' if profile.dimension_scores.jp > 0.5 else 'P'})")
    
    print(f"\n推荐策略:")
    for i, strategy in enumerate(profile.recommended_strategies, 1):
        print(f"  {i}. {strategy['name']} (权重: {strategy['weight']:.0%})")
    
    # 测试维度详情
    print("\n\n【测试2】维度详细分析")
    print("-" * 70)
    
    details = cognition.get_dimension_details(test_features)
    
    print("\n各维度置信度:")
    for dim, conf in details['dimension_confidence'].items():
        bar = "█" * int(conf * 20)
        print(f"  {dim.upper()}: {conf:.2%} {bar}")
    
    # 测试JSON输出
    print("\n\n【测试3】JSON输出")
    print("-" * 70)
    print(profile.to_json())
    
    # 测试批量分类
    print("\n\n【测试4】批量分类")
    print("-" * 70)
    
    # 修改特征模拟不同股票
    test_stocks = {
        "AAPL": test_features,
        "TSLA": {**test_features, 'volatility_20d': 0.85, 'rsi_extreme_freq': 0.75, 
                 'herding_effect': 0.80, 'retail_participation': 0.70},
        "JNJ": {**test_features, 'adx': 0.25, 'volatility_20d': 0.15, 
                'trend_duration': 0.20, 'ma_alignment': 0.30}
    }
    
    results = cognition.classifier.batch_classify(test_stocks)
    
    print("\n批量分类结果:")
    for ticker, p in results.items():
        print(f"  {ticker}: {p.mbti_type.value} ({p.mbti_name}) - 置信度: {p.confidence:.2%}")
    
    # 测试获取所有性格类型
    print("\n\n【测试5】所有16型性格列表")
    print("-" * 70)
    
    all_personalities = cognition.classifier.get_all_personalities()
    
    # 按类别分组显示
    categories = {}
    for p in all_personalities:
        cat = p['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)
    
    for category, personalities in categories.items():
        print(f"\n【{category}】")
        for p in personalities:
            print(f"  {p['type']}: {p['name']} (风险: {p['risk_level']})")
    
    print("\n" + "=" * 70)
    print("认知层测试完成!")
    print("=" * 70)
