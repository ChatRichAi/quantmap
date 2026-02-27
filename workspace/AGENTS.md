# AGENTS.md - QuantClaw Workspace Playbook

## 会话启动顺序

每次会话开始立即执行：

1. 读取 `SOUL.md`
2. 读取 `USER.md`
3. 读取 `HEARTBEAT.md`
4. 读取 `memory/daily/` 最近 2 天日志
5. 在主会话额外读取 `MEMORY.md`

## 日内工作流

### 盘前

- 检查当日市场日历与时区（A股/美股/加密）
- 更新关注标的与关键价位
- 加载前一交易日未完成信号
- 生成盘前观察清单

### 交易时段

- 按 `HEARTBEAT.md` 的市场时段执行监控
- 新信号必须包含：方向、触发条件、失效条件、风险等级、建议仓位
- 出现冲突信号时，优先执行风控更严格的一侧

### 盘后

- 写入 `memory/daily/YYYY-MM-DD.md` 盘后日志
- 更新 `memory/strategies/` 的策略表现
- 更新 `memory/state/` 的监控状态
- 生成复盘要点（做对/做错/改进动作）

### 周度与月度

- 周度：再平衡检查、策略稳定性检查
- 月度：策略表现排名、参数淘汰与替换建议

## 多市场规则

- A股时段：09:15-15:00 (Asia/Shanghai)
- 美股时段：21:30-04:00 / 22:30-05:00 (夏令/冬令)
- 加密货币：7x24 小时
- 贵金属：重点关注 09:00 与 21:00 追踪窗口

## 技能自动加载规则

### 美股分析 → 多Agent流水线（3阶段）

当用户请求美股市场扫描、板块分析或生成投资报告时，触发多Agent流水线：

#### Phase 1: 并行分析（3 analyst 同时 spawn）
- **technical** → 加载 `skills/us-market-tech-quant/SKILL.md` → 写入 `memory/state/us-analysis-tech-quant.json`
- **planner** → 加载 `skills/us-market-sector-macro/SKILL.md` → 写入 `memory/state/us-analysis-sector-macro.json`
- **policy** → 加载 `skills/us-market-risk/SKILL.md` → 写入 `memory/state/us-analysis-risk.json`

#### Phase 2: 交叉对质（3 analyst 再次 spawn，审阅其他人结论）
- **technical** 审阅 sector-macro + risk → `memory/state/us-analysis-challenge-technical.json`
- **planner** 审阅 tech-quant + risk → `memory/state/us-analysis-challenge-planner.json`
- **policy** 审阅 tech-quant + sector-macro → `memory/state/us-analysis-challenge-policy.json`
- 所有对质使用 `skills/us-market-challenge/SKILL.md`

#### Phase 3: 首席策略师聚合（coordinator）
- coordinator 加载 `skills/us-market-chief-strategist/SKILL.md`
- 读取 3 份分析报告 + 3 份对质意见
- 裁决冲突点（保守偏向）
- 生成最终 10-section 报告 → `memory/state/us-analysis-final.json`

#### 编排要求
- Phase 1 三个 analyst 必须并行 spawn，互不依赖
- Phase 2 必须等 Phase 1 全部完成后再 spawn
- Phase 3 必须等 Phase 2 全部完成后执行
- 最终报告遵循评分体系（技术面40 + 基本面30 + 情绪面30）和分级策略框架（激进/稳健/保守）

### A股超短 → `chaoduan-strategy` + `stock-sniper`
- A股盯盘、竞价分析、超短线交易时加载 `skills/chaoduan-strategy/SKILL.md`
- A股个股狙击、异动扫描时加载 `skills/stock-sniper/SKILL.md`

## 风控底线

- 单一建议必须有止损或失效条件
- 未给出仓位建议的信号视为不完整
- 高风险标的默认降级仓位
- 当现金仓位低于目标下限时，禁止新增高风险建议

## 记忆与文件规范

- 交易日志：`memory/daily/`
- 策略表现：`memory/strategies/`
- 再平衡记录：`memory/rebalance/`
- 市场状态：`memory/state/`
- 研究笔记：`memory/research/`
- 模板文件：`memory/templates/`

只要需要跨会话记住的信息，必须写文件，不依赖临时上下文。

## 外部动作边界

- 读取、分析、重构、记录可直接执行。
- 真实下单、外部发消息、资金操作默认需要确认（除非已明确自动化授权）。
- 任何不确定动作，先问清楚。

## 输出格式标准

默认输出 5 段：

1. 市场状态摘要
2. 关键信号与触发价位
3. 风险与失效条件
4. 仓位建议与优先级
5. 下一检查时间点
