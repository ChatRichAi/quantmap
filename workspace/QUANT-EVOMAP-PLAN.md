# Quant EvoMap - 策略挖掘市场

> 一个开放的量化策略基因市场
> 让 AI Agent 协作发现、验证、进化交易策略

---

## 🎯 愿景

### 问题：为什么需要 Quant EvoMap？

1. **策略同质化**：所有人用同样的技术指标 → 阿尔法衰减
2. **发现能力有限**：个人/小团队无法覆盖全市场
3. **验证成本高**：发现策略容易，验证有效难
4. **知识孤岛**：发现的策略无法共享/复用

### 解决方案：众包策略挖掘

```
传统方式:
你 ──> 研究100只股票 ──> 发现5个策略 ──> 验证有效2个
                  (耗时3个月)

Quant EvoMap:
你 ──> 发布100个赏金任务 ──> 100个Agent并行挖掘
     <── 收到200个候选策略 <──
     <── 验证50个有效      <──
     <── 精选10个最优      <── (耗时1周)
```

---

## 🏗️ 核心组件

### 1. 策略基因 (Strategy Gene)

#### 基因编码规范 (GET Protocol v1)

```typescript
interface StrategyGene {
  // 元数据
  id: string;                    // 基因唯一标识
  version: number;               // 版本号
  createdAt: Date;
  author: string;                // 发现者 Agent ID
  
  // 基因型: 可进化的编码
  genotype: {
    // 特征表达式 (树形结构)
    signal: GeneExpression;
    
    // 参数 (可进化)
    params: {
      entryThreshold: EvolvableNumber;  // 0.1 ~ 0.9
      exitThreshold: EvolvableNumber;
      positionSize: EvolvableNumber;    // 0.01 ~ 0.5
      stopLoss: EvolvableNumber;        // 0.02 ~ 0.1
    };
    
    // 适用条件
    conditions: {
      minVolatility: number;
      maxVolatility: number;
      marketRegime: ('trending' | 'ranging' | 'any')[];
    };
  };
  
  // 表现型: 可执行代码
  phenotype: {
    // 信号生成函数
    generateSignal: (ctx: MarketContext) => Signal;
    
    // 仓位管理函数
    calculatePosition: (signal: Signal, portfolio: Portfolio) => Position;
  };
  
  // 验证记录
  validation: {
    status: 'pending' | 'validating' | 'verified' | 'rejected';
    backtestResults: BacktestResult[];
    paperTradeResults?: PaperTradeResult[];
    liveTradeResults?: LiveTradeResult[];
    verifiedBy: string[];  // 验证者 Agent IDs
  };
  
  // 血统追踪
  lineage: {
    parentA?: string;
    parentB?: string;
    mutations: MutationRecord[];
    generation: number;
  };
  
  // 市场表现
  performance: {
    sharpeRatio: number;
    winRate: number;
    profitFactor: number;
    maxDrawdown: number;
    trades: number;
    avgReturn: number;
    consistency: number;  // 跨时间段稳定性
  };
}

// 基因表达式 (树形结构)
interface GeneExpression {
  type: 'operator' | 'terminal' | 'constant';
  
  // 操作符节点
  operator?: {
    name: 'add' | 'subtract' | 'multiply' | 'divide' | 
           'gt' | 'lt' | 'eq' | 'and' | 'or' | 'if' |
           'log' | 'exp' | 'sqrt' | 'abs' | 'sign';
    operands: GeneExpression[];
  };
  
  // 终端节点 (市场数据)
  terminal?: {
    name: string;  // 'close', 'volume', 'high', 'low', 'open'
    transform?: 'sma' | 'ema' | 'std' | 'max' | 'min' | 'change';
    period?: number;
  };
  
  // 常数节点
  constant?: number;
}
```

#### 示例基因

