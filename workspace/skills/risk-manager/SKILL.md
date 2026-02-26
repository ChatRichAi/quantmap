---
name: risk-manager
description: 统一风控技能，执行仓位、回撤、集中度、相关性检查。
---

# risk-manager

## 核心检查

- 单标的仓位上限
- 组合现金比例下限
- 日内/周内最大回撤
- 行业与市场集中度
- 相关性暴露

## 输入

- 候选信号列表
- 当前持仓快照
- 账户权益
- 风控参数

## 输出

- `approved_signals`
- `rejected_signals`
- `risk_notes`
- `required_actions`
