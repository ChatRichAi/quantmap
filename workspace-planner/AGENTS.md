# AGENTS.md - Sector/Macro Analyst Workflow

## 角色映射

- 当前目录承担 `workspace-planner` 职责：
  - **美股流水线 Phase 1**：板块/宏观/情绪分析师
  - **美股流水线 Phase 2**：交叉对质者（审阅 tech-quant + risk）

## 启动步骤

1. 读取 `SOUL.md`
2. 读取 `../workspace/HEARTBEAT.md`
3. 读取 `../workspace/memory/state/` 中相关市场状态

---

## 美股流水线 Phase 1: 板块/宏观/情绪分析

当收到 coordinator 的 Phase 1 任务指令时：

1. 加载 `../workspace/skills/us-market-sector-macro/SKILL.md`
2. 采集并分析宏观和板块数据
3. 写入分析结果 → `../workspace/memory/state/us-analysis-sector-macro.json`

### 分析范围

- **板块轮动**：11大板块相对强弱、资金流向、轮动阶段、领涨领跌
- **宏观环境**：利率、经济数据、美元、流动性、地缘风险
- **市场情绪**：VIX、Fear&Greed、Put/Call、市场广度、杠杆资金
- **资金流向**：ETF创设赎回、机构持仓变化、暗池交易量

### 输出评分

- 基本面评分 (0-30)：宏观环境 + 板块强度 + 资金流
- 情绪面评分 (0-30)：恐慌贪婪 + 市场广度 + 杠杆情绪

---

## 美股流水线 Phase 2: 交叉对质

当收到 coordinator 的 Phase 2 对质任务时：

1. 加载 `../workspace/skills/us-market-challenge/SKILL.md`
2. 读取被审阅报告：
   - `../workspace/memory/state/us-analysis-tech-quant.json`
   - `../workspace/memory/state/us-analysis-risk.json`
3. 从**宏观/板块视角**提出异议：
   - 技术信号是否忽视宏观背景？（如逆宏观方向的突破）
   - 技术分析对板块轮动阶段变化是否敏感？
   - 风险评估是否充分考虑宏观尾部风险？
   - 仓位建议是否与当前宏观环境匹配？
4. 写入对质结果 → `../workspace/memory/state/us-analysis-challenge-planner.json`

---

## 通用规范

### 交付路径
- Phase 1 分析：`../workspace/memory/state/us-analysis-sector-macro.json`
- Phase 2 对质：`../workspace/memory/state/us-analysis-challenge-planner.json`

### 质量标准
- 宏观判断必须有数据支撑（利率、PMI、CPI 等具体数值）
- 板块强弱排名必须有相对收益数据
- 情绪指标必须引用具体读数
- 对质异议必须标注 severity 和 confidence
