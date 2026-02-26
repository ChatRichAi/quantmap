# QuantMap — 量化策略进化网络

> **Quantitative Strategy Evolution Network powered by QEP Protocol**
>
> 将生物进化原理引入量化交易，让策略从数据中自主生长

---

## 一键部署

```bash
# 克隆并安装（自动完成全部依赖 + 生成启动脚本）
git clone https://github.com/ChatRichAi/quantmap.git && cd quantmap && bash install.sh
```

安装完成后：

```bash
bash quantmap.sh start    # 启动全部服务（API + Agents + UI）
bash quantmap.sh stop     # 停止
bash quantmap.sh status   # 查看状态
bash quantmap.sh logs     # 查看日志 (api|evolver|miner|ui)
```

| 服务 | 地址 |
|------|------|
| API 文档 | http://localhost:8889/docs |
| EvoMap UI | http://localhost:3000 |

**前置要求**: Python 3.8+ · Node.js 18+ · Git

> 自定义端口：`bash install.sh --port-api 8890 --port-ui 3001`
> 仅后端不装前端：`bash install.sh --no-ui`

---

## 项目概览

QuantMap 是一个基于 **QEP 协议（Quant Evolution Protocol）** 的分布式量化策略进化网络。它将基因表达式编程（GEP）与多 Agent 协作机制结合，实现策略的自动发现、回测验证、赏金激励和持续进化。

```
QuantMap
├── 本地进化引擎 (QuantClaw)     ──→  策略基因自驱进化
├── 分布式进化网络 (QuantMap)    ──→  多 Agent 赏金协作
├── 进化可视化平台 (EvoMap UI)   ──→  基因池实时监控
└── 技能生态 (Skills)           ──→  可复用量化工具链
```

---

## 核心协议：QEP (Quant Evolution Protocol)

QEP 是 QuantMap 的底层数据协议，定义策略基因的表示、验证和进化标准。

### 基因数据结构

```json
{
  "gene": {
    "id": "g_momentum_001",
    "name": "RSI Momentum",
    "formula": "RSI(14) < 30 AND MACD > 0",
    "parameters": { "rsi_period": 14, "macd_fast": 12 },
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
    "code": "def calculate_signal(data): ..."
  },
  "validation": {
    "markets": ["A股", "US", "Crypto"],
    "period": "2020-01-01 to 2024-12-31",
    "passed": true
  }
}
```

### 验证标准

| 指标 | 通过阈值 |
|------|----------|
| 夏普比率 | ≥ 1.0 |
| 最大回撤 | ≤ 20% |
| 胜率 | ≥ 45% |
| 市场覆盖 | A股 / 美股 / Crypto |

### 进化算子

- **变异（Mutation）** — 随机修改基因参数
- **交叉（Crossover）** — 融合两个高绩效基因
- **转位（Transposition）** — 重组基因片段
- **自然选择（Selection）** — 保留高夏普基因淘汰低绩效基因

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│   │  赏金市场     │  │  进化监控     │  │  Agent 协作网络  │ │
│   │  Bounty Mkt  │  │  EvoMap UI   │  │  P2P Network     │ │
│   └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘ │
└──────────┼────────────────┼───────────────────┼────────────┘
           │                │                   │
┌──────────┴────────────────┴───────────────────┴────────────┐
│                    QEP Protocol Layer                       │
│   Core (AST) → Operators (GEP) → Evolution → Validation    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                    Backtest Engine Layer                     │
│   A股 (akshare)  ·  美股 (yfinance)  ·  Crypto (OKX)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 项目结构

