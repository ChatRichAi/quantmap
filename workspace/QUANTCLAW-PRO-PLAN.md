# QuantClaw Pro - 智能量化交易框架 (MBTI版)

> 不止执行策略，更要理解股性、感知择时、自适应匹配
> 给每只股票做MBTI，给每个策略找最适合的"性格伴侣"

---

## 🧠 核心概念

### 什么是「股性」？
股票的"性格"——它在不同市场环境下的行为模式：
- **波动特征**: 暴涨暴跌型 vs 慢性子稳如狗
- **节奏偏好**: 早盘冲锋型 vs 尾盘偷袭型
- **情绪敏感度**: 跟风狗 vs 独行侠
- **周期属性**: 短跑选手 vs 马拉松选手

### 什么是「策略择时性」？
策略也有"性格"——它在什么市场状态下表现最好：
- **趋势策略**: 适合"决断型"股票 (J型)
- **均值回归**: 适合"摇摆型"股票 (P型)
- **突破策略**: 适合"敏感型"股票 (S型)
- **套利策略**: 适合"理性型"股票 (T型)

### MBTI 量化映射

| MBTI | 股票特征 | 适合策略 | 市场环境 |
|-----|---------|---------|---------|
| **ISTJ** | 大盘股、低波动、规律性强 | 均线回归、定投 | 震荡市 |
| **ESTP** | 小盘妖股、高波动、突发行情 | 突破追涨、事件驱动 | 牛市初期 |
| **INTJ** | 成长股、趋势明确、独立行情 | 趋势跟踪、动量 | 主升浪 |
| **ESFP** | 题材股、情绪驱动、跟风明显 | 情绪套利、龙头战法 | 热点市 |
| **INFP** | 价值股、反人性、底部徘徊 | 逆向投资、价值挖掘 | 熊市末期 |

---

## 🏗️ 系统架构 (三层认知)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Layer 3: 决策层 (Brain)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  股性识别器   │  │  策略匹配器   │  │  择时引擎    │          │
│  │ StockProfiler│  │StrategyMatch │  │ MarketTimer  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                     │
│                  ┌─────────────────┐                           │
│                  │   自适应决策器   │                           │
│                  │ AdaptiveBrain   │                           │
│                  └────────┬────────┘                           │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                    Layer 2: 认知层 (Mind)                        │
│  ┌────────────────────────┼────────────────────────┐           │
│  │                        ▼                        │           │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────┐ │           │
│  │  │  股票记忆库   │ │  策略记忆库   │ │市场环境库│ │           │
│  │  │StockMemory   │ │StrategyMemory│ │MarketMemo│ │           │
│  │  └──────────────┘ └──────────────┘ └──────────┘ │           │
│  │                                                 │           │
│  │  知识图谱连接: "AAPL在财报季表现为ESTP型"         │           │
│  │               "趋势策略在INTJ型股票上胜率68%"      │           │
│  └─────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                    Layer 1: 感知层 (Sense)                       │
│  ┌────────────────────────┼────────────────────────┐           │
│  │                        ▼                        │           │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │           │
│  │  │ 价格感知  │ │ 情绪感知  │ │ 事件感知  │        │           │
│  │  │PriceSense│ │Sentiment │ │ EventSense│        │           │
│  │  └──────────┘ └──────────┘ └──────────┘        │           │
│  │                                                 │           │
│  │  数据流: K线 → 指标 → 特征 → 模式识别            │           │
│  └─────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔬 核心模块设计

### 1. 股性分析引擎 (Stock Personality Profiler)

