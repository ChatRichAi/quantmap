# QuantMap - 基于EvoMap的量化策略进化网络

## 核心理念

将 EvoMap 的 Agent Skill 进化 改造为 QuantMap 的 Strategy Gene 进化

## 架构映射

| EvoMap 组件 | QuantMap 组件 | 说明 |
|-------------|---------------|------|
| Agent | Strategy | 策略（而非Agent） |
| Skill | Gene | 策略基因（公式） |
| Capsule | Implementation | Python代码实现 |
| Task | Bounty | 赏金任务（发现/优化策略） |
| Log Analysis | Backtest | 回测验证（而非日志分析） |
| GEP Protocol | QEP Protocol | Quant Evolution Protocol |

## 目录结构

```
quantmap/
├── index.js                    # 主入口
├── src/
│   ├── evolve.js              # 策略进化引擎
│   ├── qep/                   # QEP协议 (Quant Evolution Protocol)
│   │   ├── protocol.js        # 协议定义
│   │   ├── geneStore.js       # 基因存储（替代assetStore）
│   │   ├── selector.js        # 策略选择器
│   │   ├── backtestValidator.js # 回测验证（核心差异）
│   │   └── bountyManager.js   # 赏金管理
│   └── backtest/              # 回测引擎
│       ├── engine.js          # 回测执行
│       └── metrics.js         # 绩效计算（夏普/回撤等）
├── assets/qep/                # QEP资产目录
│   ├── genes.json             # 策略基因库
│   ├── implementations/       # 代码实现
│   │   └── *.py              # Python策略代码
│   └── backtests.jsonl        # 回测记录
├── quantclaw-connector/       # QuantClaw连接层
│   ├── exporter.js           # 导出基因到QuantClaw
│   └── importer.js           # 导入QuantClaw结果
└── bounty-market/             # 赏金市场
    ├── publisher.js          # 发布赏金
    └── hunter.js             # 接取赏金
```

## QEP Protocol (Quant Evolution Protocol)

### 核心差异

1. **验证方式**
   - EvoMap: 任务完成度（功能正确）
   - QuantMap: 回测绩效（夏普>1.0, 回撤<20%）

2. **进化目标**
   - EvoMap: 修复Bug，提升效率
   - QuantMap: 提升夏普比率，降低回撤

3. **资产形式**
   - EvoMap: 代码补丁
   - QuantMap: 策略因子公式 + Python实现

### QEP数据结构

```json
{
  "gene": {
    "id": "g_momentum_001",
    "name": "RSI Momentum",
    "formula": "RSI(14) < 30 AND MACD > 0",
    "parameters": {"rsi_period": 14, "macd_fast": 12},
    "generation": 5,
    "parent_ids": ["g_rsi_001", "g_macd_001"],
    "backtest_score": {
      "sharpe": 1.5,
      "max_drawdown": -0.15,
      "win_rate": 0.58,
      "annual_return": 0.25
    }
  },
  "implementation": {
    "language": "python",
    "code": "def calculate_signal(data): ...",
    "dependencies": ["pandas", "numpy", "talib"]
  },
  "validation": {
    "markets": ["AAPL", "MSFT", "SPY"],
    "period": "2020-01-01 to 2024-12-31",
    "verified_by": ["backtest_engine_v1", "cross_validation_v2"]
  }
}
```

## 赏金市场机制

### 赏金类型

1. **发现赏金** - 发现新因子
   ```json
   {
     "type": "discovery",
     "title": "发现高夏普动量因子",
     "requirements": {
       "min_sharpe": 1.2,
       "max_drawdown": -0.20,
       "markets": ["US equities"]
     },
     "reward": 1000
   }
   ```

2. **优化赏金** - 优化现有策略
   ```json
   {
     "type": "optimization",
     "target_gene": "g_momentum_001",
     "title": "优化RSI Momentum参数",
     "requirements": {
       "improve_sharpe_by": 0.2
     },
     "reward": 500
   }
   ```

3. **验证赏金** - 独立验证策略
   ```json
   {
     "type": "verification",
     "target_gene": "g_trend_003",
     "title": "验证趋势策略稳健性",
     "requirements": {
       "walkforward_windows": 5,
       "min_consistency": 0.8
     },
     "reward": 200
   }
   ```

## 实施步骤

### Step 1: Fork EvoMap 基础架构
```bash
cp -r ~/.openclaw/workspace/evolver ~/.openclaw/workspace/quantmap
cd quantmap
```

### Step 2: 改造核心模块
1. **替换日志分析为回测引擎**
2. **修改GEP为QEP协议**
3. **添加赏金市场**

### Step 3: 连接QuantClaw
- 导出QuantClaw基因到QuantMap
- 导入QuantMap验证结果回QuantClaw

### Step 4: 启动网络
```bash
node index.js --loop  # 启动QuantMap进化循环
```

## 与QuantClaw的关系

```
QuantClaw (本地进化)  <--双向同步-->  QuantMap (分布式进化网络)
     ↓                                          ↓
  基因池(54个)                           赏金市场(多Agent参与)
  自驱进化                               外部验证
  单一系统                               网络效应
```

QuantMap = QuantClaw 的 "外部大脑" 和 "验证网络"
