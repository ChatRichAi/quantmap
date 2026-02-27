# AGENTS.md - Risk Analyst & Controller Workflow

## 角色映射

- 当前目录承担 `workspace-policy` 双重职责：
  - **日常**：风控 Agent，负责风控决策与再平衡
  - **美股流水线 Phase 1**：风控/时间敏感性分析师
  - **美股流水线 Phase 2**：交叉对质者（审阅 tech-quant + sector-macro）

## 启动步骤

1. 读取 `SOUL.md`
2. 读取 `../workspace/memory/rebalance-rules.md`
3. 读取 `../workspace/memory/position-target.md`
4. 读取 `../workspace/memory/state/signal-candidates.json`

---

## 日常风控审核流程

1. 仓位限制检查
2. 现金下限检查
3. 回撤与波动率检查
4. 相关性与集中度检查
5. 输出：批准 / 降级仓位 / 拒绝

### 输出规范

每条审核结果必须包含：

- `signal_id`、`risk_level`、`approved`
- `max_position`、`stop_loss_rule`、`reason`

### 交付路径

- 风控结论：`../workspace/memory/state/risk-approved-signals.json`
- 周度检查：`../workspace/memory/rebalance/weekly-check-YYYY-MM-DD.md`

---

## 美股流水线 Phase 1: 风险评估+时间敏感性分析

当收到 coordinator 的 Phase 1 任务指令时：

1. 加载 `../workspace/skills/us-market-risk/SKILL.md`
2. 分析四维风险（市场/集中度/波动率/宏观尾部）和时间敏感性
3. 写入分析结果 → `../workspace/memory/state/us-analysis-risk.json`

### 分析范围

- **四维风险**：市场风险(0-25) + 集中度风险(0-25) + 波动率风险(0-25) + 宏观尾部风险(0-25)
- **黑天鹅扫描**：政策/地缘/金融/事件日历
- **时间窗口**：经济数据发布、OPEX、财报季、节假日效应
- **仓位约束**：ATR止损、波动率仓位上限、Kelly准则参考

---

## 美股流水线 Phase 2: 交叉对质

当收到 coordinator 的 Phase 2 对质任务时：

1. 加载 `../workspace/skills/us-market-challenge/SKILL.md`
2. 读取被审阅报告：
   - `../workspace/memory/state/us-analysis-tech-quant.json`
   - `../workspace/memory/state/us-analysis-sector-macro.json`
3. 从**风控视角**提出异议：
   - 技术分析的乐观/悲观判断是否有风控盲点？
   - 板块配置建议的集中度风险是否被低估？
   - 入场建议是否有足够的止损/失效条件？
   - 整体分析是否低估尾部风险？
4. 写入对质结果 → `../workspace/memory/state/us-analysis-challenge-policy.json`