#### 1.1 多维度特征提取
```typescript
interface StockPersonality {
  // 基础基因
  symbol: string;
  name: string;
  sector: string;
  marketCap: 'large' | 'mid' | 'small' | 'micro';
  
  // 波动性格 (Volatility Profile)
  volatility: {
    daily: number;        // 日均波动率
    weekly: number;       // 周波动率
    monthly: number;      // 月波动率
    pattern: 'stable' | 'explosive' | 'cyclical' | 'chaotic';
    burstFrequency: number; // 爆发频率
  };
  
  // 时间性格 (Temporal Profile)
  temporal: {
    intradayPattern: {    // 日内模式
      morning: 'aggressive' | 'moderate' | 'quiet';
      afternoon: 'aggressive' | 'moderate' | 'quiet';
      close: 'aggressive' | 'moderate' | 'quiet';
    };
    dayOfWeek: number[];  // 周内表现 [周一, 周二, ...]
    monthlyPattern: 'start-heavy' | 'end-heavy' | 'mid-heavy' | 'even';
    seasonality: {        // 季节性
      q1: number; q2: number; q3: number; q4: number;
    };
  };
  
  // 情绪性格 (Sentiment Profile)
  sentiment: {
    correlationWithMarket: number;  // 与市场相关性
    newsSensitivity: number;        // 新闻敏感度
    socialHype: number;             // 社交热度敏感度
    earningsReaction: 'violent' | 'moderate' | 'muted'; // 财报反应
  };
  
  // 技术性格 (Technical Profile)
  technical: {
    trendiness: number;      // 趋势性 (0-1)
    meanReversion: number;   // 均值回归性 (0-1)
    breakoutQuality: number; // 突破质量 (0-1)
    supportResistanceStrength: number; // 支撑阻力强度
    volumeProfile: 'consistent' | 'spiky' | 'front-loaded' | 'back-loaded';
  };
  
  // MBTI 分类结果
  mbti: {
    ei: 'E' | 'I';  // 外向/内向 (与市场关联度)
    sn: 'S' | 'N';  // 实感/直觉 (对消息反应模式)
    tf: 'T' | 'F';  // 思考/情感 (涨跌是否理性)
    jp: 'J' | 'P';  // 判断/知觉 (趋势性vs摇摆性)
    fullType: string; // e.g., "ESTP"
    confidence: number; // 分类置信度
  };
  
  // 动态标签
  tags: string[];  // e.g., ["earnings-play", "meme-stock", "dividend-aristocrat"]
  
  // 更新时间
  lastUpdated: Date;
  dataPoints: number; // 用于分析的数据点数量
}
```

#### 1.2 MBTI 计算算法
```typescript
class MBTICalculator {
  calculateEI(stock: StockData): 'E' | 'I' {
    // E (外向): 与市场高度相关，跟随大盘
    // I (内向): 独立行情，有自己的节奏
    const marketCorrelation = this.calcMarketCorrelation(stock);
    return marketCorrelation > 0.7 ? 'E' : 'I';
  }
  
  calculateSN(stock: StockData): 'S' | 'N' {
    // S (实感): 对具体消息反应明确，可预测
    // N (直觉): 经常"莫名其妙"涨跌，难预测
    const predictability = this.calcPredictability(stock);
    const newsReactionConsistency = this.calcNewsReactionConsistency(stock);
    return (predictability + newsReactionConsistency) / 2 > 0.6 ? 'S' : 'N';
  }
  
  calculateTF(stock: StockData): 'T' | 'F' {
    // T (思考): 涨跌有基本面逻辑支撑
    // F (情感): 情绪驱动，FOMO/FUD明显
    const fundamentalCorrelation = this.calcFundamentalCorrelation(stock);
    const sentimentRatio = this.calcSentimentRatio(stock);
    return fundamentalCorrelation > sentimentRatio ? 'T' : 'F';
  }
  
  calculateJP(stock: StockData): 'J' | 'P' {
    // J (判断): 趋势明确，一旦启动会持续
    // P (知觉): 摇摆不定，反复无常
    const trendConsistency = this.calcTrendConsistency(stock);
    const reversalFrequency = this.calcReversalFrequency(stock);
    return trendConsistency > reversalFrequency ? 'J' : 'P';
  }
}
```

#### 1.3 自动挖掘流程
```
每日收盘后自动运行:

1. 数据采集
   └── 获取当日全市场数据

2. 特征计算
   └── 波动率、相关性、技术形态、资金流向

3. 模式识别
   └── 聚类分析找出相似股性股票
   └── 异常检测发现性格变化

4. MBTI 分类
   └── 计算四个维度得分
   └── 输出 16 型分类结果

5. 知识存储
   └── 存入 Stock Memory
   └── 关联相似股票
   └── 标记性格变化事件

6. 策略匹配更新
   └── 重新计算股票-策略匹配度
   └── 更新推荐策略列表
```

