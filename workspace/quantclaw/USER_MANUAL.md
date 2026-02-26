# QuantClaw Pro v2.0 - 用户手册

**版本**: 2.0.0  
**日期**: 2026-02-23  
**状态**: 生产就绪

---

## 📖 目录

1. [快速开始](#快速开始)
2. [系统架构](#系统架构)
3. [功能详解](#功能详解)
4. [CLI命令参考](#cli命令参考)
5. [Python API](#python-api)
6. [配置指南](#配置指南)
7. [常见问题](#常见问题)

---

## 快速开始

### 安装依赖

```bash
cd ~/.openclaw/workspace/quantclaw

# 基础依赖
pip install numpy pandas scipy yfinance

# 研究模块依赖
pip install schedule requests

# 可选: Neo4j知识图谱
pip install py2neo
```

### 一分钟上手

```bash
# 运行演示
python3 quantclaw_v2.py

# 分析单只股票
python3 run_research.py analyze AAPL

# 抓取最新论文
python3 run_research.py fetch
```

---

## 系统架构

### 三层架构

```
┌─────────────────────────────────────────────────────────┐
│                     应用层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   标准版     │  │ 研究增强版   │  │   CLI工具    │  │
│  │ quantclaw_pro│  │ quantclaw_v2 │  │ run_research │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────┤
│                     核心层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   感知层     │  │   认知层     │  │   决策层     │  │
│  │ 44维特征    │  │ MBTI分类    │  │ 策略匹配    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────┤
│                     研究层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 论文抓取    │  │ 高级特征    │  │ A/B测试     │  │
│  │ arxiv爬虫   │  │ 熵/分形/混沌│  │ 效果验证    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 特征维度

| 层级 | 维度数 | 来源 |
|------|--------|------|
| 基础特征 | 32 | QuantClaw原创 |
| 研究特征 | 12 | arXiv论文复现 |
| **总计** | **44** | - |

---

## 功能详解

### 1. MBTI股性分类

**16型性格分类**:

```python
from quantclaw_v2 import QuantClawProV2, QuantClawConfig

config = QuantClawConfig()
claw = QuantClawProV2(config)

# 分析股票性格
import yfinance as yf
df = yf.download('AAPL', period='3mo')

feature_vector = claw.perception.extract_features('AAPL', df)
profile = claw.cognition.classifier.classify('AAPL', feature_vector.feature_dict)

print(f"股票: {profile.mbti_type.value}")  # 例如: INTJ
print(f"性格: {profile.mbti_name}")        # 例如: 战略大师
print(f"风险: {profile.risk_level}")       # 例如: High
```

**性格类型速查表**:

| 类型 | 名称 | 特征 | 推荐策略 |
|------|------|------|----------|
| INTJ | 战略大师 | 长周期趋势 | 成长股持有 |
| ENTJ | 霸道总裁 | 机构抱团 | 核心资产 |
| ESTP | 短线狂徒 | 高波动 | 波段交易 |
| ISTJ | 稳健守护者 | 低波动 | 价值投资 |

### 2. 熵正则化投资组合优化

**改进版熵正则化**（解决过度集中问题）:

```python
from research.improved_entropy import ImprovedEntropyRegularization

optimizer = ImprovedEntropyRegularization(
    epsilon=0.15,        # 熵正则化强度
    max_position=0.25,   # 单股最大25%
    min_positions=5      # 最少持有5只
)

# 输入预期收益和历史收益
expected_returns = {'AAPL': 0.15, 'MSFT': 0.12, ...}
returns_history = {'AAPL': aapl_returns, 'MSFT': msft_returns, ...}

result = optimizer.optimize_with_true_diversification(
    expected_returns,
    returns_history
)

# 查看结果
print(f"持仓数量: {result['num_positions']}")
print(f"分散化评分: {result['normalized_entropy']:.1%}")
print(f"推荐仓位: {result['positions']}")
```

**输出示例**:
```
持仓数量: 8
分散化评分: 100%
最大仓位: 12.5%
推荐仓位:
  AAPL: 12.5%
  MSFT: 12.5%
  JNJ: 12.5%
  ...
```

### 3. 论文自动抓取与分析

```bash
# 抓取最新论文
python3 -c "
from research.arxiv_crawler import ArxivPaperCrawler, PaperAnalyzer

crawler = ArxivPaperCrawler()
papers = crawler.fetch_recent_papers(max_results=20)

# 自动分析
analyzer = PaperAnalyzer()
analyzer.batch_analyze(crawler, limit=20)

# 查看高价值论文
high_value = crawler.search_papers('', status='analyzed')
for p in high_value[:5]:
    print(f'{p[\"title\"][:50]}... -> {p[\"integration_potential\"]}')
"
```

---

## CLI命令参考

### `run_research.py` - 主命令行工具

```bash
# 运行完整演示
python3 run_research.py demo

# 抓取最新论文
python3 run_research.py fetch [--max-results 50] [--analyze]

# 运行A/B测试
python3 run_research.py test [--stocks AAPL MSFT NVDA]

# 分析指定股票
python3 run_research.py analyze <ticker> [--period 3mo]

# 启动持续服务
python3 run_research.py server
```

### `research_cli.py` - 研究模块CLI

```bash
# 抓取论文
python3 research/research_cli.py fetch --max-results 50 --analyze

# 列出论文
python3 research/research_cli.py list [--status analyzed] [--limit 10]

# 查看论文详情
python3 research/research_cli.py view <arxiv_id>

# 更新论文状态
python3 research/research_cli.py update <arxiv_id> --status implementing

# 测试高级特征
python3 research/research_cli.py test-features AAPL --period 3mo

# 导出数据
python3 research/research_cli.py export --output ~/papers.json

# 查看统计
python3 research/research_cli.py stats
```

---

## Python API

### 基础分析

```python
from quantclaw_v2 import QuantClawProV2, QuantClawConfig
import yfinance as yf

# 配置
config = QuantClawConfig(
    use_advanced_features=True,
    use_composition_forecast=True,
    use_entropy_optimization=True,
    epsilon=0.15,
    max_position=0.25
)

# 初始化
claw = QuantClawProV2(config)

# 分析投资组合
result = claw.analyze_portfolio(
    tickers=['AAPL', 'MSFT', 'GOOGL', 'JPM', 'JNJ'],
    market_regime=MarketRegime.SIDEWAYS,
    lookback_days=120
)

# 查看结果
for ticker, personality in result['personalities'].items():
    print(f"{ticker}: {personality['mbti']} ({personality['name']})")

# 查看优化后的仓位
for ticker, pos in result['optimization']['positions'].items():
    print(f"{ticker}: {pos['weight']:.1%}")
```

### 自定义分析

```python
from research.advanced_features import AdvancedResearchFeatures

# 计算研究级特征
adv = AdvancedResearchFeatures()
features = adv.calculate_all_advanced_features(df)

print(f"样本熵: {features['sample_entropy']:.4f}")
print(f"赫斯特指数: {features['hurst_exponent']:.4f}")
print(f"分形维度: {features['fractal_dimension']:.4f}")
```

---

## 配置指南

### 配置参数说明

```python
@dataclass
class QuantClawConfig:
    # 感知层
    use_advanced_features: bool = True    # 使用研究级特征
    feature_mode: str = "hybrid"          # basic/hybrid/full_research
    
    # 研究模块
    use_composition_forecast: bool = True  # 启用组成预测
    use_entropy_optimization: bool = True  # 启用熵正则化
    
    # 熵正则化参数
    epsilon: float = 0.15        # 正则化强度 (0.1-0.3)
    max_position: float = 0.25   # 单股最大仓位 (0.2-0.3)
    min_positions: int = 5       # 最少持仓数量 (3-10)
    
    # 风险厌恶
    risk_aversion: float = 1.0   # 1.0=中性, >1=保守, <1=激进
```

### 推荐配置

**保守型投资者**:
```python
config = QuantClawConfig(
    epsilon=0.20,
    max_position=0.20,
    min_positions=8,
    risk_aversion=1.5
)
```

**平衡型投资者**:
```python
config = QuantClawConfig(
    epsilon=0.15,
    max_position=0.25,
    min_positions=5,
    risk_aversion=1.0
)
```

**激进型投资者**:
```python
config = QuantClawConfig(
    epsilon=0.10,
    max_position=0.30,
    min_positions=3,
    risk_aversion=0.8
)
```

---

## 常见问题

### Q1: 为什么熵正则化选择了这么多只股票？

**A**: 这是设计目标。改进版熵正则化强制分散，避免过度集中。
- 设置 `max_position` 限制单股最大仓位
- 设置 `min_positions` 确保最少持仓数
- 增加 `epsilon` 增强分散倾向

### Q2: 如何解读MBTI分类结果？

**A**: 
- **I/E**: 内向(独立走势) vs 外向(跟随市场)
- **N/S**: 直觉(趋势性) vs 实感(均值回归)
- **T/F**: 思考(量价逻辑) vs 情感(情绪驱动)
- **J/P**: 判断(趋势明确) vs 感知(灵活震荡)

### Q3: 研究特征有什么作用？

**A**: 
- **样本熵**: 衡量价格波动复杂度
- **赫斯特指数**: 判断趋势持续性(>0.5趋势, <0.5均值回归)
- **分形维度**: 衡量价格曲线复杂度
- **Lyapunov指数**: 评估可预测性

### Q4: 如何处理数据缺失？

**A**: 系统会自动处理:
1. 检查数据长度是否足够
2. 使用历史均值填充缺失值
3. 如果数据不足，回退到等权重策略

### Q5: 可以分析A股吗？

**A**: 当前使用Yahoo Finance数据源（美股）。
如需分析A股，需要:
1. 替换数据源为AKShare
2. 修改数据获取模块
3. 保持特征计算逻辑不变

### Q6: 如何验证策略效果？

**A**: 使用A/B测试框架:
```bash
python3 run_research.py test --stocks AAPL MSFT NVDA TSLA JPM
```

会输出:
- 基础方法 vs 研究增强方法的对比
- 夏普比率改进幅度
- 分散化效果评估

---

## 进阶用法

### 批量分析美股

```python
from us_stock_mbti_scanner import USStockMBTIScanner

scanner = USStockMBTIScanner()

# 分析所有美股
results = scanner.scan_all(delay=1.0)

# 查看MBTI分布
stats = scanner.db.get_statistics()
print(f"MBTI分布: {stats['by_mbti']}")
```

### 持续监控

```python
# 设置定时任务
import schedule
import time

def daily_analysis():
    scanner = USStockMBTIScanner()
    scanner.scan_batch(['AAPL', 'MSFT', 'GOOGL'])

schedule.every().day.at("09:30").do(daily_analysis)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 技术支持

### 日志文件
- 主日志: `~/.openclaw/workspace/quantclaw/mbti_scanner.log`
- 研究日志: `~/.openclaw/workspace/quantclaw/research/mbti_scanner.log`

### 数据库位置
- 论文数据库: `~/.openclaw/workspace/quantclaw/research/papers.db`
- 股性数据库: `~/.openclaw/workspace/quantclaw/mbti_personality.db`

### 相关文档
- 设计文档: `mbti_design_v1.md`
- 交付文档: `RESEARCH_EDITION_DELIVERY.md`
- 本手册: `USER_MANUAL.md`

---

**QuantClaw Pro v2.0 - 让学术论文驱动量化投资** 🚀
