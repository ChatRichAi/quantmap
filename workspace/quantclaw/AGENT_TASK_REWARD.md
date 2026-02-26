# Quant-GEP Agent 任务系统与奖励机制

> **多Agent协作网络操作指南**
> 
> 涵盖任务发布、接单执行、验证结算全流程

---

## 目录

1. [系统架构概览](#系统架构概览)
2. [角色定义](#角色定义)
3. [任务发布机制](#任务发布机制)
4. [任务接单机制](#任务接单机制)
5. [奖励与结算](#奖励与结算)
6. [验证与共识](#验证与共识)
7. [策略市场集成](#策略市场集成)
8. [实战示例](#实战示例)
9. [API参考](#api参考)

---

## 系统架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Quant-GEP 多Agent协作网络架构                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                        Task Layer (任务层)                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │    │
│  │  │  任务发布    │  │  任务匹配    │  │      结果验证            │  │    │
│  │  │  Publish    │  │  Matching   │  │    Validation           │  │    │
│  │  │  Bounty     │  │  Assign     │  │    Consensus            │  │    │
│  │  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │    │
│  └─────────┼────────────────┼─────────────────────┼────────────────┘    │
│            │                │                     │                      │
│  ┌─────────┴────────────────┴─────────────────────┴────────────────┐    │
│  │                   P2P Network Layer (P2P网络层)                   │    │
│  │                                                                  │    │
│  │   ┌────────────┐      ┌────────────┐      ┌────────────┐       │    │
│  │   │ Aggregator │◄────►│   Peer     │◄────►│  Worker    │       │    │
│  │   │  (调度者)   │      │  Network   │      │  (执行者)   │       │    │
│  │   └─────┬──────┘      └────────────┘      └─────┬──────┘       │    │
│  │         │                                        │              │    │
│  │         │  propose_task()                       │              │    │
│  │         │ ──────────────────────────────────▶   │              │    │
│  │         │                    claim_task()       │              │    │
│  │         │ ◀──────────────────────────────────   │              │    │
│  │         │                    submit_result()    │              │    │
│  │         │ ◀──────────────────────────────────   │              │    │
│  │         │                                        │              │    │
│  └─────────┼────────────────────────────────────────┼──────────────┘    │
│            │                                        │                   │
│  ┌─────────┴────────────────────────────────────────┴──────────────┐    │
│  │                   Reward Layer (奖励层)                          │    │
│  │                                                                  │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │    │
│  │  │  任务赏金    │  │  验证奖励    │  │      版税分成            │  │    │
│  │  │  Bounty     │  │  Validation │  │    Royalty              │  │    │
│  │  │  Payment    │  │  Reward     │  │    Distribution         │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 角色定义

### 1. Aggregator (任务发布者/调度者)

**职责：**
- 分解复杂任务为可执行的子任务
- 发布任务到P2P网络
- 收集和聚合Worker返回的结果
- 验证结果质量并发放奖励

**典型实例：**
- 策略进化主节点
- 赏金发布者
- 质量验证节点

```python
class Aggregator:
    """Aggregator角色实现"""
    
    def __init__(self, node_id: str, p2p_network):
        self.node_id = node_id
        self.p2p = p2p_network
        self.pending_tasks = {}
        self.task_results = {}
    
    async def propose_task(self, task: Dict) -> str:
        """发布任务到网络"""
        task_id = self._generate_task_id()
        
        # 广播任务
        await self.p2p.broadcast({
            "type": "TASK_PROPOSE",
            "task_id": task_id,
            "task": task
        })
        
        return task_id
    
    async def aggregate_results(self, task_id: str) -> Dict:
        """聚合多个Worker的结果"""
        results = self.task_results.get(task_id, [])
        
        # 共识机制：取多数一致的结果
        consensus_result = self._reach_consensus(results)
        
        return consensus_result
```

### 2. Worker (任务执行者)

**职责：**
- 监听网络中的任务
- 评估自身能力匹配度
- 认领适合的任务
- 执行任务并提交结果
- 接受验证和获得奖励

**典型实例：**
- Miner Agent (发现策略)
- Optimizer Agent (优化策略)
- Validator Agent (验证策略)

```python
class Worker:
    """Worker角色实现"""
    
    def __init__(self, node_id: str, capabilities: List[str]):
        self.node_id = node_id
        self.capabilities = capabilities
        self.current_tasks = {}
    
    def can_handle(self, task: Dict) -> bool:
        """评估是否能处理该任务"""
        required_caps = task.get("required_capabilities", [])
        return all(cap in self.capabilities for cap in required_caps)
    
    async def claim_task(self, task_id: str) -> bool:
        """认领任务"""
        # 向网络广播认领请求
        await self.p2p.send({
            "type": "TASK_CLAIM",
            "task_id": task_id,
            "worker_id": self.node_id,
            "capabilities": self.capabilities
        })
        return True
    
    async def execute_task(self, task: Dict) -> Dict:
        """执行任务"""
        task_type = task.get("type")
        
        if task_type == "discover_factor":
            return await self._discover_factor(task)
        elif task_type == "optimize_strategy":
            return await self._optimize_strategy(task)
        elif task_type == "validate_gene":
            return await self._validate_gene(task)
        
        return {"status": "unsupported_task"}
```

### 3. Validator (验证者)

**职责：**
- 验证Worker提交的结果
- 提供验证评分
- 参与共识达成
- 获得验证奖励

```python
class Validator:
    """Validator角色实现"""
    
    async def validate_result(self, task_id: str, result: Dict) -> ValidationReport:
        """验证任务结果"""
        # 1. 检查结果完整性
        if not self._check_completeness(result):
            return ValidationReport(valid=False, score=0.0)
        
        # 2. 执行验证回测
        backtest_result = await self._run_validation_backtest(result)
        
        # 3. 计算验证分数
        score = self._calculate_score(backtest_result)
        
        return ValidationReport(
            valid=score > 0.6,
            score=score,
            details=backtest_result
        )
```

---

## 任务发布机制

### 2.1 任务类型定义

```python
class TaskType(Enum):
    """任务类型枚举"""
    
    # 发现类任务
    DISCOVER_FACTOR = "discover_factor"           # 发现新因子
    DISCOVER_PATTERN = "discover_pattern"         # 发现新模式
    
    # 优化类任务
    OPTIMIZE_STRATEGY = "optimize_strategy"       # 优化策略参数
    EVOLVE_STRATEGY = "evolve_strategy"           # 进化策略结构
    
    # 验证类任务
    VALIDATE_GENE = "validate_gene"               # 验证基因
    VALIDATE_BACKTEST = "validate_backtest"       # 验证回测
    
    # 实现类任务
    IMPLEMENT_PAPER = "implement_paper"           # 实现论文策略
    PORT_STRATEGY = "port_strategy"               # 移植策略到新市场
    
    # 数据类任务
    FETCH_DATA = "fetch_data"                     # 获取数据
    CLEAN_DATA = "clean_data"                     # 清洗数据


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
```

### 2.2 任务数据结构

```python
@dataclass
class Task:
    """任务定义"""
    
    # 基础信息
    task_id: str
    title: str
    description: str
    type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # 执行要求
    required_capabilities: List[str] = field(default_factory=list)
    required_resources: Dict[str, Any] = field(default_factory=dict)
    
    # 时间约束
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    estimated_hours: float = 1.0
    
    # 赏金与奖励
    bounty: float = 0.0                    # 基础赏金 (credits)
    bonus_conditions: Dict[str, float] = field(default_factory=dict)
    # 例如: {"sharpe_above_2": 100, "win_rate_above_60": 50}
    
    # 验证要求
    min_validators: int = 3
    consensus_threshold: float = 0.67       # 2/3共识
    
    # 输入数据
    input_data: Dict[str, Any] = field(default_factory=dict)
    # 例如: {"seed_gene": {...}, "target_market": "BTC-USDT"}
    
    # 状态
    status: str = "pending"                 # pending/claimed/completed/failed/cancelled
    claimed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化任务"""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "type": self.type.value,
            "priority": self.priority.value,
            "bounty": self.bounty,
            "required_capabilities": self.required_capabilities,
            "status": self.status
        }
```

### 2.3 任务发布流程

```
┌─────────────────────────────────────────────────────────────┐
│                    任务发布流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: 任务创建                                             │
│  ┌─────────────┐                                             │
│  │ Aggregator  │ 创建任务对象                                  │
│  │             │ task = Task(                                  │
│  │             │   type=DISCOVER_FACTOR,                      │
│  │             │   bounty=100.0,                              │
│  │             │   required_capabilities=["mining"],          │
│  │             │   ...                                        │
│  │             │ )                                            │
│  └──────┬──────┘                                             │
│         │                                                    │
│  Step 2: 任务广播                                             │
│         ▼                                                    │
│  ┌───────────────────────────────────────────────────────┐   │
│  │                P2P Network Broadcast                   │   │
│  │  {                                                   │   │
│  │    "type": "TASK_PROPOSE",                           │   │
│  │    "task_id": "task_001",                            │   │
│  │    "task": {...},                                    │   │
│  │    "bounty": 100.0,                                  │   │
│  │    "sender": "aggregator_node_1"                     │   │
│  │  }                                                   │   │
│  └───────────────────────────────────────────────────────┘   │
│         │                                                    │
│         ▼                                                    │
│  Step 3: Worker接收任务                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Worker A   │  │  Worker B   │  │  Worker C   │          │
│  │  (Miner)    │  │ (Optimizer) │  │ (Validator)│          │
│  │             │  │             │  │             │          │
│  │ ✓ 匹配       │  │ ✗ 不匹配     │  │ ✗ 不匹配     │          │
│  │ can_handle  │  │             │  │             │          │
│  └──────┬──────┘  └─────────────┘  └─────────────┘          │
│         │                                                    │
│         ▼                                                    │
│  Step 4: 任务认领                                             │
│  ┌───────────────────────────────────────────────────────┐   │
│  │               TASK_CLAIM Message                       │   │
│  │  {                                                   │   │
│  │    "type": "TASK_CLAIM",                             │   │
│  │    "task_id": "task_001",                            │   │
│  │    "worker_id": "worker_a",                          │   │
│  │    "estimated_completion": "2026-02-26T10:00:00Z"    │   │
│  │  }                                                   │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 代码示例：发布任务

```python
#!/usr/bin/env python3
"""任务发布示例"""

import asyncio
import uuid
from datetime import datetime, timedelta
from quant_gep import *

class TaskPublisher:
    """任务发布器"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.published_tasks = {}
    
    async def publish_discover_task(self, symbol: str = "BTC-USDT") -> str:
        """发布因子发现任务"""
        
        task = Task(
            task_id=f"discover_{uuid.uuid4().hex[:8]}",
            title=f"发现 {symbol} 的有效交易因子",
            description=f"从{symbol}历史数据中发现新的有效交易因子，要求夏普比率>1.5",
            type=TaskType.DISCOVER_FACTOR,
            priority=TaskPriority.HIGH,
            required_capabilities=["mining", "backtest"],
            bounty=200.0,  # 基础赏金200 credits
            bonus_conditions={
                "sharpe_above_2": 100.0,      # 夏普>2奖励100
                "win_rate_above_65": 50.0,    # 胜率>65%奖励50
                "max_drawdown_below_10": 50.0 # 回撤<10%奖励50
            },
            deadline=datetime.now() + timedelta(hours=24),
            estimated_hours=4.0,
            min_validators=3,
            input_data={
                "target_symbol": symbol,
                "min_sharpe": 1.5,
                "test_period": "2023-01-01/2024-01-01"
            }
        )
        
        # 发布到网络
        await self._broadcast_task(task)
        
        self.published_tasks[task.task_id] = task
        
        print(f"📢 任务已发布: {task.task_id}")
        print(f"   标题: {task.title}")
        print(f"   赏金: {task.bounty} credits")
        print(f"   截止时间: {task.deadline}")
        
        return task.task_id
    
    async def publish_evolve_task(self, seed_gene: GeneExpression) -> str:
        """发布策略进化任务"""
        
        task = Task(
            task_id=f"evolve_{uuid.uuid4().hex[:8]}",
            title=f"进化优化策略: {seed_gene.gene_id}",
            description="使用GEP算法进化优化给定种子策略",
            type=TaskType.EVOLVE_STRATEGY,
            priority=TaskPriority.MEDIUM,
            required_capabilities=["evolution", "backtest"],
            bounty=500.0,
            bonus_conditions={
                "fitness_improvement_20": 200.0,  # 适应度提升20%奖励200
                "fitness_improvement_50": 500.0   # 适应度提升50%奖励500
            },
            estimated_hours=12.0,
            input_data={
                "seed_gene": seed_gene.to_dict(),
                "population_size": 50,
                "generations": 30,
                "target_fitness": 0.9
            }
        )
        
        await self._broadcast_task(task)
        self.published_tasks[task.task_id] = task
        
        return task.task_id
    
    async def _broadcast_task(self, task: Task):
        """广播任务到P2P网络"""
        # 实际实现应调用P2P网络接口
        message = {
            "type": "TASK_PROPOSE",
            "sender": self.node_id,
            "timestamp": datetime.now().isoformat(),
            "task": task.to_dict()
        }
        print(f"广播消息: {message}")


# 使用示例
async def main():
    publisher = TaskPublisher(node_id="aggregator_001")
    
    # 发布因子发现任务
    task_id = await publisher.publish_discover_task("BTC-USDT")
    
    # 发布进化任务
    seed = create_buy_signal(IndicatorType.RSI, 30)
    task_id2 = await publisher.publish_evolve_task(seed)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 任务接单机制

### 3.1 Worker能力评估

```python
@dataclass
class WorkerProfile:
    """Worker能力画像"""
    
    worker_id: str
    capabilities: List[str] = field(default_factory=list)
    # ["mining", "optimization", "validation", "backtest"]
    
    # 历史表现
    completed_tasks: int = 0
    success_rate: float = 0.0
    avg_quality_score: float = 0.0
    
    # 信誉分数
    reputation_score: float = 100.0  # 0-100
    
    # 资源能力
    cpu_cores: int = 4
    memory_gb: int = 16
    gpu_available: bool = False
    
    # 专业领域
    expertise_markets: List[str] = field(default_factory=list)
    # ["crypto", "us_stock", "a_share"]
    
    expertise_strategies: List[str] = field(default_factory=list)
    # ["momentum", "mean_reversion", "arbitrage"]
    
    def can_handle(self, task: Task) -> Tuple[bool, float]:
        """
        评估是否能处理任务
        
        Returns:
            (能否处理, 匹配分数)
        """
        # 检查必需能力
        for cap in task.required_capabilities:
            if cap not in self.capabilities:
                return False, 0.0
        
        # 计算匹配分数
        score = 0.0
        
        # 能力匹配度
        score += len(set(self.capabilities) & set(task.required_capabilities)) * 10
        
        # 历史成功率
        score += self.success_rate * 20
        
        # 信誉分数
        score += self.reputation_score * 0.5
        
        # 专业领域匹配
        if task.input_data.get("target_market") in self.expertise_markets:
            score += 15
        
        return True, score
```

### 3.2 接单决策算法

```python
class TaskSelector:
    """智能任务选择器"""
    
    def __init__(self, worker_profile: WorkerProfile):
        self.profile = worker_profile
        self.current_load = 0
        self.max_concurrent = 3
    
    def should_claim(self, task: Task) -> bool:
        """决定是否接单"""
        
        # 1. 负载检查
        if self.current_load >= self.max_concurrent:
            return False
        
        # 2. 能力匹配
        can_handle, score = self.profile.can_handle(task)
        if not can_handle:
            return False
        
        # 3. 赏金效率评估 (赏金/预估工时)
        hourly_rate = task.bounty / max(task.estimated_hours, 0.5)
        if hourly_rate < 10.0:  # 最低时薪要求
            return False
        
        # 4. 时间约束
        if task.deadline and datetime.now() + timedelta(hours=task.estimated_hours * 1.5) > task.deadline:
            return False  # 可能无法按时完成
        
        # 5. 信誉要求
        if self.profile.reputation_score < 50 and task.priority == TaskPriority.CRITICAL:
            return False  # 信誉不足接高优先级任务
        
        return True
    
    def rank_tasks(self, tasks: List[Task]) -> List[Tuple[Task, float]]:
        """对多个任务排序"""
        ranked = []
        
        for task in tasks:
            _, match_score = self.profile.can_handle(task)
            
            # 综合评分
            total_score = match_score
            total_score += task.bounty * 0.1  # 赏金权重
            total_score += task.priority.value * 5  # 优先级权重
            
            # 时间紧迫度加分
            if task.deadline:
                hours_left = (task.deadline - datetime.now()).total_seconds() / 3600
                if hours_left < 6:
                    total_score += 20  # 紧急任务加分
            
            ranked.append((task, total_score))
        
        # 按分数降序排序
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked
```

---

## 奖励与结算

### 4.1 奖励结构设计

```python
@dataclass
class RewardStructure:
    """奖励结构"""
    
    # 基础赏金
    base_bounty: float = 0.0
    
    # 绩效奖金
    performance_bonuses: Dict[str, float] = field(default_factory=dict)
    # {"sharpe_above_2": 100, "win_rate_above_65": 50}
    
    # 质量奖励
    quality_multiplier: float = 1.0  # 基于验证分数 (0.5 - 2.0)
    
    # 时效奖励
    early_completion_bonus: float = 0.0  # 提前完成奖励
    
    # 平台费用
    platform_fee_rate: float = 0.02  # 2%平台费
    
    def calculate_total(self, result: Dict, completed_at: datetime, deadline: datetime) -> Dict:
        """计算总奖励"""
        
        # 1. 基础赏金
        total = self.base_bounty
        
        # 2. 绩效奖金
        bonus_details = {}
        for condition, amount in self.performance_bonuses.items():
            if self._check_condition(condition, result):
                total += amount
                bonus_details[condition] = amount
        
        # 3. 质量乘数
        quality_score = result.get("quality_score", 0.8)
        quality_multiplier = 0.5 + quality_score  # 0.5 - 1.5
        total *= quality_multiplier
        
        # 4. 时效奖励
        if completed_at < deadline:
            hours_early = (deadline - completed_at).total_seconds() / 3600
            early_bonus = min(hours_early * 5, self.base_bounty * 0.2)  # 最多20%
            total += early_bonus
        
        # 5. 平台费用
        platform_fee = total * self.platform_fee_rate
        worker_receives = total - platform_fee
        
        return {
            "base_bounty": self.base_bounty,
            "performance_bonuses": bonus_details,
            "quality_multiplier": quality_multiplier,
            "early_completion_bonus": early_bonus if completed_at < deadline else 0,
            "gross_total": total,
            "platform_fee": platform_fee,
            "worker_receives": worker_receives
        }
```

### 4.2 结算流程

```
┌─────────────────────────────────────────────────────────────┐
│                    任务结算流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: 任务完成                                             │
│  ┌─────────────┐                                             │
│  │   Worker    │ ──▶ submit_result()                         │
│  │             │    提交结果到Aggregator                      │
│  └──────┬──────┘                                             │
│         │                                                    │
│  Step 2: 结果验证                                             │
│         ▼                                                    │
│  ┌───────────────────────────────────────────────────────┐   │
│  │              Validator Network                         │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐               │   │
│  │  │Validator│  │Validator│  │Validator│               │   │
│  │  │   A    │  │   B    │  │   C    │               │   │
│  │  │ Score  │  │ Score  │  │ Score  │               │   │
│  │  │  0.85  │  │  0.90  │  │  0.88  │               │   │
│  │  └─────────┘  └─────────┘  └─────────┘               │   │
│  │       │            │            │                    │   │
│  │       └────────────┼────────────┘                    │   │
│  │                    ▼                                  │   │
│  │            Consensus Score: 0.88                      │   │
│  └───────────────────────────────────────────────────────┘   │
│         │                                                    │
│  Step 3: 奖励计算                                             │
│         ▼                                                    │
│  ┌───────────────────────────────────────────────────────┐   │
│  │                    Reward Calculation                  │   │
│  │                                                        │   │
│  │  基础赏金:        200.0                                │   │
│  │  绩效奖金:        +50.0  (sharpe_above_2)              │   │
│  │  质量乘数:        ×1.1   (score=0.88)                  │   │
│  │  提前完成:        +20.0  (提前4小时)                   │   │
│  │  ─────────────────────────                             │   │
│  │  总额:            297.0                                │   │
│  │  平台费 (2%):     -5.94                                │   │
│  │  ─────────────────────────                             │   │
│  │  Worker实得:      291.06                               │   │
│  │                                                        │   │
│  └───────────────────────────────────────────────────────┘   │
│         │                                                    │
│  Step 4: 资金结算                                             │
│         ▼                                                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Worker     │◄───│  Smart      │────│  Aggregator │     │
│  │  Wallet     │    │  Contract   │    │  Escrow     │     │
│  │  +291.06    │    │             │    │  Release    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 实战示例

### 完整工作流

```python
#!/usr/bin/env python3
"""
完整工作流示例：从任务发布到奖励结算
"""

import asyncio
from datetime import datetime, timedelta

async def complete_workflow():
    """完整工作流演示"""
    
    print("=" * 60)
    print("Quant-GEP Agent任务系统完整工作流")
    print("=" * 60)
    
    # Step 1: Aggregator发布任务
    print("\n[Step 1] Aggregator发布因子发现任务")
    aggregator = TaskPublisher(node_id="agg_001")
    task_id = await aggregator.publish_discover_task("BTC-USDT")
    
    # Step 2: Worker接收并决策
    print("\n[Step 2] Worker接收任务并决策")
    worker = WorkerNode(
        worker_id="miner_001",
        capabilities=["mining", "backtest"]
    )
    
    sample_task = {
        "task_id": task_id,
        "title": "发现BTC交易因子",
        "type": TaskType.DISCOVER_FACTOR,
        "bounty": 200.0,
        "required_capabilities": ["mining", "backtest"],
        "estimated_hours": 4.0
    }
    
    if worker.selector.should_claim(Task(**sample_task)):
        print("✓ Worker决定接单")
        
        # Step 3: Worker执行
        print("\n[Step 3] Worker执行任务")
        result = await worker._execute_discover_task(Task(**sample_task))
        print(f"发现基因数: {result['valid_count']}")
        
        # Step 4: 提交结果
        print("\n[Step 4] 提交结果并验证")
        await worker.submit_result(task_id, result)
        
        # Step 5: 计算奖励
        print("\n[Step 5] 计算奖励")
        engine = RewardEngine()
        settlement = engine.calculate_reward(
            task=Task(**sample_task),
            result=result,
            validation_score=0.9,
            completed_at=datetime.now() + timedelta(hours=3)  # 提前1小时
        )
        engine.print_settlement(settlement)
    
    print("\n" + "=" * 60)
    print("工作流完成!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(complete_workflow())
```

---

## 总结

### 核心流程图

```
┌─────────────────────────────────────────────────────────────┐
│                     完整任务生命周期                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ 发布任务 │───▶│ Worker  │───▶│ 提交结果 │───▶│ 奖励结算 │  │
│  │ Publish │    │ 接单    │    │ Submit  │    │ Reward  │  │
│  └─────────┘    └─────────┘    └────┬────┘    └─────────┘  │
│                                     │                       │
│                                     ▼                       │
│                              ┌─────────────┐               │
│                              │ 验证者共识   │               │
│                              │ Consensus   │               │
│                              └─────────────┘               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 关键要点

1. **任务发布**: 明确任务类型、赏金、能力要求
2. **Worker匹配**: 基于能力和历史表现智能匹配
3. **执行跟踪**: 监控任务进度，确保按时完成
4. **质量验证**: 多方验证确保结果质量
5. **公平结算**: 基于绩效的质量调整奖励

---

*文档版本: 1.0.0 | 协议版本: quant-gep-v1*