---

### 2. 策略择时性分析 (Strategy Timing Profiler)

#### 2.1 策略人格画像
```typescript
interface StrategyProfile {
  id: string;
  name: string;
  type: 'trend' | 'mean-reversion' | 'breakout' | 'arbitrage' | 'event-driven';
  
  // 策略MBTI偏好
  preferredMBTI: {
    types: string[];           // e.g., ["ESTP", "ESTJ", "ENTJ"]
    weights: Record<string, number>; // 每种类型权重
  };
  
  // 市场环境偏好
  marketConditions: {
    trend: 'strong-up' | 'weak-up' | 'sideways' | 'weak-down' | 'strong-down' | 'any';
    volatility: 'low' | 'medium' | 'high' | 'extreme' | 'adaptive';
    volume: 'low' | 'normal' | 'high' | 'any';
    sentiment: 'fear' | 'neutral' | 'greed' | 'extreme-fear' | 'extreme-greed' | 'any';
  };
  
  // 时间偏好
  timing: {
    bestHours: number[];       // e.g., [9, 10, 14] 最适合的小时
    bestDays: number[];        // e.g., [1, 2, 3] 最适合的星期几
    bestMonths: number[];      // e.g., [1, 4, 10, 11] 最适合的月份
    holdingPeriod: 'intraday' | 'swing' | 'position' | 'long-term';
  };
  
  // 历史表现分析
  performance: {
    winRate: number;
    profitFactor: number;
    sharpeRatio: number;
    maxDrawdown: number;
    avgTrade: number;
    
    // 按MBTI类型的表现
    byMBTI: Record<string, {
      winRate: number;
      avgReturn: number;
      sampleSize: number;
    }>;
    
    // 按市场环境的表现
    byCondition: Record<string, {
      winRate: number;
      avgReturn: number;
    }>;
  };
  
  // 策略状态
  status: 'active' | 'paused' | 'backtesting';
  confidence: number;  // 当前置信度
  lastOptimized: Date;
}
```

#### 2.2 择时评分算法
```typescript
class TimingScoreCalculator {
  calculateTimingScore(
    strategy: StrategyProfile,
    stock: StockPersonality,
    marketCondition: MarketCondition
  ): TimingScore {
    
    // 1. 股性匹配分 (0-40)
    const personalityMatch = this.calcPersonalityMatch(
      strategy.preferredMBTI, 
      stock.mbti
    );
    
    // 2. 市场环境分 (0-30)
    const conditionMatch = this.calcConditionMatch(
      strategy.marketConditions,
      marketCondition
    );
    
    // 3. 时间窗口分 (0-20)
    const timingMatch = this.calcTimingMatch(
      strategy.timing,
      new Date()
    );
    
    // 4. 历史表现分 (0-10)
    const historicalPerformance = this.getHistoricalScore(
      strategy,
      stock.symbol
    );
    
    const totalScore = personalityMatch + conditionMatch + 
                       timingMatch + historicalPerformance;
    
    return {
      total: totalScore,
      breakdown: {
        personality: personalityMatch,
        condition: conditionMatch,
        timing: timingMatch,
        historical: historicalPerformance
      },
      recommendation: totalScore > 70 ? 'strong' : 
                      totalScore > 50 ? 'moderate' : 'weak'
    };
  }
}
```

---

### 3. 自适应决策引擎 (Adaptive Brain)

#### 3.1 决策流程
```typescript
class AdaptiveBrain {
  async makeDecision(context: TradingContext): Promise<Decision> {
    // 1. 感知当前市场
    const marketCondition = await this.senseMarket();
    
    // 2. 获取目标股票股性
    const stock = await this.stockMemory.get(context.symbol);
    
    // 3. 获取所有可用策略
    const strategies = await this.strategyMemory.getActiveStrategies();
    
    // 4. 计算每个策略的择时得分
    const scores = await Promise.all(
      strategies.map(async s => ({
        strategy: s,
        score: await this.timingCalculator.calculate(s, stock, marketCondition)
      }))
    );
    
    // 5. 筛选高分配对
    const candidates = scores
      .filter(s => s.score.total > 60)
      .sort((a, b) => b.score.total - a.score.total);
    
    // 6. 检查风控
    for (const candidate of candidates) {
      const riskCheck = await this.riskAgent.check({
        strategy: candidate.strategy,
        symbol: context.symbol,
        score: candidate.score
      });
      
      if (riskCheck.approved) {
        // 7. 生成交易信号
        const signal = await this.generateSignal(
          candidate.strategy,
          context
        );
        
        return {
          action: 'execute',
          strategy: candidate.strategy.id,
          signal,
          confidence: candidate.score.total,
          reasoning: this.explainDecision(candidate, stock, marketCondition)
        };
      }
    }
    
    return { action: 'hold', reason: 'No suitable strategy found' };
  }
}
```

