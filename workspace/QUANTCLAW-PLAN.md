# QuantClaw - 量化交易版 OpenClaw 实现计划

> 基于 OpenClaw 框架打造的个人量化交易系统
> 目标：模块化、可扩展、支持多策略、多品种的自动化量化交易框架

---

## 📊 项目概述

### 愿景
构建一个类似 OpenClaw 的量化交易框架，具备：
- **策略管理**：类似 Cron Job 的策略调度系统
- **记忆系统**：交易日志、策略表现的 Nowledge Mem 集成
- **技能插件**：技术指标、数据源、通知等可插拔技能
- **Agent 系统**：分析 Agent、风控 Agent、执行 Agent 协同工作
- **多市场支持**：Crypto、股票、期货等

### 核心借鉴 OpenClaw 的组件
| OpenClaw 组件 | QuantClaw 对应组件 | 功能描述 |
|--------------|-------------------|---------|
| Cron Job 系统 | Strategy Scheduler | 策略调度与定时执行 |
| Nowledge Mem | Trade Memory | 交易记忆与知识图谱 |
| Skills | Trading Skills | 技术指标、数据源等技能 |
| Agents | Trading Agents | 分析、风控、执行代理 |
| Gateway | Exchange Gateway | 交易所连接与 API 管理 |

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      QuantClaw Framework                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Strategy   │  │   Strategy   │  │   Strategy   │       │
│  │   Engine     │  │   Scheduler  │  │   Backtest   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │               │
│  ┌──────▼─────────────────▼─────────────────▼───────┐       │
│  │              Trading Agent Layer                  │       │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │       │
│  │  │ Analysis │ │  Risk    │ │Execution │         │       │
│  │  │  Agent   │ │  Agent   │ │  Agent   │         │       │
│  │  └──────────┘ └──────────┘ └──────────┘         │       │
│  └──────────────────────────────────────────────────┘       │
│         │                 │                 │               │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐         │
│  │   Skills    │  │   Skills    │  │   Skills    │         │
│  │  Indicators │  │   Data      │  │  Notify     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │               Exchange Gateway Layer                  │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │  │
│  │  │Binance │ │  OKX   │ │Alpaca  │ │  IBKR  │        │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Trade Memory (Nowledge Mem)              │  │
│  │  - 交易记录存储       - 策略表现分析                    │  │
│  │  - 市场状态记忆       - 决策上下文                      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 详细实现计划

### Phase 1: 核心框架搭建 (Week 1-2)

#### 1.1 项目初始化
- [ ] 创建 `quantclaw/` 项目目录结构
- [ ] 初始化 TypeScript + Node.js 项目
- [ ] 配置 ESLint、Prettier、Jest 测试框架
- [ ] 设计核心配置系统 (`quantclaw.config.yaml`)

```
quantclaw/
├── src/
│   ├── core/              # 核心框架
│   │   ├── config.ts      # 配置管理（类似 OpenClaw 的 loadConfig）
│   │   ├── scheduler.ts   # 策略调度器
│   │   ├── event-bus.ts   # 事件总线
│   │   └── logger.ts      # 日志系统
│   ├── agents/            # Agent 系统
│   │   ├── base-agent.ts
│   │   ├── analysis-agent.ts
│   │   ├── risk-agent.ts
│   │   └── execution-agent.ts
│   ├── strategies/        # 策略目录
│   │   ├── base-strategy.ts
│   │   └── examples/
│   ├── skills/            # 技能插件
│   │   ├── indicators/    # 技术指标
│   │   ├── data-source/   # 数据源
│   │   └── notification/  # 通知技能
│   ├── exchange/          # 交易所接口
│   │   ├── base-exchange.ts
│   │   ├── binance.ts
│   │   └── alpaca.ts
│   └── memory/            # 交易记忆
│       └── trade-memory.ts
├── tests/
├── docs/
└── quantclaw.config.yaml
```