```typescript
// 基因: "放量突破均线"
const exampleGene: StrategyGene = {
  id: "gene_a7f3d2",
  genotype: {
    signal: {
      type: 'operator',
      operator: {
        name: 'and',
        operands: [
          // 条件1: 价格 > 20日均线
          {
            type: 'operator',
            operator: {
              name: 'gt',
              operands: [
                { type: 'terminal', terminal: { name: 'close' } },
                { 
                  type: 'terminal', 
                  terminal: { name: 'close', transform: 'sma', period: 20 }
                }
              ]
            }
          },
          // 条件2: 成交量 > 2倍均量
          {
            type: 'operator',
            operator: {
              name: 'gt',
              operands: [
                { type: 'terminal', terminal: { name: 'volume' } },
                {
                  type: 'operator',
                  operator: {
                    name: 'multiply',
                    operands: [
                      { type: 'terminal', terminal: { name: 'volume', transform: 'sma', period: 20 } },
                      { type: 'constant', constant: 2.0 }
                    ]
                  }
                }
              ]
            }
          }
        ]
      }
    },
    params: {
      entryThreshold: { value: 0.7, min: 0.1, max: 0.9 },
      exitThreshold: { value: 0.3, min: 0.1, max: 0.9 },
      positionSize: { value: 0.1, min: 0.01, max: 0.5 },
      stopLoss: { value: 0.05, min: 0.02, max: 0.1 }
    },
    conditions: {
      minVolatility: 0.15,
      maxVolatility: 0.5,
      marketRegime: ['trending']
    }
  },
  
  performance: {
    sharpeRatio: 1.8,
    winRate: 0.62,
    profitFactor: 2.1,
    maxDrawdown: 0.12,
    trades: 147,
    avgReturn: 0.023,
    consistency: 0.85
  },
  
  lineage: {
    generation: 5,
    mutations: [
      { type: 'param_tuning', from: { volumeMult: 1.5 }, to: { volumeMult: 2.0 } },
      { type: 'operator_change', from: 'ema', to: 'sma' }
    ]
  }
};
```

---

### 2. 赏金任务 (Bounty)

#### 任务类型

```typescript
interface Bounty {
  id: string;
  type: BountyType;
  status: 'open' | 'claimed' | 'validating' | 'completed' | 'expired';
  
  // 任务参数
  params: {
    symbol: string;           // 目标股票
    timeframe: string;        // 时间周期
    dataRange: { start: Date; end: Date };
    
    // 奖励参数
    reward: {
      base: number;           // 基础奖励
      bonus: number;          // 超额奖励
      token: string;          // 奖励代币
    };
    
    // 通过标准
    criteria: {
      minSharpe: number;
      minWinRate: number;
      maxDrawdown: number;
      minTrades: number;
    };
  };
  
  // 任务元信息
  meta: {
    createdBy: string;        // 发布者
    createdAt: Date;
    deadline?: Date;
    priority: 'low' | 'medium' | 'high' | 'critical';
    tags: string[];
  };
  
  // 提交记录
  submissions: Submission[];
}

enum BountyType {
  // 发现型: 为某股票找到有效策略
  STRATEGY_DISCOVERY = 'strategy_discovery',
  
  // 改进型: 优化现有策略
  STRATEGY_OPTIMIZATION = 'strategy_optimization',
  
  // 验证型: 验证某策略是否有效
  STRATEGY_VALIDATION = 'strategy_validation',
  
  // 迁移型: 将策略适配到新市场/股票
  STRATEGY_MIGRATION = 'strategy_migration',
  
  // 组合型: 发现多策略组合
  PORTFOLIO_CONSTRUCTION = 'portfolio_construction'
}
```

#### 示例赏金任务

```typescript
// 赏金: 发现 TSLA 的有效日内策略
const tslaBounty: Bounty = {
  id: "bounty_tsla_001",
  type: BountyType.STRATEGY_DISCOVERY,
  status: 'open',
  
  params: {
    symbol: 'TSLA',
    timeframe: '5m',
    dataRange: {
      start: new Date('2023-01-01'),
      end: new Date('2024-01-01')
    },
    reward: {
      base: 100,
      bonus: 200,
      token: 'QUANT'
    },
    criteria: {
      minSharpe: 1.5,
      minWinRate: 0.55,
      maxDrawdown: 0.15,
      minTrades: 50
    }
  },
  
  meta: {
    createdBy: 'user_quantclaw',
    createdAt: new Date(),
    deadline: new Date('2024-03-01'),
    priority: 'high',
    tags: ['TSLA', 'intraday', 'high-volatility', 'breakout']
  },
  
  submissions: []
};
```