#### 3.2 决策解释器
系统不仅要决策，还要解释为什么：

```typescript
interface DecisionExplanation {
  summary: string;  // 一句话总结
  
  stockAnalysis: {
    mbtiType: string;
    personalityTraits: string[];
    recentBehavior: string;
  };
  
  strategyMatch: {
    chosenStrategy: string;
    matchScore: number;
    matchReasons: string[];  // e.g., ["该策略在ESTP型股票上历史胜率72%", "当前市场环境适合趋势跟踪"]
  };
  
  timingAnalysis: {
    marketCondition: string;
    timingScore: number;
    timingFactors: string[];
  };
  
  riskAssessment: {
    riskLevel: 'low' | 'medium' | 'high';
    riskFactors: string[];
    positionSuggestion: string;
  };
}

// 示例输出:
// {
//   summary: "建议对TSLA使用突破追涨策略，匹配度82%",
//   stockAnalysis: {
//     mbtiType: "ESTP",
//     personalityTraits: ["高波动", "消息敏感", "早盘活跃"],
//     recentBehavior: "近5日有3次突破形态，成功率为100%"
//   },
//   strategyMatch: {
//     chosenStrategy: "breakout-momentum",
//     matchScore: 82,
//     matchReasons: [
//       "该策略在ESTP型股票上历史胜率72%",
//       "TSLA当前处于突破后的动量延续期",
//       "早盘时段与策略最佳执行时间匹配"
//     ]
//   },
//   ...
// }
```

---

### 4. 知识图谱与学习

#### 4.1 实体类型
```
[Stock] -> hasMBTI -> [MBTIType]
      -> similarTo -> [Stock]
      -> performsIn -> [MarketCondition]
      -> suitableFor -> [Strategy]

[Strategy] -> prefersMBTI -> [MBTIType]
         -> performsBest -> [MarketCondition]
         -> hasWinRate -> [Performance]

[Trade] -> executedBy -> [Strategy]
      -> onStock -> [Stock]
      -> inCondition -> [MarketCondition]
      -> resultedIn -> [Outcome]
```

#### 4.2 自动学习循环
```
1. 每日盘后:
   - 分析当日所有交易
   - 更新策略-股票匹配表现
   - 识别新的股性模式

2. 每周:
   - 重新计算所有MBTI分类
   - 更新相似股票集群
   - 优化策略参数

3. 每月:
   - 深度回测所有策略组合
   - 更新策略择时性模型
   - 生成策略表现报告

4. 持续:
   - 监控股票性格变化
   - 检测策略失效信号
   - 自动调整推荐权重
```

---

## 🎯 智能功能特性

### 1. 股性预警
当股票的"性格"发生变化时自动提醒：
```
"AAPL 股性发生变化：从 ISTJ → ESTP"
"原因：近20日波动率从 1.2% 上升至 3.8%，与市场相关性从 0.9 下降至 0.4"
"建议：当前不适合使用均值回归策略，考虑切换至突破策略"
```

### 2. 策略推荐
根据当前持仓和市场状态推荐最佳策略：
```
"基于当前市场环境 (震荡市 + 低波动)，推荐以下策略组合："

"1. 网格交易 (置信度: 85%)"
"   推荐标的: AAPL, MSFT, JNJ"
"   原因: 这些ISTJ型股票在震荡市表现稳定"

"2. 日内 scalp (置信度: 72%)"
"   推荐标的: TSLA, NVDA, AMD"
"   原因: ESTP型股票早盘波动提供 scalp 机会"
```