#### 1.2 配置系统 (借鉴 OpenClaw Cron Job)
```yaml
# quantclaw.config.yaml
user:
  id: "user_xxx"
  risk_profile: "moderate"  # conservative | moderate | aggressive

gateways:
  binance:
    api_key: ${BINANCE_API_KEY}
    api_secret: ${BINANCE_API_SECRET}
    testnet: true
  alpaca:
    api_key: ${ALPACA_API_KEY}
    api_secret: ${ALPACA_API_SECRET}
    paper: true

strategies:
  btc_breakout:
    enabled: true
    symbol: "BTCUSDT"
    exchange: "binance"
    timeframe: "5m"
    schedule: "*/5 * * * *"  # 每5分钟
    max_position: 0.1        # 最大10%资金
    params:
      breakout_threshold: 71000
      volume_multiplier: 1.5
      
  mu_swing:
    enabled: true
    symbol: "MU"
    exchange: "alpaca"
    timeframe: "1h"
    schedule: "0 * * * *"    # 每小时
    max_position: 0.05

memory:
  enabled: true
  nmem_endpoint: "http://127.0.0.1:14242"
  auto_capture: true
  auto_recall: true

notifications:
  whatsapp:
    enabled: true
  telegram:
    enabled: false
```

#### 1.3 策略调度器 (Strategy Scheduler)
借鉴 OpenClaw 的 Cron Job 机制：
- 策略配置自动注入 `owner` 字段
- 每个策略独立 `sessionKey` 追踪
- 状态管理：`running` / `paused` / `error`

```typescript
// src/core/scheduler.ts
interface StrategyJob {
  id: string;
  name: string;
  owner: string;           // 自动注入
  sessionKey: string;      // 自动解析
  schedule: string;        // cron 表达式
  symbol: string;
  status: 'running' | 'paused' | 'error';
  lastRun: Date;
  nextRun: Date;
  runCount: number;
  errorCount: number;
}

class StrategyScheduler {
  async add(strategyConfig: StrategyConfig): Promise<StrategyJob>
  async list(userId: string): Promise<StrategyJob[]>
  async pause(jobId: string): Promise<void>
  async resume(jobId: string): Promise<void>
  async remove(jobId: string): Promise<void>
}
```

---

### Phase 2: 技能系统 (Week 3-4)

#### 2.1 数据源技能 (Data Source Skills)
```typescript
// src/skills/data-source/binance-skill.ts
interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  timestamp: number;
  fundingRate?: number;
}

class BinanceDataSkill {
  async getPrice(symbol: string): Promise<number>
  async getKlines(symbol: string, timeframe: string, limit: number): Promise<OHLCV[]>
  async getFundingRate(symbol: string): Promise<number>
  async getOrderBook(symbol: string, depth: number): Promise<OrderBook>
}
```

#### 2.2 技术指标技能 (Indicator Skills)
```typescript
// src/skills/indicators/technical-skill.ts
class TechnicalIndicatorSkill {
  // 趋势指标
  sma(data: number[], period: number): number[]
  ema(data: number[], period: number): number[]
  macd(data: number[], fast: number, slow: number, signal: number): MACDResult
  
  // 波动指标
  rsi(data: number[], period: number): number[]
  bollinger(data: number[], period: number, stdDev: number): BollingerResult
  atr(data: OHLCV[], period: number): number[]
  
  // 成交量指标
  obv(data: OHLCV[]): number[]
  vwma(data: OHLCV[], period: number): number[]
}
```

#### 2.3 通知技能 (Notification Skills)
- WhatsApp 通知（复用现有 btc-monitor 逻辑）
- Telegram 通知
- Email 通知
- 系统通知

---

### Phase 3: Agent 系统 (Week 5-6)

#### 3.1 分析 Agent (Analysis Agent)
```typescript
// src/agents/analysis-agent.ts
class AnalysisAgent extends BaseAgent {
  async analyze(context: MarketContext): Promise<AnalysisResult> {
    // 1. 加载历史记忆
    const memory = await this.tradeMemory.search({
      query: `${context.symbol} trend analysis`,
      limit: 5
    });
    
    // 2. 技术分析
    const technical = await this.runTechnicalAnalysis(context);
    
    // 3. 基本面扫描（如有数据）
    const fundamental = await this.runFundamentalAnalysis(context);
    
    // 4. 情绪分析（可选）
    const sentiment = await this.runSentimentAnalysis(context);
    
    return {
      signal: 'buy' | 'sell' | 'hold',
      confidence: 0.85,
      reasoning: [...],
      indicators: {...}
    };
  }
}
```

