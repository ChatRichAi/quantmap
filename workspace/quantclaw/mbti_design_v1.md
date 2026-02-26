# QuantClaw Pro - MBTI 股性分类系统
## 完整详细设计文档

**版本**: v1.0  
**创建时间**: 2026-02-23  
**状态**: 设计方案已冻结，待开发实施

---

## 目录

1. [四维度计算器精确公式](#一四维度计算器精确公式)
2. [16型策略库完整定义](#二16型策略库完整定义)
3. [Neo4j 知识图谱数据模型](#三neo4j-知识图谱数据模型)

---

## 一、四维度计算器精确公式

### 1.1 概述

四维度计算器将感知层输出的 **32维特征向量** 映射到 MBTI 的四个维度：
- **I/E** (内向/外向)
- **N/S** (直觉/实感)
- **T/F** (思考/情感)
- **J/P** (判断/感知)

每个维度的输出值为 **[0, 1]** 区间，以 **0.5** 为分割阈值。

### 1.2 I/E 维度计算器

#### 定义
- **I (内向, <0.5)**: 股票独立走势、低关注度、不受大盘影响
- **E (外向, >0.5)**: 高换手率、高关注度、资金博弈激烈

#### 输入特征

| 特征名 | 权重 | 说明 |
|--------|------|------|
| market_correlation | 0.30 | 市场相关性(Beta) |
| turnover_percentile | 0.25 | 换手率分位数 |
| volume_price_corr | 0.20 | 量价相关系数 |
| retail_participation | 0.15 | 散户参与度 |
| fund_flow_ratio | 0.10 | 主力流入占比 |

#### 计算公式

```python
IE_score = (
    (1 - market_correlation) * 0.30 +           # 独立性
    (1 - turnover_percentile) * 0.25 +          # 安静度
    volume_price_corr * 0.20 +                  # 流动性敏感度
    retail_participation * 0.15 +               # 散户关注度
    (1 - abs(fund_flow_ratio - 0.5) * 2) * 0.10 # 资金稳定性
)
```

#### 标准化处理

```python
def normalize_ie(raw_score):
    """
    使用历史数据分布进行标准化
    """
    # 基于训练集的均值和标准差
    mean = 0.45  # 历史均值
    std = 0.20   # 历史标准差
    
    # Z-score标准化
    z_score = (raw_score - mean) / std
    
    # Sigmoid映射到[0,1]
    normalized = 1 / (1 + np.exp(-z_score))
    
    return np.clip(normalized, 0, 1)
```

#### 阈值设定

```python
if ie_score < 0.4:
    personality = "I (明显内向)"
elif ie_score < 0.5:
    personality = "I- (轻微内向)"
elif ie_score < 0.6:
    personality = "E- (轻微外向)"
else:
    personality = "E (明显外向)"
```

---

### 1.3 N/S 维度计算器

#### 定义
- **N (直觉, >0.5)**: 趋势性强、动量持久、突破倾向
- **S (实感, <0.5)**: 均值回归、区间明确、可预测

#### 输入特征

| 特征名 | 权重 | 说明 |
|--------|------|------|
| adx | 0.35 | 趋势强度指数 |
| trend_duration | 0.25 | 趋势持续时间 |
| hurst_exponent | 0.20 | 赫斯特指数 |
| breakout_frequency | 0.15 | 突破频率 |
| mean_reversion | 0.05 | 均值回归倾向(1-hurst) |

#### 计算公式

```python
NS_score = (
    adx * 0.35 +                           # ADX趋势强度
    trend_duration * 0.25 +                # 趋势持续时间
    hurst_exponent * 0.20 +                # 赫斯特指数(>0.5为趋势性)
    breakout_frequency * 0.15 +            # 突破频率
    (1 - consolidation_ratio) * 0.05       # 非盘整时间
)
```

#### 标准化处理

```python
def normalize_ns(raw_score):
    """
    N/S维度标准化
    """
    mean = 0.52  # 股票通常略偏趋势性
    std = 0.18
    
    z_score = (raw_score - mean) / std
    normalized = 1 / (1 + np.exp(-z_score))
    
    return np.clip(normalized, 0, 1)
```

---

### 1.4 T/F 维度计算器

#### 定义
- **T (思考, <0.5)**: 量价配合、机构主导、逻辑清晰
- **F (情感, >0.5)**: 情绪化、消息敏感、散户博弈

#### 输入特征

| 特征名 | 权重 | 说明 |
|--------|------|------|
| volume_price_corr | 0.30 | 量价相关系数(绝对值) |
| fund_flow_ratio | 0.25 | 机构主导度 |
| rsi_extreme_freq | 0.20 | RSI极端频率 |
| herding_effect | 0.15 | 羊群效应 |
| fear_greed_index | 0.10 | 恐惧贪婪指数偏离度 |

#### 计算公式

```python
# 情绪偏离度(距离0.5的程度)
emotion_deviation = abs(fear_greed_index - 0.5) * 2

TF_score = (
    rsi_extreme_freq * 0.20 +              # 情绪化交易频率
    herding_effect * 0.15 +                # 羊群效应
    emotion_deviation * 0.10 +             # 情绪极端程度
    (1 - abs(volume_price_corr - 0.5) * 2) * 0.30 +  # 量价非逻辑性
    (1 - fund_flow_ratio) * 0.25           # 机构参与度低
)
```

---

### 1.5 J/P 维度计算器

#### 定义
- **J (判断, >0.5)**: 趋势明确、方向一致、执行力强
- **P (感知, <0.5)**: 灵活、震荡、多方向试探

#### 输入特征

| 特征名 | 权重 | 说明 |
|--------|------|------|
| direction_consistency | 0.35 | 方向一致性 |
| trend_efficiency | 0.25 | 趋势效率 |
| ma_alignment | 0.20 | 均线排列 |
| pattern_complexity | 0.15 | 形态复杂度(反向) |
| consolidation_ratio | 0.05 | 盘整占比(反向) |

#### 计算公式

```python
JP_score = (
    direction_consistency * 0.35 +         # 方向一致性
    trend_efficiency * 0.25 +              # 趋势效率
    ma_alignment * 0.20 +                  # 均线排列
    (1 - pattern_complexity) * 0.15 +      # 形态简单
    (1 - consolidation_ratio) * 0.05       # 非盘整
)
```

---

### 1.6 完整代码实现

```python
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class DimensionScores:
    """四维性格分数"""
    ie: float  # 内向/外向
    ns: float  # 直觉/实感
    tf: float  # 思考/情感
    jp: float  # 判断/感知
    
    def to_mbti_code(self) -> str:
        """转换为MBTI代码"""
        code = ""
        code += "E" if self.ie > 0.5 else "I"
        code += "N" if self.ns > 0.5 else "S"
        code += "F" if self.tf > 0.5 else "T"
        code += "J" if self.jp > 0.5 else "P"
        return code
    
    def confidence(self) -> float:
        """计算分类置信度"""
        distances = [
            abs(self.ie - 0.5),
            abs(self.ns - 0.5),
            abs(self.tf - 0.5),
            abs(self.jp - 0.5)
        ]
        return min(distances) * 2  # 距离越远，置信度越高


class DimensionCalculator:
    """四维度计算器"""
    
    def __init__(self):
        # 历史统计数据(用于标准化)
        self.stats = {
            'ie': {'mean': 0.45, 'std': 0.20},
            'ns': {'mean': 0.52, 'std': 0.18},
            'tf': {'mean': 0.48, 'std': 0.22},
            'jp': {'mean': 0.50, 'std': 0.19}
        }
    
    def calculate_ie(self, features: Dict[str, float]) -> float:
        """计算I/E维度"""
        raw_score = (
            (1 - features.get('market_correlation', 0.5)) * 0.30 +
            (1 - features.get('turnover_percentile', 0.5)) * 0.25 +
            features.get('volume_price_corr', 0.5) * 0.20 +
            features.get('retail_participation', 0.5) * 0.15 +
            (1 - abs(features.get('fund_flow_ratio', 0.5) - 0.5) * 2) * 0.10
        )
        return self._normalize(raw_score, 'ie')
    
    def calculate_ns(self, features: Dict[str, float]) -> float:
        """计算N/S维度"""
        raw_score = (
            features.get('adx', 0.5) * 0.35 +
            features.get('trend_duration', 0.5) * 0.25 +
            features.get('hurst_exponent', 0.5) * 0.20 +
            features.get('breakout_frequency', 0.5) * 0.15 +
            (1 - features.get('consolidation_ratio', 0.5)) * 0.05
        )
        return self._normalize(raw_score, 'ns')
    
    def calculate_tf(self, features: Dict[str, float]) -> float:
        """计算T/F维度"""
        emotion_deviation = abs(features.get('fear_greed_index', 0.5) - 0.5) * 2
        
        raw_score = (
            features.get('rsi_extreme_freq', 0.5) * 0.20 +
            features.get('herding_effect', 0.5) * 0.15 +
            emotion_deviation * 0.10 +
            (1 - abs(features.get('volume_price_corr', 0.5) - 0.5) * 2) * 0.30 +
            (1 - features.get('fund_flow_ratio', 0.5)) * 0.25
        )
        return self._normalize(raw_score, 'tf')
    
    def calculate_jp(self, features: Dict[str, float]) -> float:
        """计算J/P维度"""
        raw_score = (
            features.get('direction_consistency', 0.5) * 0.35 +
            features.get('trend_efficiency', 0.5) * 0.25 +
            features.get('ma_alignment', 0.5) * 0.20 +
            (1 - features.get('pattern_complexity', 0.5)) * 0.15 +
            (1 - features.get('consolidation_ratio', 0.5)) * 0.05
        )
        return self._normalize(raw_score, 'jp')
    
    def _normalize(self, raw_score: float, dimension: str) -> float:
        """使用Sigmoid进行标准化"""
        mean = self.stats[dimension]['mean']
        std = self.stats[dimension]['std']
        
        z_score = (raw_score - mean) / std
        normalized = 1 / (1 + np.exp(-z_score))
        
        return float(np.clip(normalized, 0, 1))
    
    def calculate_all(self, features: Dict[str, float]) -> DimensionScores:
        """计算所有维度"""
        return DimensionScores(
            ie=self.calculate_ie(features),
            ns=self.calculate_ns(features),
            tf=self.calculate_tf(features),
            jp=self.calculate_jp(features)
        )
```

---

## 二、16型策略库完整定义

### 2.1 分析师型 (Analysts) - NT 组合

#### INTJ - 战略大师

**详细特征描述**:  
INTJ型股票展现出极强的战略性和前瞻性，它们往往处于行业技术前沿，具有清晰的长周期上升趋势。这类股票通常由机构投资者主导，散户参与度相对较低，价格波动呈现"进二退一"的稳健模式。它们对短期市场噪音不敏感，但一旦形成趋势就会持续较长时间。典型的INTJ股票包括科技巨头如NVDA、AAPL等，它们具有强大的护城河和持续的创新能力。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 成长股动量 | 40% | 持有强势成长股，利用趋势延续 |
| 趋势跟踪 | 35% | MA20/MA60多头排列时入场 |
| 突破买入 | 25% | 放量突破前高时加仓 |

**策略参数配置**:

```python
INTJ_CONFIG = {
    'position_size': 1.2,           # 120%基准仓位
    'holding_period': 'medium_long', # 中长款(1-6个月)
    'entry_conditions': {
        'ma_alignment': True,        # 均线多头排列
        'adx_threshold': 25,         # ADX>25确认趋势
        'volume_spike': 1.3          # 成交量放大30%
    },
    'exit_conditions': {
        'trend_break': True,         # 趋势线跌破
        'ma_cross': 'MA5_cross_MA20_down',  # 均线死叉
        'profit_target': 0.30        # 30%止盈
    },
    'stop_loss': 0.12,              # 12%止损
    'trailing_stop': 0.08           # 8%移动止损
}
```

**适用市场环境**: 牛市、结构性行情
**风险等级**: 中高
**典型标的**: NVDA, AAPL, MSFT, AMD

---

#### INTP - 逻辑解谜者

**详细特征描述**:  
INTP型股票走势复杂多变，常让传统技术分析失效。它们的价格行为呈现出高度的非线性和反身性，简单的趋势跟踪策略往往难以盈利。这类股票可能涉及复杂的商业模式或处于高度竞争和变化的行业。它们需要更 sophisticated 的量化模型才能捕捉到有效的交易信号。这类股票对量化策略来说是"难题"但也是有潜力的阿尔法来源。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 机器学习多因子 | 50% | 使用复杂模型捕捉非线性关系 |
| 统计套利 | 30% | 跨品种配对交易 |
| 波动率交易 | 20% | 利用隐含波动率偏差 |

**策略参数配置**:

```python
INTP_CONFIG = {
    'position_size': 0.8,
    'holding_period': 'variable',
    'entry_conditions': {
        'model_signal': 'ml_score > 0.7',
        'volatility_regime': 'normal_to_high',
        'correlation_breakdown': True
    },
    'exit_conditions': {
        'model_decay': 'ml_score < 0.3',
        'regime_change': True,
        'max_holding': 20  # 最大持有20天
    },
    'stop_loss': 0.15,
    'trailing_stop': None
}
```

**适用市场环境**: 震荡市、结构性分化
**风险等级**: 高
**典型标的**: 复杂衍生品、小盘科技股

---

#### ENTJ - 霸道总裁

**详细特征描述**:  
ENTJ型股票是市场中的"霸主"，它们具有极强的市场统治力和机构抱团特征。这类股票往往具有稳固的市场地位、优秀的盈利能力和持续的股东回报。它们的走势呈现"强者恒强"的特点，在牛市中领涨，在熊市中抗跌。机构资金的持续流入使得它们的价格波动相对稳健，但估值往往处于高位。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 核心资产持有 | 50% | 长期持有优质资产 |
| 趋势跟踪 | 30% | 跟随机构资金动向 |
| 定投策略 | 20% | 定期定额投资 |

**策略参数配置**:

```python
ENTJ_CONFIG = {
    'position_size': 1.5,
    'holding_period': 'long',
    'entry_conditions': {
        'institutional_holding': 'increasing',
        'roe_threshold': 15,
        'market_leader': True
    },
    'exit_conditions': {
        'fundamental_change': True,
        'valuation_extreme': 'PE > 95th_percentile',
        'institutional_exit': True
    },
    'stop_loss': 0.10,
    'trailing_stop': 0.15
}
```

**适用市场环境**: 任何市场环境
**风险等级**: 中
**典型标的**: MSFT, AAPL, BRK.B, JNJ

---

#### ENTP - 辩论家

**详细特征描述**:  
ENTP型股票充满争议和多空博弈，市场对它们的价值判断存在巨大分歧。这类股票的价格波动剧烈，经常出现极端的涨跌。它们可能是做空热门股、有争议的公司或处于转型期的企业。高波动性为短线交易者提供了机会，但也伴随着巨大风险。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 配对交易 | 40% | 做多/做空相关性高的股票 |
| 多空策略 | 35% | 根据情绪指标做多或做空 |
| 事件驱动 | 25% | 利用财报/新闻事件 |

**策略参数配置**:

```python
ENTP_CONFIG = {
    'position_size': 1.0,
    'holding_period': 'short_medium',
    'entry_conditions': {
        'short_interest': 'high',
        'sentiment_extreme': True,
        'volume_surge': 2.0
    },
    'exit_conditions': {
        'sentiment_reversal': True,
        'short_squeeze': True,
        'position_convergence': True
    },
    'stop_loss': 0.08,
    'trailing_stop': 0.06
}
```

**适用市场环境**: 高波动市场、事件密集期
**风险等级**: 高
**典型标的**: GME, AMC, TSLA(争议期)

---

### 2.2 外交官型 (Diplomats) - NF 组合

#### INFJ - 逆向先知

**详细特征描述**:  
INFJ型股票具有强烈的逆向特征，它们常常在市场恐慌时被错杀，在市场狂热时被忽视。这类股票的价格走势往往领先于市场共识，具有"春江水暖鸭先知"的特点。它们可能是被低估的价值股或具有转型潜力的困境企业。投资这类股票需要独立思考能力和承受短期浮亏的勇气。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 逆向投资 | 45% | 市场恐慌时买入 |
| 左侧交易 | 35% | 提前布局潜在反转 |
| 均值回归 | 20% | 利用价格偏离 |

**策略参数配置**:

```python
INFJ_CONFIG = {
    'position_size': 0.9,
    'holding_period': 'medium',
    'entry_conditions': {
        'rsi_oversold': 'RSI < 30',
        'sentiment_pessimistic': True,
        'fundamental_solid': True,
        'price_below_ma': 'price < MA200'
    },
    'exit_conditions': {
        'sentiment_improvement': True,
        'valuation_recover': True,
        'profit_target': 0.25
    },
    'stop_loss': 0.15,
    'trailing_stop': None
}
```

**适用市场环境**: 熊市末期、价值洼地
**风险等级**: 高
**典型标的**: 被错杀的价值股、困境反转股

---

#### INFP - 梦想家

**详细特征描述**:  
INFP型股票是市场的"梦想承载者"，它们往往代表着未来的可能性而非当下的确定性。这类股票的价格主要由叙事和想象力驱动，基本面往往难以支撑当前估值。它们的波动性极高，可能在短时间内翻倍也可能腰斩。投资这类股票需要敏锐的主题嗅觉和严格的纪律。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 事件驱动 | 40% | 利用重大事件催化 |
| 主题炒作 | 35% | 跟随热门概念轮动 |
| 动量爆发 | 25% | 追涨强势股 |

**策略参数配置**:

```python
INFP_CONFIG = {
    'position_size': 0.7,
    'holding_period': 'short',
    'entry_conditions': {
        'theme_hot': True,
        'narrative_change': True,
        'volume_explosion': 3.0
    },
    'exit_conditions': {
        'theme_cooling': True,
        'momentum_decay': True,
        'profit_target': 0.20
    },
    'stop_loss': 0.10,
    'trailing_stop': 0.05
}
```

**适用市场环境**: 主题炒作期、流动性充裕
**风险等级**: 极高
**典型标的**: 概念股、Meme股

---

#### ENFJ - 魅力领袖

**详细特征描述**:  
ENFJ型股票是板块中的"领头羊"，它们的涨跌往往带动整个行业板块。这类股票具有强大的市场号召力和资金聚集效应，是机构配置的必选标的。它们的价格走势稳健向上，但一旦见顶也会引发板块连锁反应。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 龙头股策略 | 45% | 持有行业龙头 |
| 板块联动 | 35% | 利用板块效应 |
| 趋势跟随 | 20% | 跟随资金流向 |

**策略参数配置**:

```python
ENFJ_CONFIG = {
    'position_size': 1.1,
    'holding_period': 'medium',
    'entry_conditions': {
        'sector_leader': True,
        'fund_inflow': 'institutional_buying',
        'relative_strength': 'top_10%'
    },
    'exit_conditions': {
        'sector_rotation': True,
        'leadership_change': True,
        'profit_target': 0.30
    },
    'stop_loss': 0.10,
    'trailing_stop': 0.10
}
```

**适用市场环境**: 结构性行情、板块轮动
**风险等级**: 中
**典型标的**: 行业龙头、板块核心标的

---

#### ENFP - 创新先锋

**详细特征描述**:  
ENFP型股票代表着创新和变革，它们往往是新技术、新模式的先行者。这类股票具有极高的成长潜力和估值弹性，但同时也伴随着巨大的不确定性。它们的价格波动与行业景气度高度相关，需要密切关注产业趋势。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 主题投资 | 40% | 布局新兴主题 |
| 趋势突破 | 35% | 突破关键位置时买入 |
| 成长股策略 | 25% | 持有高成长股 |

**策略参数配置**:

```python
ENFP_CONFIG = {
    'position_size': 1.0,
    'holding_period': 'medium',
    'entry_conditions': {
        'theme_emerging': True,
        'breakout_confirmed': True,
        'volume_expansion': 1.5
    },
    'exit_conditions': {
        'theme_mature': True,
        'growth_deceleration': True,
        'profit_target': 0.40
    },
    'stop_loss': 0.12,
    'trailing_stop': 0.12
}
```

**适用市场环境**: 新兴产业爆发期
**风险等级**: 高
**典型标的**: 新能源股、AI概念股

---

### 2.3 守护者型 (Sentinels) - SJ 组合

#### ISTJ - 稳健守护者

**详细特征描述**:  
ISTJ型股票是市场的"压舱石"，它们具有极低的波动性和稳定的现金流。这类股票通常是公用事业、高速公路等防御性行业，价格走势平稳，分红稳定。它们在市场恐慌时提供避风港，但在牛市中跑输大盘。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 趋势跟踪 | 40% | 持有稳健上升趋势 |
| 红利再投资 | 35% | 利用分红复利 |
| 防御配置 | 25% | 市场高风险时增配 |

**策略参数配置**:

```python
ISTJ_CONFIG = {
    'position_size': 1.3,
    'holding_period': 'long',
    'entry_conditions': {
        'dividend_yield': '> 3%',
        'beta_low': 'beta < 0.5',
        'earnings_stable': True
    },
    'exit_conditions': {
        'dividend_cut': True,
        'valuation_expensive': 'PE > 20',
        'regulatory_change': True
    },
    'stop_loss': 0.08,
    'trailing_stop': 0.10
}
```

**适用市场环境**: 熊市、高波动期
**风险等级**: 低
**典型标的**: 公用事业股、REITs

---

#### ISFJ - 价值守望者

**详细特征描述**:  
ISFJ型股票是被市场低估的"宝藏"，它们具有坚实的资产负债表和稳定的盈利能力，但由于缺乏故事性而被忽视。这类股票的估值往往处于历史低位，提供较高的安全边际。投资这类股票需要耐心和长期视角。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 价值投资 | 50% | 买入低估股票 |
| 定投策略 | 30% | 定期定额买入 |
| 安全边际 | 20% | 严格控制买入价 |

**策略参数配置**:

```python
ISFJ_CONFIG = {
    'position_size': 1.2,
    'holding_period': 'long',
    'entry_conditions': {
        'pb_low': 'PB < 1',
        'pe_low': 'PE < 10',
        'dividend_yield': '> 4%',
        'earnings_stable': True
    },
    'exit_conditions': {
        'valuation_recover': 'PE > 15',
        'fundamental_deteriorate': True,
        'profit_target': 0.50
    },
    'stop_loss': 0.10,
    'trailing_stop': None
}
```

**适用市场环境**: 价值洼地、长期底部
**风险等级**: 低
**典型标的**: 银行股、保险股

---

#### ESTJ - 效率机器

**详细特征描述**:  
ESTJ型股票代表着效率和规范，它们通常是大盘股或行业龙头，具有高度透明的信息披露和规范的公司治理。这类股票的价格走势与市场指数高度相关，是构建投资组合的基础资产。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 指数增强 | 45% | 跑赢基准指数 |
| ETF轮动 | 35% | 行业ETF间轮动 |
| 大盘股策略 | 20% | 持有优质大盘股 |

**策略参数配置**:

```python
ESTJ_CONFIG = {
    'position_size': 1.4,
    'holding_period': 'medium_long',
    'entry_conditions': {
        'large_cap': 'market_cap > 100B',
        'liquidity_high': True,
        'index_component': True
    },
    'exit_conditions': {
        'index_rebalance': True,
        'sector_underweight': True,
        'profit_target': 0.20
    },
    'stop_loss': 0.07,
    'trailing_stop': 0.08
}
```

**适用市场环境**: 机构主导市场
**风险等级**: 中低
**典型标的**: 大盘蓝筹股、指数成分股

---

#### ESFJ - 群体领袖

**详细特征描述**:  
ESFJ型股票是市场的"跟随者"，它们的价格走势与整体市场高度同步。这类股票缺乏独立行情，但提供了良好的市场Beta暴露。它们适合作为投资组合的基础配置，用于捕捉市场整体机会。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 行业轮动 | 45% | 根据景气度切换行业 |
| Beta策略 | 35% | 放大市场收益 |
| 指数跟踪 | 20% | 复制指数表现 |

**策略参数配置**:

```python
ESFJ_CONFIG = {
    'position_size': 1.3,
    'holding_period': 'medium',
    'entry_conditions': {
        'sector_momentum': 'top_3_sectors',
        'beta_target': '0.8-1.2',
        'liquidity_good': True
    },
    'exit_conditions': {
        'sector_momentum_decay': True,
        'market_breadth_deteriorate': True,
        'profit_target': 0.15
    },
    'stop_loss': 0.08,
    'trailing_stop': 0.08
}
```

**适用市场环境**: 普涨行情
**风险等级**: 中
**典型标的**: 行业ETF、Beta接近1的股票

---

### 2.4 探险家型 (Explorers) - SP 组合

#### ISTP - 敏捷猎手

**详细特征描述**:  
ISTP型股票是短线交易者的"猎场"，它们具有极高的波动性和快速的价格变动。这类股票通常是市值较小的科技股或概念股，价格走势技术性强，适合技术分析和高频交易。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 波段操作 | 40% | 捕捉波段机会 |
| 日内交易 | 35% | 日内高抛低吸 |
| 技术突破 | 25% | 技术指标突破 |

**策略参数配置**:

```python
ISTP_CONFIG = {
    'position_size': 0.8,
    'holding_period': 'short',
    'entry_conditions': {
        'technical_setup': True,
        'volatility_high': 'ATR > 5%',
        'volume_spike': 2.0
    },
    'exit_conditions': {
        'target_hit': True,
        'time_stop': 3,  # 3天无条件离场
        'reversal_signal': True
    },
    'stop_loss': 0.06,
    'trailing_stop': 0.04
}
```

**适用市场环境**: 高波动期、小票活跃
**风险等级**: 高
**典型标的**: 小盘科技股

---

#### ISFP - 艺术玩家

**详细特征描述**:  
ISFP型股票的价格走势如同抽象艺术，难以捉摸且无规律可循。这类股票通常是ST股或壳资源，价格受随机因素主导，传统分析方法基本失效。它们只适合最激进的投机者。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 均值回归 | 50% | 极端偏离时反向操作 |
| 高频套利 | 30% | 利用微小价差 |
| 事件博弈 | 20% | 赌重组/摘帽 |

**策略参数配置**:

```python
ISFP_CONFIG = {
    'position_size': 0.6,
    'holding_period': 'very_short',
    'entry_conditions': {
        'extreme_deviation': 'z_score > 2',
        'mean_reversion_setup': True,
        'low_liquidity': True
    },
    'exit_conditions': {
        'mean_reversion_complete': True,
        'time_stop': 1,
        'profit_target': 0.05
    },
    'stop_loss': 0.05,
    'trailing_stop': None
}
```

**适用市场环境**: 震荡市
**风险等级**: 极高
**典型标的**: ST股、壳资源

---

#### ESTP - 短线狂徒

**详细特征描述**:  
ESTP型股票是短线客的天堂，它们具有极高的换手率和追涨杀跌特征。这类股票通常是热门概念股，价格走势受情绪主导，波动剧烈。适合风险承受能力强的短线交易者。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 打板策略 | 40% | 追涨涨停板 |
| 游资跟随 | 35% | 跟随主力资金 |
| 热点追逐 | 25% | 快速切换热点 |

**策略参数配置**:

```python
ESTP_CONFIG = {
    'position_size': 0.7,
    'holding_period': 'very_short',
    'entry_conditions': {
        'limit_up_break': True,
        'hot_theme': True,
        'volume_surge': 3.0
    },
    'exit_conditions': {
        'momentum_fade': True,
        'next_day_open': True,
        'profit_target': 0.10
    },
    'stop_loss': 0.05,
    'trailing_stop': None
}
```

**适用市场环境**: 热点炒作期
**风险等级**: 极高
**典型标的**: 热门概念股

---

#### ESFP - 派对动物

**详细特征描述**:  
ESFP型股票是市场的"焦点"，它们的价格走势与消息和情绪高度相关。这类股票通常是网红股或Meme股，价格波动剧烈且难以预测。它们代表了市场最情绪化的一面。

**推荐策略**:

| 策略名称 | 权重 | 说明 |
|----------|------|------|
| 情绪交易 | 45% | 利用情绪波动 |
| 新闻驱动 | 35% | 快速反应新闻 |
| 动量追逐 | 20% | 追涨杀跌 |

**策略参数配置**:

```python
ESFP_CONFIG = {
    'position_size': 0.6,
    'holding_period': 'very_short',
    'entry_conditions': {
        'news_sentiment': 'extreme_positive',
        'social_media_hot': True,
        'volume_explosion': 5.0
    },
    'exit_conditions': {
        'sentiment_peak': True,
        'attention_decay': True,
        'profit_target': 0.08
    },
    'stop_loss': 0.04,
    'trailing_stop': None
}
```

**适用市场环境**: 情绪化市场
**风险等级**: 极高
**典型标的**: 网红股、Meme股

---

## 三、Neo4j 知识图谱数据模型

### 3.1 节点类型定义

#### Stock (股票节点)

```cypher
// Stock节点属性
{
  ticker: string,           // 股票代码 (主键)
  name: string,             // 公司名称
  sector: string,           // 行业
  market_cap: float,        // 市值
  exchange: string,         // 交易所
  created_at: datetime,     // 创建时间
  updated_at: datetime      // 更新时间
}

// 创建Stock节点的Cypher
CREATE (s:Stock {
  ticker: 'AAPL',
  name: 'Apple Inc.',
  sector: 'Technology',
  market_cap: 3000000000000,
  exchange: 'NASDAQ',
  created_at: datetime(),
  updated_at: datetime()
})
```

#### Personality (性格节点)

```cypher
// Personality节点属性
{
  code: string,             // MBTI代码 (主键) - INTJ/ENFP等
  name: string,             // 性格名称 - "战略大师"
  category: string,         // 大类 - Analysts/Diplomats/Sentinels/Explorers
  description: string,      // 详细描述
  risk_level: string,       // 风险等级 - Low/Medium/High/Extreme
  avg_holding_period: string,  // 平均持有周期
  created_at: datetime
}

// 创建Personality节点的Cypher
CREATE (p:Personality {
  code: 'INTJ',
  name: '战略大师',
  category: 'Analysts',
  description: '长周期趋势、强逻辑驱动、独立判断、高Alpha',
  risk_level: 'High',
  avg_holding_period: 'medium_long',
  created_at: datetime()
})
```

#### Strategy (策略节点)

```cypher
// Strategy节点属性
{
  id: string,               // 策略ID (主键)
  name: string,             // 策略名称
  type: string,             // 策略类型 - trend_following/mean_reversion/etc
  description: string,      // 策略描述
  time_frame: string,       // 时间框架 - intraday/short/medium/long
  entry_rules: [string],    // 入场规则
  exit_rules: [string],     // 出场规则
  stop_loss: float,         // 默认止损
  position_size: float,     // 仓位建议
  created_at: datetime
}

// 创建Strategy节点的Cypher
CREATE (st:Strategy {
  id: 'trend_following_001',
  name: '趋势跟踪策略',
  type: 'trend_following',
  description: '跟随市场趋势进行交易',
  time_frame: 'medium',
  entry_rules: ['MA_cross_up', 'ADX > 25'],
  exit_rules: ['MA_cross_down', 'trend_break'],
  stop_loss: 0.10,
  position_size: 1.0,
  created_at: datetime()
})
```

#### MarketRegime (市场环境节点)

```cypher
// MarketRegime节点属性
{
  id: string,               // 环境ID (主键)
  name: string,             // 环境名称 - "牛市"/"熊市"
  vix_level: string,        // 波动率水平 - low/normal/high/extreme
  trend_direction: string,  // 趋势方向 - up/down/sideways
  liquidity: string,        // 流动性 - tight/normal/abundant
  sentiment: string,        // 情绪 - fear/neutral/greed/extreme_greed
  start_date: date,         // 开始日期
  end_date: date            // 结束日期 (可为空)
}

// 创建MarketRegime节点的Cypher
CREATE (mr:MarketRegime {
  id: 'bull_market_2024',
  name: '牛市',
  vix_level: 'low',
  trend_direction: 'up',
  liquidity: 'abundant',
  sentiment: 'greed',
  start_date: date('2024-01-01'),
  end_date: null
})
```

#### PersonalitySnapshot (性格快照节点)

```cypher
// PersonalitySnapshot节点属性 (时序数据)
{
  id: string,               // 快照ID (主键)
  date: date,               // 快照日期
  ie_score: float,          // I/E维度分数
  ns_score: float,          // N/S维度分数
  tf_score: float,          // T/F维度分数
  jp_score: float,          // J/P维度分数
  confidence: float,        // 分类置信度
  feature_vector: [float],  // 32维特征向量
  data_quality: float       // 数据质量评分
}

// 创建PersonalitySnapshot的Cypher
CREATE (ps:PersonalitySnapshot {
  id: 'AAPL_2024-01-15',
  date: date('2024-01-15'),
  ie_score: 0.35,
  ns_score: 0.68,
  tf_score: 0.42,
  jp_score: 0.71,
  confidence: 0.82,
  feature_vector: [0.3, 0.5, ...],  // 32维
  data_quality: 0.95
})
```

---

### 3.2 关系类型定义

#### HAS_PERSONALITY (股票→性格)

```cypher
// 关系属性
{
  start_date: date,         // 性格开始日期
  end_date: date,           // 性格结束日期 (可为空)
  confidence: float,        // 分类置信度
  stability_score: float    // 性格稳定性评分
}

// 创建关系的Cypher
MATCH (s:Stock {ticker: 'AAPL'}), (p:Personality {code: 'INTJ'})
CREATE (s)-[r:HAS_PERSONALITY {
  start_date: date('2024-01-01'),
  end_date: null,
  confidence: 0.82,
  stability_score: 0.75
}]->(p)
```

#### COMPATIBLE_WITH (性格↔策略)

```cypher
// 关系属性
{
  compatibility_score: float,    // 兼容性评分 0-1
  win_rate: float,               // 历史胜率
  avg_return: float,             // 平均收益
  sharpe_ratio: float,           // 夏普比率
  max_drawdown: float,           // 最大回撤
  sample_count: int,             // 样本数量
  last_updated: datetime         // 最后更新时间
}

// 创建关系的Cypher
MATCH (p:Personality {code: 'INTJ'}), (st:Strategy {id: 'trend_following_001'})
CREATE (p)-[r:COMPATIBLE_WITH {
  compatibility_score: 0.85,
  win_rate: 0.62,
  avg_return: 0.15,
  sharpe_ratio: 1.2,
  max_drawdown: -0.12,
  sample_count: 156,
  last_updated: datetime()
}]->(st)
```

#### PERFORMED_IN (策略→市场环境)

```cypher
// 关系属性
{
  win_rate: float,
  avg_return: float,
  sharpe_ratio: float,
  max_drawdown: float,
  sample_count: int
}

// 创建关系的Cypher
MATCH (st:Strategy {id: 'trend_following_001'}), (mr:MarketRegime {id: 'bull_market_2024'})
CREATE (st)-[r:PERFORMED_IN {
  win_rate: 0.68,
  avg_return: 0.18,
  sharpe_ratio: 1.5,
  max_drawdown: -0.08,
  sample_count: 234
}]->(mr)
```

#### MUTATED_TO (性格→性格)

```cypher
// 关系属性
{
  mutation_date: date,           // 转变日期
  trigger_event: string,         // 触发事件
  confidence_delta: float,       // 置信度变化
  reason: string                 // 转变原因
}

// 创建关系的Cypher (成长股变成价值股)
MATCH (p1:Personality {code: 'ENFP'}), (p2:Personality {code: 'ISTJ'})
CREATE (p1)-[r:MUTATED_TO {
  mutation_date: date('2023-06-15'),
  trigger_event: 'growth_deceleration',
  confidence_delta: -0.15,
  reason: '增速放缓，估值回归'
}]->(p2)
```

#### HAS_SNAPSHOT (股票→性格快照)

```cypher
// 关系属性
{
  snapshot_date: date
}

// 创建关系的Cypher
MATCH (s:Stock {ticker: 'AAPL'}), (ps:PersonalitySnapshot {id: 'AAPL_2024-01-15'})
CREATE (s)-[r:HAS_SNAPSHOT {snapshot_date: date('2024-01-15')}]->(ps)
```

#### SNAPSHOT_OF (性格快照→性格)

```cypher
// 创建关系的Cypher
MATCH (ps:PersonalitySnapshot {id: 'AAPL_2024-01-15'}), (p:Personality {code: 'INTJ'})
CREATE (ps)-[:SNAPSHOT_OF]->(p)
```

---

### 3.3 完整Schema创建脚本

```cypher
// ==================== 创建约束和索引 ====================

// 唯一约束
CREATE CONSTRAINT stock_ticker IF NOT EXISTS
FOR (s:Stock) REQUIRE s.ticker IS UNIQUE;

CREATE CONSTRAINT personality_code IF NOT EXISTS
FOR (p:Personality) REQUIRE p.code IS UNIQUE;

CREATE CONSTRAINT strategy_id IF NOT EXISTS
FOR (st:Strategy) REQUIRE st.id IS UNIQUE;

CREATE CONSTRAINT market_regime_id IF NOT EXISTS
FOR (mr:MarketRegime) REQUIRE mr.id IS UNIQUE;

CREATE CONSTRAINT snapshot_id IF NOT EXISTS
FOR (ps:PersonalitySnapshot) REQUIRE ps.id IS UNIQUE;

// 索引
CREATE INDEX stock_sector IF NOT EXISTS
FOR (s:Stock) ON (s.sector);

CREATE INDEX stock_market_cap IF NOT EXISTS
FOR (s:Stock) ON (s.market_cap);

CREATE INDEX personality_category IF NOT EXISTS
FOR (p:Personality) ON (p.category);

CREATE INDEX strategy_type IF NOT EXISTS
FOR (st:Strategy) ON (st.type);

CREATE INDEX snapshot_date IF NOT EXISTS
FOR (ps:PersonalitySnapshot) ON (ps.date);

CREATE INDEX has_personality_dates IF NOT EXISTS
FOR ()-[r:HAS_PERSONALITY]-() ON (r.start_date, r.end_date);

// ==================== 创建基础数据 ====================

// 创建16型性格节点
UNWIND [
  {code: 'INTJ', name: '战略大师', category: 'Analysts', risk: 'High'},
  {code: 'INTP', name: '逻辑解谜者', category: 'Analysts', risk: 'High'},
  {code: 'ENTJ', name: '霸道总裁', category: 'Analysts', risk: 'Medium'},
  {code: 'ENTP', name: '辩论家', category: 'Analysts', risk: 'High'},
  {code: 'INFJ', name: '逆向先知', category: 'Diplomats', risk: 'High'},
  {code: 'INFP', name: '梦想家', category: 'Diplomats', risk: 'Extreme'},
  {code: 'ENFJ', name: '魅力领袖', category: 'Diplomats', risk: 'Medium'},
  {code: 'ENFP', name: '创新先锋', category: 'Diplomats', risk: 'High'},
  {code: 'ISTJ', name: '稳健守护者', category: 'Sentinels', risk: 'Low'},
  {code: 'ISFJ', name: '价值守望者', category: 'Sentinels', risk: 'Low'},
  {code: 'ESTJ', name: '效率机器', category: 'Sentinels', risk: 'Medium'},
  {code: 'ESFJ', name: '群体领袖', category: 'Sentinels', risk: 'Medium'},
  {code: 'ISTP', name: '敏捷猎手', category: 'Explorers', risk: 'High'},
  {code: 'ISFP', name: '艺术玩家', category: 'Explorers', risk: 'Extreme'},
  {code: 'ESTP', name: '短线狂徒', category: 'Explorers', risk: 'Extreme'},
  {code: 'ESFP', name: '派对动物', category: 'Explorers', risk: 'Extreme'}
] AS personality
CREATE (p:Personality {
  code: personality.code,
  name: personality.name,
  category: personality.category,
  risk_level: personality.risk,
  created_at: datetime()
});

// 创建市场环境节点
CREATE (mr1:MarketRegime {
  id: 'bull_market',
  name: '牛市',
  vix_level: 'low',
  trend_direction: 'up',
  liquidity: 'abundant',
  sentiment: 'greed'
});

CREATE (mr2:MarketRegime {
  id: 'bear_market',
  name: '熊市',
  vix_level: 'high',
  trend_direction: 'down',
  liquidity: 'tight',
  sentiment: 'fear'
});

CREATE (mr3:MarketRegime {
  id: 'sideways_market',
  name: '震荡市',
  vix_level: 'normal',
  trend_direction: 'sideways',
  liquidity: 'normal',
  sentiment: 'neutral'
});
```

---

### 3.4 常用查询示例

#### 查询某股票的历史性格演变

```cypher
MATCH (s:Stock {ticker: 'AAPL'})-[r:HAS_PERSONALITY]->(p:Personality)
RETURN s.ticker, p.code, p.name, r.start_date, r.end_date, r.confidence
ORDER BY r.start_date DESC;
```

#### 查询某性格最适合的策略

```cypher
MATCH (p:Personality {code: 'INTJ'})-[r:COMPATIBLE_WITH]->(st:Strategy)
RETURN p.code, st.name, r.compatibility_score, r.win_rate, r.sharpe_ratio
ORDER BY r.compatibility_score DESC
LIMIT 5;
```

#### 查询某股票当前性格和推荐策略

```cypher
MATCH (s:Stock {ticker: 'AAPL'})-[hp:HAS_PERSONALITY]->(p:Personality)
WHERE hp.end_date IS NULL  // 当前性格
MATCH (p)-[cw:COMPATIBLE_WITH]->(st:Strategy)
RETURN s.ticker, p.code, p.name, st.name, cw.compatibility_score
ORDER BY cw.compatibility_score DESC
LIMIT 3;
```

#### 查询性格转变频繁的股票

```cypher
MATCH (s:Stock)-[r:HAS_PERSONALITY]->(p:Personality)
WITH s, count(r) AS personality_changes
WHERE personality_changes > 3
RETURN s.ticker, s.name, personality_changes
ORDER BY personality_changes DESC
LIMIT 10;
```

#### 查询某策略在某种市场环境下的表现

```cypher
MATCH (st:Strategy {id: 'trend_following_001'})-[r:PERFORMED_IN]->(mr:MarketRegime)
WHERE mr.name = '牛市'
RETURN st.name, mr.name, r.win_rate, r.avg_return, r.sharpe_ratio;
```

#### 更新性格兼容性评分

```cypher
MATCH (p:Personality {code: 'INTJ'})-[r:COMPATIBLE_WITH]->(st:Strategy {id: 'trend_following_001'})
SET r.win_rate = 0.65,
    r.avg_return = 0.16,
    r.sample_count = r.sample_count + 1,
    r.last_updated = datetime()
RETURN p.code, st.name, r.win_rate;
```

#### 创建新的性格快照

```cypher
// 创建快照节点
CREATE (ps:PersonalitySnapshot {
  id: 'AAPL_2024-02-01',
  date: date('2024-02-01'),
  ie_score: 0.38,
  ns_score: 0.72,
  tf_score: 0.45,
  jp_score: 0.68,
  confidence: 0.85
})

// 关联到股票
WITH ps
MATCH (s:Stock {ticker: 'AAPL'})
CREATE (s)-[:HAS_SNAPSHOT {snapshot_date: date('2024-02-01')}]->(ps)

// 关联到性格类型
WITH ps
MATCH (p:Personality {code: 'INTJ'})
CREATE (ps)-[:SNAPSHOT_OF]->(p);
```

---

### 3.5 Python集成代码

```python
from py2neo import Graph, Node, Relationship
from datetime import datetime, date

class PersonalityKnowledgeGraph:
    """股性知识图谱操作类"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.graph = Graph(uri, auth=(user, password))
    
    def create_stock(self, ticker: str, name: str, sector: str, 
                     market_cap: float, exchange: str):
        """创建股票节点"""
        query = """
        MERGE (s:Stock {ticker: $ticker})
        SET s.name = $name,
            s.sector = $sector,
            s.market_cap = $market_cap,
            s.exchange = $exchange,
            s.updated_at = datetime()
        RETURN s
        """
        return self.graph.run(query, ticker=ticker, name=name, 
                            sector=sector, market_cap=market_cap, 
                            exchange=exchange).data()
    
    def create_personality_snapshot(self, ticker: str, 
                                    ie_score: float, ns_score: float,
                                    tf_score: float, jp_score: float,
                                    snapshot_date: date = None):
        """创建性格快照"""
        snapshot_date = snapshot_date or date.today()
        snapshot_id = f"{ticker}_{snapshot_date}"
        
        # 确定MBTI代码
        mbti_code = self._scores_to_mbti(ie_score, ns_score, tf_score, jp_score)
        
        query = """
        // 创建快照节点
        CREATE (ps:PersonalitySnapshot {
            id: $snapshot_id,
            date: $snapshot_date,
            ie_score: $ie_score,
            ns_score: $ns_score,
            tf_score: $tf_score,
            jp_score: $jp_score,
            confidence: $confidence
        })
        
        // 关联到股票
        WITH ps
        MATCH (s:Stock {ticker: $ticker})
        CREATE (s)-[:HAS_SNAPSHOT {snapshot_date: $snapshot_date}]->(ps)
        
        // 关联到性格类型
        WITH ps
        MATCH (p:Personality {code: $mbti_code})
        CREATE (ps)-[:SNAPSHOT_OF]->(p)
        
        RETURN ps.id, p.code
        """
        
        confidence = min(abs(ie_score-0.5), abs(ns_score-0.5), 
                        abs(tf_score-0.5), abs(jp_score-0.5)) * 2
        
        return self.graph.run(query, snapshot_id=snapshot_id,
                            snapshot_date=snapshot_date,
                            ie_score=ie_score, ns_score=ns_score,
                            tf_score=tf_score, jp_score=jp_score,
                            confidence=confidence, ticker=ticker,
                            mbti_code=mbti_code).data()
    
    def _scores_to_mbti(self, ie: float, ns: float, tf: float, jp: float) -> str:
        """将四维分数转换为MBTI代码"""
        code = ""
        code += "E" if ie > 0.5 else "I"
        code += "N" if ns > 0.5 else "S"
        code += "F" if tf > 0.5 else "T"
        code += "J" if jp > 0.5 else "P"
        return code
    
    def get_recommended_strategies(self, ticker: str, top_n: int = 3) -> list:
        """获取推荐策略"""
        query = """
        MATCH (s:Stock {ticker: $ticker})-[:HAS_SNAPSHOT]->(ps:PersonalitySnapshot)
        WITH ps ORDER BY ps.date DESC LIMIT 1
        MATCH (ps)-[:SNAPSHOT_OF]->(p:Personality)
        MATCH (p)-[cw:COMPATIBLE_WITH]->(st:Strategy)
        RETURN p.code AS personality,
               st.name AS strategy,
               st.id AS strategy_id,
               cw.compatibility_score AS score,
               cw.win_rate AS win_rate,
               cw.sharpe_ratio AS sharpe
        ORDER BY cw.compatibility_score DESC
        LIMIT $top_n
        """
        return self.graph.run(query, ticker=ticker, top_n=top_n).data()
    
    def update_compatibility(self, personality_code: str, strategy_id: str,
                           win_rate: float, avg_return: float, 
                           sharpe_ratio: float, sample_count: int = 1):
        """更新性格-策略兼容性"""
        query = """
        MATCH (p:Personality {code: $personality_code})
        MATCH (st:Strategy {id: $strategy_id})
        MERGE (p)-[cw:COMPATIBLE_WITH]->(st)
        ON CREATE SET cw.win_rate = $win_rate,
                      cw.avg_return = $avg_return,
                      cw.sharpe_ratio = $sharpe_ratio,
                      cw.sample_count = $sample_count,
                      cw.last_updated = datetime()
        ON MATCH SET cw.win_rate = (cw.win_rate * cw.sample_count + $win_rate * $sample_count) 
                                  / (cw.sample_count + $sample_count),
                     cw.avg_return = (cw.avg_return * cw.sample_count + $avg_return * $sample_count) 
                                   / (cw.sample_count + $sample_count),
                     cw.sample_count = cw.sample_count + $sample_count,
                     cw.last_updated = datetime()
        RETURN p.code, st.name, cw.win_rate
        """
        return self.graph.run(query, personality_code=personality_code,
                            strategy_id=strategy_id, win_rate=win_rate,
                            avg_return=avg_return, sharpe_ratio=sharpe_ratio,
                            sample_count=sample_count).data()
```

---

## 四、总结

本设计文档完整定义了 QuantClaw Pro - MBTI 股性分类系统的三个核心模块：

1. **四维度计算器**: 将32维特征映射到MBTI四维性格，使用历史数据标准化和Sigmoid函数
2. **16型策略库**: 为每种性格类型定义了详细的特征描述、策略参数和风险管理
3. **Neo4j知识图谱**: 完整的节点/关系Schema和Python集成代码

**下一步**: 进入开发实施阶段，按Phase 1-5逐步实现各模块。

---

**文档版本**: v1.0  
**最后更新**: 2026-02-23  
**作者**: QuantClaw Team