### 3. 错误反思
交易失败后自动分析原因：
```
"交易复盘: NVDA 做空失败"

"原因分析:"
"- 错误地将 NVDA 分类为 ESTP (波动型)"
"- 实际应为 ESFP (情绪型)"
"- 忽略了当日 AI 板块整体情绪高涨的信号"

"知识更新:"
"- 更新 NVDA MBTI 类型: ESTP → ESFP"
"- 增加情绪指标权重"
"- 记录该模式以供未来识别"
```

### 4. 市场状态感知
实时识别市场环境并调整策略：
```typescript
interface MarketCondition {
  regime: 'trending-up' | 'trending-down' | 'mean-reverting' | 'breakout' | 'choppy';
  volatilityRegime: 'low' | 'normal' | 'high' | 'extreme';
  sentiment: 'extreme-fear' | 'fear' | 'neutral' | 'greed' | 'extreme-greed';
  breadth: 'strong' | 'healthy' | 'weak' | 'deteriorating';
  correlation: 'high' | 'normal' | 'low';  // 个股相关性
  
  // 预测
  forecast: {
    nextDayRegime: string;
    confidence: number;
    keyLevels: { support: number; resistance: number };
  };
}
```

---

## 🛠️ 技术实现

### 数据流架构
```
实时数据流:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 交易所    │───>│ 特征提取  │───>│ 模式识别  │───>│ 决策引擎  │
│ WebSocket│    │ 管道      │    │ 引擎      │    │           │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                     │
                              ┌──────────────────────┼──────┐
                              ▼                      ▼      ▼
                        ┌──────────┐           ┌──────────┐┌──────────┐
                        │ Nowledge │           │  交易    ││  通知    │
                        │   Mem    │           │  执行    ││  推送    │
                        └──────────┘           └──────────┘└──────────┘

批处理流 (每日/每周):
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 历史数据  │───>│ 股性分析  │───>│ MBTI分类  │───>│ 知识存储  │
│ 数据库    │    │ 引擎      │    │ 更新      │    │           │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 核心算法
- **股性聚类**: K-Means / DBSCAN 基于波动率、相关性、技术特征
- **MBTI分类**: 决策树 / 随机森林 基于历史行为模式
- **策略匹配**: 协同过滤 + 贝叶斯优化
- **择时预测**: LSTM / Transformer 时间序列预测
- **强化学习**: PPO / SAC 用于策略权重动态调整

---

## 📊 预期能力

运行3个月后，系统应该能够：

| 能力 | 描述 | 准确率目标 |
|-----|------|----------|
| **股性识别** | 自动对新股票进行MBTI分类 | 80%+ |
| **策略匹配** | 推荐最适合某股票当前状态的策略 | 75%+ |
| **择时判断** | 判断当前是否适合执行某策略 | 70%+ |
| **性格变化检测** | 及时发现股票行为模式变化 | 90%+ |
| **市场状态识别** | 实时识别市场环境 | 85%+ |

---

## 🚀 实施路线图

### Phase 1: 感知层 (Week 1-2)
- 数据采集管道
- 特征提取引擎
- 基础指标计算

### Phase 2: 认知层 (Week 3-4)
- 股性分析引擎
- MBTI自动分类
- 知识图谱构建

### Phase 3: 决策层 (Week 5-6)
- 策略择时分析
- 自适应决策引擎
- 解释器模块

### Phase 4: 学习与进化 (Week 7-8)
- 交易反馈学习
- 策略参数优化
- 错误反思系统

### Phase 5: 集成与UI (Week 9-10)
- CLI工具
- Web仪表盘
- 实时监控面板

---

## 💡 与原版 btc-monitor/MU 计划的对比

| 维度 | 原版计划 | QuantClaw Pro |
|-----|---------|--------------|
| **策略执行** | 固定规则 | 自适应选择 |
| **股票认知** | 无 | 深度股性分析 |
| **策略认知** | 无 | 择时性分析 |
| **匹配机制** | 人工指定 | 智能推荐 |
| **学习能力** | 无 | 持续进化 |
| **解释能力** | 无 | 决策可解释 |
| **复杂度** | 中等 | 高 |
| **预期收益** | 稳定 | 优化+ |

---

**这是你要的智能量化系统吗？还是还有想调整的地方？**
