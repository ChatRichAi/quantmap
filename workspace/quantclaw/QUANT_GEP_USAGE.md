# Quant-GEP 详细使用文档

> **开发者实战指南** - 从入门到精通
> > 版本: v1.0.0 | 协议: quant-gep-v1

---

## 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [详细教程](#详细教程)
4. [API完整参考](#api完整参考)
5. [实战案例](#实战案例)
6. [调试与优化](#调试与优化)
7. [故障排除](#故障排除)
8. [最佳实践](#最佳实践)

---

## 快速开始

### 1. 环境准备

```bash
# 确保Python版本 >= 3.10
python3 --version

# 进入QuantClaw工作目录
cd ~/.openclaw/workspace/quantclaw

# 验证quant_gep模块可用
python3 -c "from quant_gep import *; print('✅ Quant-GEP 已就绪')"
```

### 2. 第一个程序

创建文件 `first_strategy.py`:

```python
#!/usr/bin/env python3
"""你的第一个Quant-GEP策略"""

import sys
sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from quant_gep import (
    create_buy_signal, IndicatorType,
    quick_backtest, MarketType, TimeFrame
)

def main():
    print("🚀 创建第一个策略...")
    
    # 创建一个简单的RSI超卖策略
    gene = create_buy_signal(IndicatorType.RSI, threshold=30, condition="<")
    
    print(f"策略公式: {gene.to_formula()}")
    print(f"AST深度: {gene.get_depth()}")
    print(f"节点数: {gene.get_complexity()}")
    
    # 回测
    print("\n📊 执行回测...")
    result = quick_backtest(
        gene=gene,
        symbol="BTC-USDT",
        market_type=MarketType.CRYPTO,
        timeframe=TimeFrame.H1
    )
    
    print(f"\n回测结果:")
    print(f"  总交易: {result.total_trades}")
    print(f"  胜率: {result.win_rate:.1%}")
    print(f"  夏普: {result.sharpe_ratio:.2f}")
    print(f"  最大回撤: {result.max_drawdown:.1%}")

if __name__ == "__main__":
    main()
```

运行:
```bash
python3 first_strategy.py
```

---

## 核心概念

### 2.1 基因(Gene)是什么?

在Quant-GEP中，**基因**是一个可执行的交易策略，由两部分组成:

```
┌─────────────────────────────────────────┐
│              GeneExpression             │
├─────────────────────────────────────────┤
│                                         │
│  Genotype (基因型)                      │
│  ├── AST树形结构                        │
│  ├── 可变异、交叉、转位                  │
│  └── 进化的对象                         │
│                                         │
│  Phenotype (表现型)                     │
│  ├── evaluate(context) → 交易信号       │
│  └── 在市场数据上执行                   │
│                                         │
└─────────────────────────────────────────┘
```

**关键理解:**
- **Genotype** = 数据结构 (树)，可以被进化算法操作
- **Phenotype** = 行为 (函数)，在回测中产生交易信号

### 2.2 AST节点类型速查

| 节点 | 用途 | 示例 | 评估结果 |
|------|------|------|----------|
| `OperatorNode(AND)` | 逻辑与 | `A AND B` | bool |
| `OperatorNode(OR)` | 逻辑或 | `A OR B` | bool |
| `OperatorNode(>)` | 大于 | `close > SMA(20)` | bool |
| `OperatorNode(+)` | 加法 | `close + 10` | float |
| `IndicatorNode(RSI)` | 计算RSI | `RSI(14)` | float |
| `ConstantNode(30)` | 常数30 | `30` | 30.0 |
| `VariableNode(close)` | 收盘价 | `close` | 当前close |

### 2.3 进化参数详解

```python
from quant_gep import GEPConfig

config = GEPConfig(
    # 变异概率 (0.0 - 1.0)
    mutation_rate=0.1,           # 10%的概率执行单点变异
    subtree_mutation_rate=0.05,  # 5%的概率执行子树变异
    
    # 交叉概率
    crossover_rate=0.7,          # 70%的概率执行交叉
    
    # 转位概率
    is_transposition_rate=0.1,   # IS转位概率
    ris_transposition_rate=0.1,  # RIS转位概率
    
    # 反转概率
    inversion_rate=0.1,          # 反转概率
    
    # 选择参数
    tournament_size=3,           # 锦标赛大小
    elitism_count=2,             # 精英保留数量
    
    # 约束
    max_depth=10,                # 最大AST深度
    max_nodes=50                 # 最大节点数
)
```

**参数调优建议:**
- **高变异率(0.2+)** → 探索性强，但收敛慢
- **低变异率(0.05)** →  exploitation强，但易陷入局部最优
- **推荐**: 从 `mutation_rate=0.1`, `crossover_rate=0.7` 开始

---

## 详细教程

### 3.1 创建自定义基因

#### 基础: 从公式创建

```python
from quant_gep import GeneExpression

# 从字符串公式解析
gene = GeneExpression.from_formula("RSI(14) < 30 AND Volume > 1000000")
print(gene.to_formula())
```

#### 进阶: 手动构建AST

```python
from quant_gep import (
    GeneExpression, OperatorNode, Operator,
    IndicatorNode, IndicatorType,
    ConstantNode, VariableNode
)

# 构建: (RSI(14) < 30) AND (MACD > 0) AND (close > SMA(20))

# 根节点: AND
root = OperatorNode(Operator.AND)

# 条件1: RSI(14) < 30
rsi = IndicatorNode(IndicatorType.RSI, {"period": 14})
threshold1 = ConstantNode(30)
cond1 = OperatorNode(Operator.LT)
cond1.add_child(rsi)
cond1.add_child(threshold1)
root.add_child(cond1)

# 条件2: MACD > 0 (简化版，实际MACD需要更多参数)
macd = IndicatorNode(IndicatorType.MACD, {"fast": 12, "slow": 26})
zero = ConstantNode(0)
cond2 = OperatorNode(Operator.GT)
cond2.add_child(macd)
cond2.add_child(zero)
root.add_child(cond2)

# 条件3: close > SMA(20)
close = VariableNode("close")
sma20 = IndicatorNode(IndicatorType.SMA, {"period": 20})
cond3 = OperatorNode(Operator.GT)
cond3.add_child(close)
cond3.add_child(sma20)
root.add_child(cond3)

# 创建基因
gene = GeneExpression(root=root, gene_id="my_complex_strategy")
print(f"策略: {gene.to_formula()}")
print(f"深度: {gene.get_depth()}")
```

#### 专家: 动态生成基因

```python
import random
from quant_gep import *

def generate_random_strategy(max_depth=5):
    """随机生成策略"""
    generator = RandomTreeGenerator()
    tree = generator.generate_tree(max_depth=max_depth)
    return GeneExpression(root=tree)

# 生成10个随机策略
strategies = [generate_random_strategy() for _ in range(10)]
for i, s in enumerate(strategies):
    print(f"{i+1}. {s.to_formula()}")
```

### 3.2 回测详解

#### 基础回测

```python
from quant_gep import *

gene = create_buy_signal(IndicatorType.RSI, 30)

# 快速回测
result = quick_backtest(gene, "BTC-USDT", MarketType.CRYPTO, TimeFrame.H1)

# 访问结果
print(f"""
回测统计:
========
总交易次数: {result.total_trades}
盈利次数: {result.winning_trades}
亏损次数: {result.losing_trades}
胜率: {result.win_rate:.2%}

收益指标:
========
总收益率: {result.total_return:.2%}
年化收益: {result.annual_return:.2%}

风险指标:
========
最大回撤: {result.max_drawdown:.2%}
回撤天数: {result.max_drawdown_duration}
波动率: {result.volatility:.2%}

风险调整:
========
夏普比率: {result.sharpe_ratio:.2f}
索提诺比率: {result.sortino_ratio:.2f}
卡尔玛比率: {result.calmar_ratio:.2f}

交易统计:
========
平均盈利: {result.avg_win:.2f}
平均亏损: {result.avg_loss:.2f}
盈亏比: {result.profit_factor:.2f}
""")
```

#### 自定义回测适配器

```python
from quant_gep.backtest import BacktestAdapter, MarketData, BacktestResult
from quant_gep import GeneExpression

class MyCustomAdapter(BacktestAdapter):
    """自定义回测适配器示例"""
    
    def __init__(self):
        super().__init__(market_type=MarketType.CRYPTO)
    
    def get_data(self, symbol, timeframe, start_time=None, end_time=None, limit=1000):
        """获取数据 - 这里接入你的数据源"""
        # TODO: 接入你的数据API
        # 例如: 从数据库、文件、或第三方API获取
        
        # 返回模拟数据 (实际应替换为真实数据)
        return self._generate_mock_data(symbol, timeframe, limit)
    
    def run(self, gene, data, initial_capital=10000.0, position_size=1.0):
        """执行回测 - 自定义交易逻辑"""
        result = BacktestResult()
        equity = initial_capital
        
        for i in range(50, len(data)):
            context = data.get_context(i)
            
            # 获取信号
            try:
                signal = gene.evaluate(context)
            except:
                signal = False
            
            # 自定义交易逻辑
            if signal and not self.has_position:
                # 买入
                self.enter_position(data.closes[i])
            elif not signal and self.has_position:
                # 卖出
                pnl = self.exit_position(data.closes[i])
                equity += pnl
                result.equity_curve.append(equity)
        
        return result

# 使用
adapter = MyCustomAdapter()
data = adapter.get_data("BTC-USDT", TimeFrame.H1)
result = adapter.run(gene, data)
```

#### 多市场回测对比

```python
from quant_gep import *

gene = create_crossover_signal(20, 60)

markets = [
    ("AAPL", MarketType.US_STOCK, TimeFrame.D1),
    ("BTC-USDT", MarketType.CRYPTO, TimeFrame.H4),
    ("000001.SZ", MarketType.A_SHARE, TimeFrame.D1),
]

results = []
for symbol, market_type, timeframe in markets:
    result = quick_backtest(gene, symbol, market_type, timeframe)
    results.append({
        "symbol": symbol,
        "sharpe": result.sharpe_ratio,
        "drawdown": result.max_drawdown,
        "return": result.annual_return
    })

# 对比结果
print("多市场回测对比:")
print(f"{'Symbol':<15} {'Sharpe':<10} {'Drawdown':<12} {'Return':<10}")
print("-" * 50)
for r in results:
    print(f"{r['symbol']:<15} {r['sharpe']:<10.2f} {r['drawdown']:<12.2%} {r['return']:<10.2%}")
```

### 3.3 进化算法实战

#### 基础进化流程

```python
from quant_gep import *
import time

def run_evolution():
    """运行完整的进化流程"""
    
    # 1. 配置
    config = GEPConfig(
        mutation_rate=0.15,
        crossover_rate=0.75,
        max_depth=8,
        elitism_count=3
    )
    
    # 2. 创建算法
    algo = GEPAlgorithm(config)
    
    # 3. 种子策略
    seeds = [
        create_buy_signal(IndicatorType.RSI, 30),
        create_buy_signal(IndicatorType.RSI, 40),
        create_crossover_signal(10, 30),
        create_crossover_signal(20, 60),
    ]
    
    # 4. 初始化种群
    population = algo.initialize_population(size=50, seed_genes=seeds)
    print(f"初始种群: {len(population)} 个个体")
    
    # 5. 定义适应度函数
    def fitness_fn(gene):
        # 执行回测
        result = quick_backtest(gene, "BTC-USDT", MarketType.CRYPTO, TimeFrame.H1)
        
        # 综合评分 (多目标)
        if result.sharpe_ratio > 0 and result.max_drawdown < 0:
            fitness = (
                result.sharpe_ratio * 0.4 +                    # 夏普权重40%
                (1 - abs(result.max_drawdown)) * 0.3 +         # 回撤权重30%
                min(result.total_trades / 100, 1) * 0.2 +      # 交易频率20%
                result.win_rate * 0.1                          # 胜率10%
            )
        else:
            fitness = 0.01  # 最小适应度
        
        return FitnessResult(
            fitness=fitness,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown=result.max_drawdown,
            annual_return=result.annual_return,
            win_rate=result.win_rate,
            total_trades=result.total_trades
        )
    
    # 6. 执行进化
    print("\n开始进化...")
    start_time = time.time()
    
    final_pop, history = algo.evolve(
        population=population,
        fitness_fn=fitness_fn,
        generations=30,
        target_fitness=0.9,  # 目标适应度，达到则提前停止
        callback=lambda stats: print(
            f"Gen {stats.generation:2d}: best={stats.best_fitness:.4f}, "
            f"avg={stats.avg_fitness:.4f}, diversity={stats.diversity:.3f}"
        )
    )
    
    elapsed = time.time() - start_time
    print(f"\n进化完成! 耗时: {elapsed:.1f}s")
    
    # 7. 获取最优解
    final_fitness = [fitness_fn(g).fitness for g in final_pop]
    best_idx = final_fitness.index(max(final_fitness))
    best_gene = final_pop[best_idx]
    best_fitness = fitness_fn(best_gene)
    
    print(f"\n最优策略:")
    print(f"  公式: {best_gene.to_formula()}")
    print(f"  代数: {best_gene.generation}")
    print(f"  适应度: {best_fitness.fitness:.4f}")
    print(f"  夏普: {best_fitness.sharpe_ratio:.2f}")
    print(f"  回撤: {best_fitness.max_drawdown:.2%}")
    
    return best_gene, history

if __name__ == "__main__":
    best, history = run_evolution()
```

#### 收敛分析

```python
import json

# 获取收敛报告
report = algo.get_convergence_report()
print(json.dumps(report, indent=2))

# 输出示例:
# {
#   "total_generations": 30,
#   "final_best_fitness": 0.9234,
#   "initial_best_fitness": 0.5234,
#   "improvement": 0.4000,
#   "fitness_trend": [0.52, 0.55, 0.61, ..., 0.92],
#   "converged": true
# }

# 绘制进化曲线 (需要matplotlib)
def plot_evolution(history):
    try:
        import matplotlib.pyplot as plt
        
        generations = [h.generation for h in history]
        best = [h.best_fitness for h in history]
        avg = [h.avg_fitness for h in history]
        
        plt.figure(figsize=(12, 6))
        plt.plot(generations, best, label='Best Fitness', linewidth=2)
        plt.plot(generations, avg, label='Avg Fitness', linewidth=2, alpha=0.7)
        plt.xlabel('Generation')
        plt.ylabel('Fitness')
        plt.title('Evolution Progress')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig('evolution_curve.png')
        print("图表已保存: evolution_curve.png")
    except ImportError:
        print("请安装matplotlib: pip install matplotlib")

plot_evolution(history)
```

### 3.4 数据序列化与存储

#### 基础序列化

```python
from quant_gep import *
import json

# 创建并验证策略
gene = create_crossover_signal(20, 60)
gene.gene_id = "strategy_001"
gene.generation = 10

# 执行回测获取验证数据
result = quick_backtest(gene, "BTC-USDT")

# 序列化为Quant-GEP格式
payload = serialize_gene(
    gene=gene,
    validation=ValidationInfo(
        status=ValidationStatus.VALIDATED,
        sharpe_ratio=result.sharpe_ratio,
        max_drawdown=result.max_drawdown,
        annual_return=result.annual_return,
        win_rate=result.win_rate,
        total_trades=result.total_trades,
        test_symbols=["BTC-USDT"],
        test_period="2020-01-01/2024-01-01"
    ),
    meta=Metadata(
        author="QuantClaw-Trader",
        source=GeneSource.EVOLUTION,
        tags=["sma", "trend_following", "crypto", "btc"],
        description="20/60日均线金叉策略，经30代GEP进化优化"
    )
)

# 保存为JSON
with open("strategy_001.json", "w") as f:
    json.dump(payload, f, indent=2)

print("策略已保存: strategy_001.json")
```

#### 批量策略管理

```python
import os
import glob

class StrategyLibrary:
    """策略库管理器"""
    
    def __init__(self, storage_dir="strategies"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def save(self, gene, name=None):
        """保存策略"""
        if name is None:
            name = gene.gene_id or f"strategy_{hash(str(gene.to_dict()))}"
        
        filepath = os.path.join(self.storage_dir, f"{name}.json")
        
        payload = serialize_gene(gene)
        with open(filepath, "w") as f:
            json.dump(payload, f, indent=2)
        
        return filepath
    
    def load(self, name):
        """加载策略"""
        filepath = os.path.join(self.storage_dir, f"{name}.json")
        
        with open(filepath, "r") as f:
            payload = json.load(f)
        
        return deserialize_gene(payload)
    
    def list_all(self):
        """列出所有策略"""
        files = glob.glob(os.path.join(self.storage_dir, "*.json"))
        return [os.path.basename(f).replace(".json", "") for f in files]
    
    def filter_by_tag(self, tag):
        """按标签筛选"""
        results = []
        for name in self.list_all():
            gene = self.load(name)
            meta = getattr(gene, '_meta', None)
            if meta and tag in meta.tags:
                results.append(name)
        return results

# 使用示例
lib = StrategyLibrary()

# 保存多个策略
strategies = [
    create_buy_signal(IndicatorType.RSI, 30),
    create_buy_signal(IndicatorType.RSI, 40),
    create_crossover_signal(20, 60),
]

for i, s in enumerate(strategies):
    s.gene_id = f"batch_{i}"
    filepath = lib.save(s, name=f"batch_strategy_{i}")
    print(f"保存: {filepath}")

# 列出所有策略
print(f"\n策略库: {lib.list_all()}")

# 加载并验证
loaded = lib.load("batch_strategy_0")
print(f"\n加载成功: {loaded.to_formula()}")
```

---

## API完整参考

### Core模块

#### GeneExpression

```python
class GeneExpression:
    def __init__(self, root: GeneASTNode, gene_id: str = None, generation: int = 0)
    def evaluate(self, context: MarketContext) -> Union[bool, float]
    def to_dict(self) -> dict
    def to_json(self) -> str
    def to_formula(self) -> str
    def clone(self) -> GeneExpression
    def get_depth(self) -> int
    def get_complexity(self) -> int
    
    @classmethod
    def from_dict(cls, data: dict) -> GeneExpression
    @classmethod
    def from_json(cls, json_str: str) -> GeneExpression
    @classmethod
    def from_formula(cls, formula: str) -> GeneExpression
```

#### GeneASTNode

```python
class GeneASTNode(ABC):
    node_type: NodeType
    children: List[GeneASTNode]
    parent: Optional[GeneASTNode]
    
    @abstractmethod
    def evaluate(self, context: MarketContext) -> Union[bool, float]
    
    def add_child(self, child: GeneASTNode)
    def remove_child(self, child: GeneASTNode)
    def replace_child(self, old: GeneASTNode, new: GeneASTNode)
    def get_depth(self) -> int
    def get_node_count(self) -> int
    def traverse(self) -> List[GeneASTNode]
    def find_nodes(self, predicate) -> List[GeneASTNode]
```

### Operators模块

#### 变异算子

```python
class PointMutation:
    def __init__(self, config: GEPConfig)
    def mutate(self, gene: GeneExpression) -> GeneExpression

class SubtreeMutation:
    def __init__(self, config: GEPConfig)
    def mutate(self, gene: GeneExpression) -> GeneExpression
```

#### 交叉算子

```python
class OnePointCrossover:
    def __init__(self, config: GEPConfig)
    def crossover(self, p1: GeneExpression, p2: GeneExpression) -> Tuple[GeneExpression, GeneExpression]

class UniformCrossover:
    def __init__(self, config: GEPConfig)
    def crossover(self, p1: GeneExpression, p2: GeneExpression) -> Tuple[GeneExpression, GeneExpression]
```

#### 选择算子

```python
class SelectionOperator:
    def __init__(self, config: GEPConfig)
    def tournament_selection(self, pop, scores, k=3) -> GeneExpression
    def roulette_selection(self, pop, scores) -> GeneExpression
    def elitism_selection(self, pop, scores, count) -> List[GeneExpression]
```

### Evolution模块

```python
class GEPAlgorithm:
    def __init__(self, config: Optional[GEPConfig] = None)
    def evolve(self, population, fitness_fn, generations=50, 
               target_fitness=None, callback=None) -> Tuple[List[GeneExpression], List[EvolutionStats]]
    def initialize_population(self, size: int, seed_genes=None) -> List[GeneExpression]
    def get_convergence_report(self) -> dict

def quick_evolve(seed_gene, fitness_fn, pop_size=50, generations=30) -> Tuple[GeneExpression, List[EvolutionStats]]
```

### Backtest模块

```python
class BacktestAdapter(ABC):
    @abstractmethod
    def get_data(self, symbol, timeframe, start, end, limit) -> MarketData
    @abstractmethod
    def run(self, gene, data, initial_capital, position_size) -> BacktestResult

class SimpleBacktestEngine(BacktestAdapter):
    def __init__(self)
    def get_data(self, symbol, timeframe, limit=1000) -> MarketData
    def run(self, gene, data, initial_capital=10000, position_size=1.0) -> BacktestResult

def quick_backtest(gene, symbol, market_type, timeframe) -> BacktestResult
def create_adapter(market_type: MarketType) -> BacktestAdapter
```

### Protocol模块

```python
class QuantGEPSchema:
    @staticmethod
    def serialize(gene, validation=None, meta=None) -> dict
    @staticmethod
    def deserialize(payload: dict) -> GeneExpression
    @staticmethod
    def to_json(gene, **kwargs) -> str
    @staticmethod
    def from_json(json_str: str) -> GeneExpression
    @staticmethod
    def validate(payload: dict) -> Tuple[bool, List[str]]

# 便捷函数
def serialize_gene(gene, **kwargs) -> dict
def deserialize_gene(payload) -> GeneExpression
def gene_to_json(gene, **kwargs) -> str
def gene_from_json(json_str) -> GeneExpression
```

---

## 实战案例

### 案例1: RSI均值回归策略发现

```python
#!/usr/bin/env python3
"""
实战案例1: 自动发现最优RSI均值回归策略
目标: 找到最佳RSI周期和阈值
"""

import sys
sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from quant_gep import *
import json

def discover_rsi_strategy():
    print("=" * 60)
    print("实战案例: RSI均值回归策略自动发现")
    print("=" * 60)
    
    # 1. 创建参数化RSI基因模板
    def create_rsi_gene(period, threshold):
        rsi = IndicatorNode(IndicatorType.RSI, {"period": period})
        const = ConstantNode(threshold)
        op = OperatorNode(Operator.LT)
        op.add_child(rsi)
        op.add_child(const)
        return GeneExpression(root=op)
    
    # 2. 初始化种群 (覆盖不同参数组合)
    seeds = []
    for period in [7, 14, 21]:
        for threshold in [20, 30, 40]:
            gene = create_rsi_gene(period, threshold)
            gene.gene_id = f"rsi_{period}_{threshold}"
            seeds.append(gene)
    
    print(f"\n初始种子: {len(seeds)} 个")
    for s in seeds:
        print(f"  - {s.to_formula()}")
    
    # 3. 配置进化
    config = GEPConfig(
        mutation_rate=0.2,  # 高变异率探索参数空间
        crossover_rate=0.6,
        max_depth=3,  # 限制深度，保持简单
        tournament_size=2
    )
    
    algo = GEPAlgorithm(config)
    population = algo.initialize_population(size=30, seed_genes=seeds)
    
    # 4. 适应度函数
    def fitness_fn(gene):
        # 回测
        result = quick_backtest(gene, "BTC-USDT", MarketType.CRYPTO, TimeFrame.H4)
        
        # 优先高夏普 + 低回撤
        if result.sharpe_ratio <= 0 or result.max_drawdown >= 0:
            return FitnessResult(fitness=0.01)
        
        fitness = (
            result.sharpe_ratio * 0.5 +
            (1 - abs(result.max_drawdown)) * 0.3 +
            result.win_rate * 0.2
        )
        
        return FitnessResult(
            fitness=fitness,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown=result.max_drawdown,
            win_rate=result.win_rate
        )
    
    # 5. 执行进化
    print("\n开始进化...")
    final_pop, history = algo.evolve(
        population=population,
        fitness_fn=fitness_fn,
        generations=20,
        callback=lambda s: print(f"Gen {s.generation}: best={s.best_fitness:.4f}")
    )
    
    # 6. 获取最优策略
    best_fitnesses = [fitness_fn(g) for g in final_pop]
    best_idx = max(range(len(best_fitnesses)), key=lambda i: best_fitnesses[i].fitness)
    best_gene = final_pop[best_idx]
    best_fit = best_fitnesses[best_idx]
    
    print("\n" + "=" * 60)
    print("最优策略发现!")
    print("=" * 60)
    print(f"策略: {best_gene.to_formula()}")
    print(f"适应度: {best_fit.fitness:.4f}")
    print(f"夏普: {best_fit.sharpe_ratio:.2f}")
    print(f"回撤: {best_fit.max_drawdown:.2%}")
    print(f"胜率: {best_fit.win_rate:.1%}")
    
    # 7. 保存
    payload = serialize_gene(best_gene, validation=ValidationInfo(
        status=ValidationStatus.VALIDATED,
        sharpe_ratio=best_fit.sharpe_ratio,
        max_drawdown=best_fit.max_drawdown
    ))
    
    with open("discovered_rsi_strategy.json", "w") as f:
        json.dump(payload, f, indent=2)
    
    print(f"\n已保存: discovered_rsi_strategy.json")
    
    return best_gene

if __name__ == "__main__":
    discover_rsi_strategy()
```

### 案例2: 多因子组合策略进化

```python
#!/usr/bin/env python3
"""
实战案例2: 多因子组合策略进化
目标: 结合RSI、MACD、成交量等多个因子
"""

import sys
sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from quant_gep import *

def build_multi_factor_strategy():
    print("=" * 60)
    print("实战案例: 多因子组合策略进化")
    print("=" * 60)
    
    # 1. 创建基础因子库
    def create_rsi_factor(period=14, threshold=30):
        rsi = IndicatorNode(IndicatorType.RSI, {"period": period})
        const = ConstantNode(threshold)
        op = OperatorNode(Operator.LT)
        op.add_child(rsi)
        op.add_child(const)
        return GeneExpression(root=op)
    
    def create_volume_factor(threshold=1000000):
        vol = VariableNode("volume")
        const = ConstantNode(threshold)
        op = OperatorNode(Operator.GT)
        op.add_child(vol)
        op.add_child(const)
        return GeneExpression(root=op)
    
    def create_sma_factor(fast=20, slow=60):
        sma_fast = IndicatorNode(IndicatorType.SMA, {"period": fast})
        sma_slow = IndicatorNode(IndicatorType.SMA, {"period": slow})
        op = OperatorNode(Operator.GT)
        op.add_child(sma_fast)
        op.add_child(sma_slow)
        return GeneExpression(root=op)
    
    # 2. 创建组合策略模板
    def combine_factors(factors, operator=Operator.AND):
        if len(factors) == 0:
            return None
        if len(factors) == 1:
            return factors[0]
        
        root = OperatorNode(operator)
        for f in factors:
            root.add_child(f.root.clone())
        return GeneExpression(root=root)
    
    # 3. 初始化
    rsi_factor = create_rsi_factor(14, 30)
    vol_factor = create_volume_factor(500000)
    sma_factor = create_sma_factor(10, 30)
    
    base_combination = combine_factors([rsi_factor, vol_factor], Operator.AND)
    
    print(f"\n基础组合: {base_combination.to_formula()}")
    
    # 4. 进化配置
    config = GEPConfig(
        mutation_rate=0.15,
        crossover_rate=0.7,
        max_depth=6,
        elitism_count=2
    )
    
    algo = GEPAlgorithm(config)
    population = algo.initialize_population(size=40, seed_genes=[base_combination])
    
    # 5. 适应度 (多目标优化)
    def fitness_fn(gene):
        # 多市场回测验证
        markets = [
            ("BTC-USDT", MarketType.CRYPTO),
            ("ETH-USDT", MarketType.CRYPTO),
        ]
        
        total_fitness = 0
        sharpe_list = []
        
        for symbol, market in markets:
            result = quick_backtest(gene, symbol, market, TimeFrame.H4)
            
            if result.sharpe_ratio > 0:
                market_fitness = (
                    result.sharpe_ratio * 0.5 +
                    (1 - abs(result.max_drawdown)) * 0.3 +
                    result.win_rate * 0.2
                )
                total_fitness += market_fitness
                sharpe_list.append(result.sharpe_ratio)
        
        avg_fitness = total_fitness / len(markets) if markets else 0
        
        # 惩罚跨市场差异大的策略
        if sharpe_list:
            sharpe_std = statistics.stdev(sharpe_list) if len(sharpe_list) > 1 else 0
            stability_penalty = sharpe_std * 0.1
            avg_fitness -= stability_penalty
        
        return FitnessResult(fitness=max(0.01, avg_fitness))
    
    # 6. 进化
    print("\n开始多因子进化...")
    final_pop, history = algo.evolve(
        population=population,
        fitness_fn=fitness_fn,
        generations=25
    )
    
    # 7. 结果
    best = max(final_pop, key=lambda g: fitness_fn(g).fitness)
    print(f"\n最优多因子策略: {best.to_formula()}")
    
    # 8. 验证各个市场
    print("\n跨市场验证:")
    for symbol in ["BTC-USDT", "ETH-USDT", "SOL-USDT"]:
        result = quick_backtest(best, symbol, MarketType.CRYPTO, TimeFrame.H4)
        print(f"  {symbol}: Sharpe={result.sharpe_ratio:.2f}, WinRate={result.win_rate:.1%}")
    
    return best

if __name__ == "__main__":
    import statistics
    build_multi_factor_strategy()
```

---

## 调试与优化

### 启用详细日志

```python
import logging

# 启用Quant-GEP调试日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 或者仅启用特定模块
logger = logging.getLogger('quant_gep.evolution')
logger.setLevel(logging.DEBUG)
```

### 性能分析

```python
import cProfile
import pstats

def profile_evolution():
    """分析进化性能瓶颈"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 运行进化
    algo = GEPAlgorithm(GEPConfig())
    pop = algo.initialize_population(30)
    algo.evolve(pop, fitness_fn, generations=10)
    
    profiler.disable()
    
    # 输出统计
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # 输出前20个最耗时函数

profile_evolution()
```

### 内存优化

```python
# 对于大规模进化，使用生成器节省内存
def lazy_population_generator(size):
    """惰性生成种群"""
    for i in range(size):
        gene = generate_random_strategy()
        yield gene

# 处理大量基因时，使用批处理
def batch_process(genes, batch_size=100):
    """批处理基因"""
    for i in range(0, len(genes), batch_size):
        batch = genes[i:i+batch_size]
        # 处理这批基因
        process_batch(batch)
        # 显式释放内存
        del batch
        import gc
        gc.collect()
```

---

## 故障排除

### 常见问题

#### Q1: ImportError: cannot import name 'xxx'

**原因**: Python路径问题或模块未正确安装

**解决**:
```python
import sys
sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

# 验证路径
import os
print(os.listdir('/Users/oneday/.openclaw/workspace/quantclaw/quant_gep'))
```

#### Q2: gene.evaluate() 返回错误

**原因**: AST结构不完整或指标计算失败

**调试**:
```python
# 打印AST结构
def print_tree(node, indent=0):
    print("  " * indent + f"{type(node).__name__}: {getattr(node, 'value', '')}")
    for child in node.children:
        print_tree(child, indent + 1)

print_tree(gene.root)

# 逐步测试
context = MarketContext(
    symbol="TEST",
    timestamp=0,
    open=100,
    high=105,
    low=98,
    close=102,
    volume=10000
)

try:
    result = gene.evaluate(context)
    print(f"结果: {result}")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
```

#### Q3: 进化收敛太快/太慢

**调整建议**:
```python
# 收敛太快 (陷入局部最优)
config = GEPConfig(
    mutation_rate=0.2,      # 提高变异率
    subtree_mutation_rate=0.1,  # 增加子树变异
    crossover_rate=0.5,     # 降低交叉率
    tournament_size=5,      # 增大赛 tournament
)

# 收敛太慢 (搜索效率低)
config = GEPConfig(
    mutation_rate=0.05,     # 降低变异率
    crossover_rate=0.8,     # 提高交叉率
    elitism_count=5,        # 增加精英保留
)
```

#### Q4: 回测结果不一致

**原因**: 随机数据或时间戳问题

**解决**:
```python
import random
import numpy as np

# 设置随机种子保证可重复
random.seed(42)
np.random.seed(42)

# 使用真实历史数据而非模拟数据
```

---

## 最佳实践

### 1. 策略设计原则

```python
"""
✅ 好的策略特征:
- 逻辑简单清晰 (深度 < 6)
- 有明确的交易逻辑
- 在多个市场有效
- 参数不过度优化

❌ 避免:
- 过度复杂的嵌套条件
- 太多参数 (易过拟合)
- 只在特定时间段有效
- 与实际交易逻辑不符
"""

# 好的例子: 清晰的逻辑
good_strategy = GeneExpression.from_formula(
    "RSI(14) < 30 AND close > SMA(20)"
)

# 坏的例子: 过于复杂
bad_strategy = GeneExpression.from_formula(
    "RSI(14) < 30 AND RSI(14) > 20 AND close > SMA(20) AND close < SMA(60) AND volume > 1000000"
)
```

### 2. 进化参数调优指南

| 场景 | mutation_rate | crossover_rate | 代数 | 种群大小 |
|------|---------------|----------------|------|----------|
| 探索新策略 | 0.2 | 0.5 | 50+ | 100+ |
| 优化现有策略 | 0.05 | 0.8 | 20 | 50 |
| 快速验证 | 0.1 | 0.7 | 10 | 30 |
| 精细调优 | 0.03 | 0.6 | 100 | 200 |

### 3. 回测验证清单

```python
def validate_strategy(gene, symbol="BTC-USDT"):
    """策略验证清单"""
    checks = {}
    
    # 1. 基础回测
    result = quick_backtest(gene, symbol)
    checks['sharpe > 0'] = result.sharpe_ratio > 0
    checks['drawdown < 50%'] = abs(result.max_drawdown) < 0.5
    checks['trades > 10'] = result.total_trades > 10
    
    # 2. 跨时间验证
    # TODO: 使用不同时间段数据
    
    # 3. 跨市场验证
    for sym in ["BTC-USDT", "ETH-USDT"]:
        r = quick_backtest(gene, sym)
        checks[f'{sym} works'] = r.sharpe_ratio > 0
    
    # 4. 结构检查
    checks['depth < 8'] = gene.get_depth() < 8
    checks['nodes < 20'] = gene.get_complexity() < 20
    
    print("策略验证结果:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    
    return all(checks.values())
```

### 4. 生产部署建议

```python
"""
生产环境部署检查清单:

□ 使用真实历史数据 (非模拟)
□ 设置合理的滑点和手续费
□ 考虑市场冲击和流动性
□ 实施严格的风险管理
□ 有失效检测和自动停止机制
□ 策略版本控制和回滚方案
□ 实时监控和告警
"""

# 生产级回测配置
production_config = {
    'slippage': 0.001,      # 0.1% 滑点
    'commission': 0.001,    # 0.1% 手续费
    'max_position': 0.2,    # 最大20%仓位
    'stop_loss': 0.05,      # 5%止损
}
```

---

## 附录

### A. 完整示例代码库

所有示例代码位于:
```
~/.openclaw/workspace/quantclaw/quant_gep/examples.py
```

运行示例:
```bash
cd ~/.openclaw/workspace/quantclaw
python3 -m quant_gep.examples
```

### B. 更新日志

**v1.0.0 (2026-02-25)**
- ✅ 初始版本发布
- ✅ Core AST模块
- ✅ Operators进化算子
- ✅ Evolution算法
- ✅ Backtest回测引擎
- ✅ Protocol序列化
- ✅ API接口

### C. 获取帮助

- 文档: `QUANT_GEP_PROTOCOL.md`
- 示例: `quant_gep/examples.py`
- 测试: 运行各模块的 `if __name__ == "__main__"` 部分

---

*本文档与Quant-GEP v1.0.0同步更新*