---

### 3. 验证胶囊 (Capsule)

```typescript
interface Capsule {
  id: string;
  bountyId: string;
  geneId: string;
  
  // 验证结果
  validation: {
    status: 'passed' | 'failed' | 'partial';
    score: number;  // 0-100
    
    // 回测详情
    backtest: {
      period: { start: Date; end: Date };
      trades: TradeRecord[];
      equity: number[];
      metrics: PerformanceMetrics;
    };
    
    // 稳健性测试
    robustness: {
      walkForward: boolean;
      monteCarlo: boolean;
      outOfSample: boolean;
      parameterSensitivity: number;
    };
    
    // 验证者签名
    validators: {
      agentId: string;
      signature: string;
      timestamp: Date;
    }[];
  };
  
  // 胶囊元信息
  meta: {
    createdAt: Date;
    expiresAt: Date;  // 策略有效期
    reputation: number;  // 提交者信誉分
  };
}
```

---

## 🤖 Agent 类型

### 1. 挖掘 Agent (Miner Agent)

```typescript
class MinerAgent {
  async mine(bounty: Bounty): Promise<StrategyGene> {
    // 1. 加载历史数据
    const data = await this.loadData(bounty.params);
    
    // 2. 遗传编程进化
    const population = this.initializePopulation(100);
    
    for (let gen = 0; gen < 50; gen++) {
      // 评估适应度
      const fitness = population.map(gene => 
        this.backtest(gene, data)
      );
      
      // 选择、交叉、变异
      population = this.evolve(population, fitness);
    }
    
    // 3. 返回最优基因
    return this.selectBest(population);
  }
}
```

### 2. 验证 Agent (Validator Agent)

```typescript
class ValidatorAgent {
  async validate(gene: StrategyGene, bounty: Bounty): Promise<Capsule> {
    // 1. 代码审查
    const codeReview = this.reviewCode(gene);
    
    // 2. 独立回测
    const backtest = await this.runBacktest(gene, bounty.params);
    
    // 3. 稳健性测试
    const robustness = await this.testRobustness(gene);
    
    // 4. 生成验证报告
    return {
      validation: {
        status: this.determineStatus(backtest, robustness),
        score: this.calculateScore(backtest, robustness),
        backtest,
        robustness,
        validators: [{ agentId: this.id, signature: this.sign(), timestamp: new Date() }]
      }
    };
  }
}
```

### 3. 优化 Agent (Optimizer Agent)

```typescript
class OptimizerAgent {
  async optimize(gene: StrategyGene): Promise<StrategyGene> {
    // 1. 参数优化 (贝叶斯优化)
    const optimizedParams = await this.bayesianOptimize(gene);
    
    // 2. 结构优化 (遗传编程微调)
    const optimizedStructure = await this.gpRefine(gene);
    
    // 3. 组合优化
    return this.combine(optimizedParams, optimizedStructure);
  }
}
```

---

## 📊 激励机制

### 奖励分配

```
总奖励池: 100 QUANT

赏金完成奖励: 60 QUANT
├── 挖掘者: 40 QUANT (发现有效策略)
├── 验证者: 15 QUANT (3个验证者 × 5)
└── 优化者: 5 QUANT  (如有改进)

平台维护: 20 QUANT
质押奖励: 20 QUANT (用于奖励优质基因持有者)
```

### 声誉系统

```typescript
interface Reputation {
  agentId: string;
  
  // 挖掘声誉
  mining: {
    submissions: number;
    accepted: number;
    acceptanceRate: number;
    avgGeneQuality: number;
  };
  
  // 验证声誉
  validation: {
    validations: number;
    accuracy: number;  // 验证准确率
    consensus: number; // 与其他验证者一致性
  };
  
  // 总体声誉分
  score: number;  // 0-100
  tier: 'bronze' | 'silver' | 'gold' | 'platinum' | 'diamond';
}
```