#### 3.2 风控 Agent (Risk Agent)
```typescript
// src/agents/risk-agent.ts
class RiskAgent extends BaseAgent {
  async check(context: TradeContext): Promise<RiskCheckResult> {
    const checks = await Promise.all([
      this.checkPositionLimit(context),      // 仓位限制
      this.checkDailyLossLimit(context),     // 日亏损限制
      this.checkDrawdownLimit(context),      // 回撤限制
      this.checkCorrelationRisk(context),    // 相关性风险
      this.checkVolatilityRisk(context),     // 波动率风险
      this.checkConcentrationRisk(context),  // 集中度风险
    ]);
    
    return {
      approved: checks.every(c => c.passed),
      violations: checks.filter(c => !c.passed),
      suggestedAction: 'proceed' | 'reduce' | 'block'
    };
  }
}
```

#### 3.3 执行 Agent (Execution Agent)
```typescript
// src/agents/execution-agent.ts
class ExecutionAgent extends BaseAgent {
  async execute(order: Order): Promise<ExecutionResult> {
    // 智能订单路由
    const route = await this.determineBestRoute(order);
    
    // 订单拆分（大额订单）
    const slices = this.calculateOrderSlices(order);
    
    // 执行并监控
    for (const slice of slices) {
      const result = await this.submitOrder(slice);
      await this.monitorExecution(result);
    }
  }
}
```

---

### Phase 4: 交易记忆系统 (Week 7)

#### 4.1 Nowledge Mem 集成
```typescript
// src/memory/trade-memory.ts
class TradeMemory {
  // 保存交易记录
  async saveTrade(trade: TradeRecord): Promise<void> {
    await this.nmem.save({
      title: `Trade: ${trade.symbol} ${trade.side} @ ${trade.price}`,
      text: JSON.stringify(trade),
      unit_type: 'event',
      labels: ['trade', trade.symbol, trade.strategy],
      event_start: trade.timestamp,
      importance: this.calculateImportance(trade)
    });
  }
  
  // 搜索相关交易
  async searchTrades(query: string): Promise<TradeRecord[]>
  
  // 获取策略表现
  async getStrategyPerformance(strategyId: string, days: number): Promise<PerformanceMetrics>
  
  // 保存市场观察
  async saveObservation(observation: MarketObservation): Promise<void>
}
```

#### 4.2 自动捕获与回忆
- **Auto Capture**: 每笔交易、每个决策自动存入记忆
- **Auto Recall**: 策略执行前自动检索相关历史

---

### Phase 5: 回测系统 (Week 8)

#### 5.1 回测引擎
```typescript
// src/strategies/backtest.ts
class BacktestEngine {
  async run(config: BacktestConfig): Promise<BacktestResult> {
    const data = await this.loadHistoricalData(config);
    const portfolio = new Portfolio(config.initialCapital);
    
    for (const candle of data) {
      // 更新市场状态
      this.updateMarketState(candle);
      
      // 运行策略
      const signal = await this.strategy.onTick(this.marketState);
      
      // 模拟执行
      if (signal) {
        const trade = this.simulateExecution(signal, candle);
        portfolio.applyTrade(trade);
      }
      
      // 记录每日净值
      portfolio.recordEquity(candle.timestamp);
    }
    
    return this.generateReport(portfolio);
  }
}
```

#### 5.2 性能报告
- 收益率、最大回撤、夏普比率
- 交易次数、胜率、盈亏比
- 月度/年度收益分布

---

### Phase 6: CLI 与 Web UI (Week 9-10)

#### 6.1 CLI 工具
```bash
# 策略管理
quantclaw strategy add <config-file>
quantclaw strategy list
quantclaw strategy pause <id>
quantclaw strategy resume <id>
quantclaw strategy remove <id>

# 回测
quantclaw backtest --strategy <name> --start 2024-01-01 --end 2024-12-31

# 查看表现
quantclaw performance --strategy <name> --days 30

# 实时状态
quantclaw status

# 交易记录
quantclaw trades --symbol BTCUSDT --limit 50
```

#### 6.2 Web 仪表盘 (可选)
- 策略运行状态监控
- 实时盈亏展示
- 交易历史浏览
- 性能图表分析

---

## 🚀 迁移现有策略

### 迁移 btc-monitor
将现有的 BTC $71K 突破监控系统改造为 QuantClaw 策略：

