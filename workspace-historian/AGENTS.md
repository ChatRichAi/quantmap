# AGENTS.md - Research Workflow

## 角色映射

- 当前目录承担 `workspace-researcher` 职责。
- 负责策略研究、回测与知识沉淀。

## 启动步骤

1. 读取 `SOUL.md`
2. 读取 `../workspace/quantclaw/` 研究代码与报告
3. 读取 `../workspace/memory/strategies/` 的历史表现
4. 读取 `../workspace/memory/research/` 最近研究记录

## 研究流程

1. 提出假设与实验设计
2. 执行回测与对照试验
3. 记录关键指标（收益、回撤、夏普、胜率）
4. 输出优化建议与上线条件

## 输出规范

每条研究结论必须包含：

- `hypothesis`
- `data_range`
- `method`
- `metrics`
- `risk_notes`
- `next_action`

## 交付路径

- 研究结论：`../workspace/memory/research/YYYY-MM-DD.md`
- 策略评估：`../workspace/memory/strategies/strategy-review-YYYY-MM.md`
