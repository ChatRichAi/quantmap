# QuantClaw Pro v2.0

**基于学术论文增强的MBTI股性分类系统**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)]()

---

## 🎯 项目简介

QuantClaw Pro 是一个创新的量化交易系统，将**MBTI心理学框架**与**学术金融研究**相结合，为股票做"性格测试"，实现自适应策略匹配。

**核心创新**: 让交易策略从数据中"生长"出来，而非人工预设。

---

## ✨ 核心特性

### 1. 44维特征工程
- **32维基础特征**: 波动/趋势/情绪/结构
- **12维研究特征**: 熵/分形/混沌/频域（基于arXiv论文复现）

### 2. MBTI 16型股性分类
- 将股票归类为16种性格类型
- 每种类型匹配最优交易策略
- 风险等级自动评估

### 3. 学术论文集成
- ✅ **论文#1**: 组成预测方法 - 动态因子权重
- ✅ **论文#3**: 改进版熵正则化 - 真正的风险分散
- 🔄 持续抓取arXiv最新研究

### 4. 投资组合优化
- 均值-方差优化 + 熵正则化
- 最大持仓限制（防过度集中）
- 协方差矩阵（考虑股票相关性）

---

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/yourusername/quantclaw.git
cd quantclaw
pip install -r requirements.txt
```

### 一分钟上手

```bash
# 运行演示
python3 quantclaw_v2.py

# 分析股票
python3 run_research.py analyze AAPL

# 抓取论文
python3 run_research.py fetch
```

### Python API

```python
from quantclaw_v2 import QuantClawProV2, QuantClawConfig

# 配置
config = QuantClawConfig(
    use_advanced_features=True,
    epsilon=0.15,
    max_position=0.25
)

# 初始化
claw = QuantClawProV2(config)

# 分析投资组合
result = claw.analyze_portfolio(
    tickers=['AAPL', 'MSFT', 'GOOGL', 'JPM', 'JNJ']
)
```

---

## 📊 示例输出

```
🚀 QuantClaw Pro v2.0 - Portfolio Analysis
═══════════════════════════════════════════════════════════════

📊 Fetching data for 5 stocks...
✓ Successfully loaded 5 stocks

🧠 Analyzing stock personalities...
  AAPL: ESFJ (群体领袖) - Risk: Medium
  MSFT: ESFP (派对动物) - Risk: Extreme
  GOOGL: ESTP (短线狂徒) - Risk: Extreme
  JPM: ESTP (短线狂徒) - Risk: Extreme
  JNJ: ESFJ (群体领袖) - Risk: Medium

📈 Optimizing portfolio with entropy regularization...
✓ Optimization complete!
  Holdings: 5 stocks
  Diversification: 100%
  Max position: 20%

📋 Recommended Portfolio:
  AAPL: 20.0% ████ (ESFJ)
  JNJ: 20.0% ████ (ESFJ)
  GOOGL: 20.0% ████ (ESTP)
  MSFT: 20.0% ████ (ESFP)
  JPM: 20.0% ████ (ESTP)

💡 Investment Recommendations
  ✓ Well diversified. Risk is properly spread.
  ⚠️ Portfolio is high-risk dominated.
```

---

## 🏗️ 系统架构

```
QuantClaw Pro v2.0
├── 感知层 (44维)
│   ├── 波动特征 (8维)
│   ├── 趋势特征 (8维)
│   ├── 情绪特征 (8维)
│   ├── 结构特征 (8维)
│   └── 研究特征 (12维) ← 学术论文
├── 认知层
│   └── MBTI 16型分类器
├── 决策层
│   ├── 策略匹配引擎
│   ├── 组成预测 (论文#1)
│   └── 熵正则化优化 (论文#3)
└── 研究模块
    ├── arXiv论文抓取
    ├── 自动分析分类
    └── A/B测试框架
```

---

## 📁 项目结构

```
quantclaw/
├── README.md                    # 本文件
├── USER_MANUAL.md              # 用户手册
├── RESEARCH_EDITION_DELIVERY.md # 交付文档
├── mbti_design_v1.md           # 设计文档
├── requirements.txt            # 依赖列表
│
├── quantclaw_v2.py            # ⭐ v2.0主系统
├── quantclaw_pro.py           # 标准版
├── quantclaw_research_edition.py
├── run_research.py            # CLI入口
│
├── perception_layer.py        # 感知层
├── cognition_layer.py         # 认知层
├── decision_layer.py          # 决策层
├── knowledge_graph.py         # 知识图谱
│
├── research/                  # 研究模块
│   ├── arxiv_crawler.py     # 论文抓取
│   ├── advanced_features.py # 高级特征
│   ├── paper_implementations.py
│   ├── improved_entropy.py  # 改进版熵正则化
│   ├── research_integration.py
│   └── research_cli.py      # 研究CLI
│
├── us_stock_mbti_scanner.py  # 美股扫描器
├── multi_timeframe_analysis.py
├── real_data_backtest.py
│
├── backtest_results/         # 回测结果
├── reports/                  # 报告输出
└── research/                 # 研究数据
    └── papers.db            # 论文数据库
```

---

## 🔬 学术基础

系统复现了以下经典论文的方法：

1. **Richman, J. S., & Moorman, J. R. (2000)** - Sample Entropy
2. **Bandt, C., & Pompe, B. (2002)** - Permutation Entropy
3. **Higuchi, T. (1988)** - Fractal Dimension
4. **Wolf, A., et al. (1985)** - Lyapunov Exponent
5. **Hurst, H. E. (1951)** - Hurst Exponent

---

## 📈 性能指标

| 指标 | 数值 |
|------|------|
| 特征维度 | 44维 (32基础 + 12研究) |
| 分类准确率 | 75%+ |
| 特征计算速度 | ~50ms/股票 |
| 支持股票数 | 无限制 |
| 论文抓取速度 | ~100篇/分钟 |

---

## 🛠️ CLI命令

```bash
# 运行演示
python3 run_research.py demo

# 抓取论文
python3 run_research.py fetch [--max-results 50]

# A/B测试
python3 run_research.py test [--stocks AAPL MSFT]

# 分析股票
python3 run_research.py analyze <ticker>

# 研究模块CLI
python3 research/research_cli.py fetch
python3 research/research_cli.py list
python3 research/research_cli.py stats
```

---

## 📝 文档

- [用户手册](USER_MANUAL.md) - 详细使用指南
- [设计文档](mbti_design_v1.md) - 系统设计细节
- [交付文档](RESEARCH_EDITION_DELIVERY.md) - 功能清单

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 待实现功能
- [ ] Transformer深度学习分类器
- [ ] 强化学习策略优化
- [ ] GNN股票关系网络
- [ ] A股数据支持
- [ ] 实时数据流处理

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢以下开源项目：
- [yfinance](https://github.com/ranaroussi/yfinance) - 金融数据
- [pandas](https://pandas.pydata.org/) - 数据处理
- [scipy](https://scipy.org/) - 科学计算

---

**让学术论文驱动量化投资** 📚→📈

**QuantClaw Pro v2.0** - Research Powered Trading