```typescript
// strategies/btc-breakout.strategy.ts
export class BTCBreakoutStrategy extends BaseStrategy {
  name = 'btc_breakout';
  symbol = 'BTCUSDT';
  timeframe = '5m';
  
  private state = {
    isMonitoring: false,
    breakoutStartTime: null,
    alerted: false
  };
  
  async onTick(market: MarketState): Promise<Signal | null> {
    const price = market.price;
    const volume = market.volume;
    const fundingRate = market.fundingRate;
    const avgVolume = await this.indicators.sma(market.volumeHistory, 20);
    
    // 条件1: 突破 $71K
    if (price > 71000) {
      if (!this.state.isMonitoring) {
        this.state.isMonitoring = true;
        this.state.breakoutStartTime = Date.now();
      }
      
      // 条件2: 成交量 > 1.5倍均量
      // 条件3: 资金费率 > +0.01%
      // 条件4: 维持30分钟以上
      const duration = Date.now() - this.state.breakoutStartTime;
      
      if (volume > avgVolume * 1.5 && 
          fundingRate > 0.0001 && 
          duration > 30 * 60 * 1000 &&
          !this.state.alerted) {
        
        this.state.alerted = true;
        
        // 发送通知
        await this.notify({
          type: 'breakout_confirmed',
          symbol: this.symbol,
          price,
          volume,
          fundingRate
        });
        
        return {
          action: 'buy',
          confidence: 0.8,
          reason: 'BTC breakout confirmed'
        };
      }
    } else {
      // 价格回落，重置状态
      this.state = { isMonitoring: false, breakoutStartTime: null, alerted: false };
    }
    
    return null;
  }
}
```

### 迁移 MU 交易计划
```typescript
// strategies/mu-swing.strategy.ts
export class MUSwingStrategy extends BaseStrategy {
  name = 'mu_swing';
  symbol = 'MU';
  timeframe = '1h';
  
  // 关键价位
  private levels = {
    entry: [400, 390],
    stopLoss: 380,
    targets: [414, 455, 480, 500],
    ma20: 360
  };
  
  async onTick(market: MarketState): Promise<Signal | null> {
    const price = market.price;
    const position = await this.getPosition(this.symbol);
    
    // 入场逻辑
    if (!position) {
      for (const entryPrice of this.levels.entry) {
        if (price <= entryPrice) {
          return {
            action: 'buy',
            size: 0.3,  // 30% 仓位
            reason: `Price reached entry level $${entryPrice}`
          };
        }
      }
    }
    
    // 止损逻辑
    if (position && price < this.levels.stopLoss) {
      return {
        action: 'sell',
        size: 1.0,  // 全部卖出
        reason: 'Stop loss triggered'
      };
    }
    
    // 止盈逻辑
    for (const target of this.levels.targets) {
      if (position && price >= target) {
        return {
          action: 'sell',
          size: 0.3,  // 减仓 30%
          reason: `Target $${target} reached`
        };
      }
    }
    
    return null;
  }
}
```

---

## 📅 实施时间线

| 阶段 | 内容 | 预计时间 |
|-----|------|---------|
| Phase 1 | 核心框架搭建 | Week 1-2 |
| Phase 2 | 技能系统 | Week 3-4 |
| Phase 3 | Agent 系统 | Week 5-6 |
| Phase 4 | 交易记忆 | Week 7 |
| Phase 5 | 回测系统 | Week 8 |
| Phase 6 | CLI 与 UI | Week 9-10 |
| - | 测试与优化 | Week 11-12 |

---

## 🔧 技术栈

- **语言**: TypeScript (Node.js 20+)
- **调度**: node-cron / bullmq
- **数据库**: PostgreSQL (交易数据) + SQLite (本地配置)
- **记忆**: Nowledge Mem (nmem CLI)
- **测试**: Jest
- **CLI**: Commander.js
- **日志**: Winston
- **API**: CCXT (交易所统一接口)

---

## 💡 设计原则

1. **借鉴 OpenClaw 成功模式**
   - Cron Job 式策略调度
   - 自动 owner/sessionKey 注入
   - Skills 可插拔架构

2. **量化交易专用优化**
   - 低延迟事件处理
   - 完整的回测支持
   - 严格的风控体系

3. **个人用户友好**
   - 简单配置即可运行
   - 纸面交易优先
   - 渐进式实盘

4. **可扩展性**
   - 新策略只需实现 BaseStrategy
   - 新交易所只需实现 BaseExchange
   - 新指标只需添加 Skill

---

## 📝 下一步行动

1. **确认需求**: 是否需要调整范围或优先级？
2. **初始化项目**: 创建 `quantclaw/` 目录并开始 Phase 1
3. **选择首个迁移策略**: BTC 突破 或 MU 波段？
4. **确定交易所**: Binance (现货/合约) + Alpaca (美股)？

准备好开始了吗？🚀
