---
name: stock-personality
description: 基于 MBTI 股性模型的股票行为分类与策略匹配技能。
---

# stock-personality

## 来源

本技能整合 `workspace/quantclaw/` 内现有 MBTI 股性分析能力。

## 核心能力

- 股票行为特征提取
- MBTI 类型映射
- 策略与股性匹配
- 风险等级辅助判断

## 输入

- `symbol`
- `lookback_period`
- `market`

## 输出

```json
{
  "symbol": "AAPL",
  "mbti": "ESFJ",
  "confidence": 0.76,
  "risk_level": "medium",
  "preferred_strategies": ["trend-following", "breakout"]
}
```

## 备注

需要与 `workspace/quantclaw/` 代码和回测结果保持同步更新。
