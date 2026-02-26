# AGENTS.md - Execution Workflow

## 角色映射

- 当前目录承担 `workspace-executor` 职责。
- 负责动作执行与结果落库。

## 启动步骤

1. 读取 `SOUL.md`
2. 读取 `../workspace/memory/state/risk-approved-signals.json`
3. 读取 `../workspace/memory/state/execution-state.json`

## 执行流程

1. 拉取待执行动作
2. 校验参数完整性
3. 执行动作（模拟/实盘由配置决定）
4. 记录结果与失败原因
5. 写入复盘日志

## 输出规范

每条执行记录必须包含：

- `signal_id`
- `execution_time`
- `expected_price`
- `actual_price`
- `slippage`
- `status`
- `error`

## 交付路径

- 执行状态：`../workspace/memory/state/execution-state.json`
- 执行日志：`../workspace/memory/trades/YYYY-MM-DD.json`