```
.openclaw/
├── workspace/
│   ├── quantmap/                  # QuantMap 核心协议
│   │   ├── index.js               # 主入口，进化循环
│   │   ├── src/
│   │   │   ├── qep/protocol.js    # QEP 协议实现
│   │   │   └── backtest/          # 回测引擎
│   │   ├── assets/qep/            # 基因库 & 回测记录
│   │   ├── quantclaw-connector/   # 连接本地 QuantClaw
│   │   ├── bounty-market/         # 赏金市场
│   │   ├── docs/
│   │   │   ├── whitepaper.html    # 白皮书
│   │   │   └── roadmap.html       # 路线图
│   │   └── visualization/         # 基因可视化
│   │
│   ├── quantclaw/                 # 本地量化进化引擎
│   │   ├── quant_gep/             # Quant-GEP 协议实现 (Python)
│   │   │   ├── core/              # AST 基因表达式
│   │   │   ├── operators/         # GEP 进化算子
│   │   │   ├── evolution/         # 进化算法
│   │   │   ├── backtest/          # 多市场回测适配器
│   │   │   └── protocol/          # 协议 Schema & 验证
│   │   ├── factor_evolution_engine.py   # 因子进化引擎
│   │   ├── darwinian_ecosystem_v4.py    # 达尔文生态系统
│   │   ├── api_server.py                # REST API 服务
│   │   └── ecosystem_visualization.html # 生态可视化
│   │
│   ├── quant-evomap-ui/           # 前端可视化平台 (Next.js)
│   │   ├── app/[locale]/          # 多语言页面 (中/英)
│   │   │   ├── dashboard/         # 总览仪表盘
│   │   │   ├── genes/             # 基因库浏览器
│   │   │   ├── evomap/            # 进化地图
│   │   │   ├── marketplace/       # 策略市场
│   │   │   ├── agents/            # Agent 排行榜
│   │   │   └── bounties/          # 赏金任务
│   │   └── components/            # UI 组件库
│   │
│   ├── skills/                    # 量化技能工具链
│   │   ├── stock-sniper/          # 选股狙击手
│   │   ├── backtest-engine/       # 通用回测引擎
│   │   ├── market-data/           # 多源行情数据
│   │   ├── technical-analysis/    # 技术分析指标
│   │   ├── risk-manager/          # 风险管理
│   │   ├── portfolio-tracker/     # 持仓追踪
│   │   ├── chaoduan-strategy/     # 超短线策略
│   │   ├── crypto-ta-okx/         # OKX 加密量化
│   │   └── auto-evolve/           # 自动进化脚本
│   │
│   ├── scripts/                   # 监控 & 分析脚本
│   │   ├── us_stock_monitor.py    # 美股实时监控
│   │   ├── us_stock_resonance_monitor.py  # 共振选股
│   │   └── multi-node-bounty-sniper.js    # 多节点赏金狙击
│   │
│   └── evolver/                   # 进化守护进程
│
├── extensions/
│   └── openclaw-nowledge-mem/     # 知识记忆扩展插件
│
└── quant-evomap-ui/               # UI 部署目录
```

---

## 快速开始

### 运行 QuantMap 进化循环

```bash
cd workspace/quantmap
node index.js --loop
```

### 启动 QuantClaw 本地引擎

```bash
cd workspace/quantclaw
python api_server.py          # 启动 API 服务
python factor_evolution_engine.py  # 启动因子进化
```

### 启动 EvoMap 前端

```bash
cd quant-evomap-ui/quant-evomap-ui
npm install
npm run dev
# 访问 http://localhost:3000
```

### 运行股票狙击手

```bash
cd workspace/skills/stock-sniper
bash run.sh
```

---

## 赏金市场机制

QuantMap 的核心激励机制，Agent 通过完成策略发现/优化/验证任务获得赏金。

| 赏金类型 | 描述 | 验收标准 |
|----------|------|----------|
| **发现赏金** | 发现新的因子/策略 | 夏普 ≥ 1.2，回撤 ≤ 20% |
| **优化赏金** | 提升现有策略绩效 | 夏普提升 ≥ 0.2 |
| **验证赏金** | 独立验证策略稳健性 | Walk-forward 一致性 ≥ 80% |

---

## QuantClaw vs QuantMap

| | QuantClaw | QuantMap |
|--|-----------|----------|
| 范围 | 本地单机进化 | 分布式网络 |
| 验证 | 内部自验证 | 多 Agent 外部验证 |
| 激励 | 无 | 赏金市场 |
| 基因池 | 本地（~54个基因） | 网络共享 |
| 定位 | 大脑 | 神经网络 |

> QuantMap = QuantClaw 的外部大脑 + 分布式验证网络

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端引擎 | Python 3.8+, FastAPI |
| 进化协议 | Node.js (QEP Protocol) |
| 前端 | Next.js 14, TypeScript, Tailwind CSS |
| 数据源 | akshare (A股), yfinance (美股), OKX API (加密) |
| 回测 | pandas, numpy, TA-Lib |
| 数据库 | SQLite (本地基因库) |

---

## Roadmap

- [x] QEP Protocol v1.0 基础规范
- [x] QuantClaw 本地进化引擎
- [x] 基因 AST 表达式 + GEP 算子
- [x] 多市场回测适配器（A股/美股/Crypto）
- [x] EvoMap 可视化前端
- [x] 赏金市场基础框架
- [ ] P2P 多节点网络
- [ ] 链上赏金结算
- [ ] QEP Protocol v2.0（联邦学习支持）

---

## License

MIT License — 策略进化，人人可参与
