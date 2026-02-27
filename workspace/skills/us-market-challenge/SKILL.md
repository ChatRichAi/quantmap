---
name: us-market-challenge
description: 美股多Agent流水线Phase 2交叉对质通用skill。每个分析师审阅其他两位分析师的结论，从自身专业视角提出异议、补充和修正建议。确保分析全面性，避免群体思维盲点。
---

# 交叉对质 (Cross-Challenge Review)

你正在执行美股分析流水线的 Phase 2：交叉对质环节。

你的任务是从**你的专业视角**审阅其他两位分析师的结论，找出盲点、矛盾和潜在问题。

---

## 对质规则

### 核心原则
1. **专业对焦** — 只从你的专业角度提出异议，不越界评判对方专业领域
2. **有据反驳** — 异议必须有数据或逻辑支撑，不允许空泛反对
3. **建设性** — 目标是提高分析质量，不是否定对方
4. **标注冲突等级** — 区分"致命分歧"和"补充建议"

### 对质分工

#### technical（技术分析师）审阅 sector-macro + risk
- 从价格行为角度验证板块轮动判断是否与技术面吻合
- 检查宏观判断是否有技术面反证（如指数走势与宏观叙事矛盾）
- 评估风险评分中波动率相关判断的技术合理性
- 检查时间窗口判断是否与技术形态节奏一致

#### planner（板块宏观分析师）审阅 tech-quant + risk
- 检查技术信号是否忽视宏观背景（如逆宏观方向的技术突破）
- 评估技术分析是否对板块轮动阶段变化敏感
- 检查风险评估是否充分考虑宏观尾部风险
- 验证仓位建议是否与宏观环境匹配

#### policy（风控分析师）审阅 tech-quant + sector-macro
- 检查技术分析的乐观/悲观判断是否有风控盲点
- 评估板块配置建议的集中度风险
- 验证入场建议是否有足够的止损/失效条件
- 检查整体分析是否低估尾部风险

---

## 输出 JSON 结构

写入 `memory/state/us-analysis-challenge-{role}.json`：

```json
{
  "timestamp": "ISO8601",
  "challenger": "technical|planner|policy",
  "phase": 2,
  "reviewedReports": ["被审阅的报告文件名1", "被审阅的报告文件名2"],
  "challenges": [
    {
      "id": "CHG-001",
      "targetReport": "被对质的报告",
      "targetClaim": "被质疑的结论原文/摘要",
      "challengeType": "contradiction|blind_spot|overestimate|underestimate|missing_context|timing_mismatch",
      "severity": "critical|major|minor",
      "challenge": "异议内容",
      "evidence": "支撑异议的证据/数据",
      "suggestedRevision": "修正建议",
      "confidenceInChallenge": 0-10
    }
  ],
  "agreements": [
    {
      "targetReport": "报告名",
      "claim": "认同的结论",
      "reinforcement": "从本视角补充的支持证据"
    }
  ],
  "newInsights": [
    {
      "insight": "交叉审阅中发现的新洞察",
      "relevance": "high|medium|low"
    }
  ],
  "overallAssessment": {
    "conflictCount": { "critical": 0, "major": 0, "minor": 0 },
    "alignmentScore": 0-10,
    "keyConflictSummary": "核心分歧一句话总结"
  }
}
```

## 对质质量标准

1. **每份被审阅报告至少提出 2 个有实质内容的异议**
2. **每个异议必须标注 severity 和 confidence**
3. **critical 级别异议必须有明确证据**
4. **同时标注认同的部分**（避免纯否定）
5. **鼓励发现交叉审阅带来的新洞察**
