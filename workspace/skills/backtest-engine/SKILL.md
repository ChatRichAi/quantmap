---
name: backtest-engine
description: 策略回测技能，支持单策略与多策略组合评估。
---

# backtest-engine

## 功能

- 历史数据回测
- 样本外验证
- 指标输出: 收益率、最大回撤、夏普、胜率、盈亏比
- 参数敏感性测试

## 输入

- 策略定义
- 回测区间
- 市场与标的
- 成本参数（手续费/滑点）

## 输出

- `report.json`
- `equity_curve.csv`
- `summary.md`

## 集成建议

优先复用 `workspace/quantclaw/` 现有回测能力。
