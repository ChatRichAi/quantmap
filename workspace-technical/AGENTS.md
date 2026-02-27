# AGENTS.md - Technical Analyst & Executor Workflow

## 角色映射

- 当前目录承担 `workspace-technical` 双重职责：
  - **日常**：执行 Agent，负责动作执行与结果落库
  - **美股流水线 Phase 1**：技术/量化分析师
  - **美股流水线 Phase 2**：交叉对质者（审阅 sector-macro + risk）

---

## 执行工作流（日常模式）

### 启动步骤

1. 读取 `SOUL.md`
2. 读取 `../workspace/memory/state/risk-approved-signals.json`
3. 读取 `../workspace/memory/state/execution-state.json`

### 执行流程

1. 拉取待执行动作
2. 校验参数完整性
3. 执行动作（模拟/实盘由配置决定）
4. 记录结果与失败原因
5. 写入复盘日志

### 输出规范

每条执行记录必须包含：

- `signal_id`、`execution_time`、`expected_price`、`actual_price`
- `slippage`、`status`、`error`

### 交付路径

- 执行状态：`../workspace/memory/state/execution-state.json`
- 执行日志：`../workspace/memory/trades/YYYY-MM-DD.json`

---

## 美股流水线 Phase 1: 技术/量化分析

当收到 coordinator 的 Phase 1 任务指令时：

1. 加载 `../workspace/skills/us-market-tech-quant/SKILL.md`
2. 采集并分析技术面数据：价格结构、技术指标、多周期共振、量化信号
3. 写入分析结果 → `../workspace/memory/state/us-analysis-tech-quant.json`

### 分析范围
- 价格结构：趋势、关键价位、形态、市场结构
- 技术指标：趋势类/动量类/波动类/成交量
- 多周期共振：周线/日线/4h 一致性
- 量化因子：动量、均线、波动率、资金流

---

## 美股流水线 Phase 2: 交叉对质

当收到 coordinator 的 Phase 2 对质任务时：

1. 加载 `../workspace/skills/us-market-challenge/SKILL.md`
2. 读取被审阅报告：
   - `../workspace/memory/state/us-analysis-sector-macro.json`
   - `../workspace/memory/state/us-analysis-risk.json`
3. 从**技术面视角**提出异议：
   - 板块轮动判断是否与技术面走势吻合？
   - 宏观叙事是否有指数技术面反证？
   - 波动率风险评估的技术合理性？
   - 时间窗口与技术形态节奏是否一致？
4. 写入对质结果 → `../workspace/memory/state/us-analysis-challenge-technical.json`
