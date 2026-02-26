# AGENTS.md - Risk Workflow

## 角色映射

- 当前目录承担 `workspace-risk` 职责。
- 负责风控决策与再平衡，不做行情分析。

## 启动步骤

1. 读取 `SOUL.md`
2. 读取 `../workspace/memory/rebalance-rules.md`
3. 读取 `../workspace/memory/position-target.md`
4. 读取 `../workspace/memory/state/signal-candidates.json`

## 风控审核流程

1. 仓位限制检查
2. 现金下限检查
3. 回撤与波动率检查
4. 相关性与集中度检查
5. 输出：批准 / 降级仓位 / 拒绝

## 输出规范

每条审核结果必须包含：

- `signal_id`
- `risk_level`
- `approved`
- `max_position`
- `stop_loss_rule`
- `reason`

## 交付路径

- 风控结论：`../workspace/memory/state/risk-approved-signals.json`
- 周度检查：`../workspace/memory/rebalance/weekly-check-YYYY-MM-DD.md`