---

## 🔧 技术实现

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Quant EvoMap Network                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Miner   │  │ Validator│  │ Optimizer│  │  User    │   │
│  │  Agents  │  │  Agents  │  │  Agents  │  │  Client  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │          │
│       └─────────────┴─────────────┴─────────────┘          │
│                         │                                   │
│  ┌──────────────────────┼──────────────────────┐          │
│  │                      ▼                      │          │
│  │           ┌──────────────────┐              │          │
│  │           │   P2P Network    │              │          │
│  │           │  (libp2p/IPFS)   │              │          │
│  │           └────────┬─────────┘              │          │
│  │                    │                        │          │
│  │  ┌─────────────────┼─────────────────┐     │          │
│  │  │                 ▼                 │     │          │
│  │  │  ┌──────────┐ ┌──────────┐       │     │          │
│  │  │  │Gene Store│ │Bounty    │       │     │          │
│  │  │  │(IPFS)    │ │Registry  │       │     │          │
│  │  │  └──────────┘ └──────────┘       │     │          │
│  │  │                                   │     │          │
│  │  │  ┌──────────┐ ┌──────────┐       │     │          │
│  │  │  │Consensus │ │Reputation│       │     │          │
│  │  │  │(PoS/PoW) │ │Contract  │       │     │          │
│  │  │  └──────────┘ └──────────┘       │     │          │
│  │  └───────────────────────────────────┘     │          │
│  └────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 技术 | 说明 |
|-----|------|------|
| P2P网络 | libp2p | Agent间通信 |
| 数据存储 | IPFS + 本地 | 基因、回测结果存储 |
| 共识机制 | PoS | 验证结果共识 |
| 智能合约 | Solidity | 赏金、奖励分配 |
| 回测引擎 | Python/NumPy | 快速策略验证 |
| 基因进化 | DEAP/gplearn | 遗传编程 |

---

## 🚀 与 OpenClaw 整合

### 赏金猎人系统升级

现有的赏金猎人可以直接接入 Quant EvoMap：

```typescript
// 在现有 bounty-sniper.js 基础上扩展
class QuantEvoMapSniper {
  async scan() {
    // 1. 扫描 EvoMap 通用任务 (现有)
    const evomapBounties = await this.scanEvoMap();
    
    // 2. 扫描 Quant EvoMap 策略任务 (新增)
    const quantBounties = await this.scanQuantEvoMap();
    
    // 3. 根据 Agent 专长选择任务
    if (this.specialty === 'strategy_mining') {
      return quantBounties.filter(b => b.type === 'strategy_discovery');
    }
    
    return [...evomapBounties, ...quantBounties];
  }
}
```

### Nowledge Mem 集成

```typescript
// 自动记录发现的策略基因
async function onGeneDiscovered(gene: StrategyGene) {
  await nmem.save({
    title: `Strategy Gene: ${gene.id}`,
    text: JSON.stringify(gene),
    unit_type: 'learning',
    labels: ['strategy-gene', 'quant-evomap', gene.params.symbol],
    importance: gene.performance.sharpeRatio > 2 ? 0.9 : 0.7
  });
}
```

---

## 📈 发展路线图

### Phase 1: 单机版 (Week 1-2)
- 基因编码规范
- 遗传编程引擎
- 本地回测验证

### Phase 2: 局域网 (Week 3-4)
- 多个本地 Agent 协作
- 简单的赏金/验证机制
- 共享基因库

### Phase 3: 测试网 (Week 5-8)
- P2P网络搭建
- 赏金市场上线
- 邀请测试 Agent

### Phase 4: 主网 (Week 9+)
- 开放参与
- 代币激励
- 生态建设

---

**这是你要的 Quant EvoMap 吗？一个专注于策略挖掘的开放市场？**
