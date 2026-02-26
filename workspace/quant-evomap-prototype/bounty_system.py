"""
Bounty System - Quant EvoMap 赏金市场
任务发布、认领、验证、奖励分配
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
import json
import uuid


class BountyType(Enum):
    """赏金类型"""
    STRATEGY_DISCOVERY = "strategy_discovery"      # 发现新策略
    STRATEGY_OPTIMIZATION = "strategy_optimization" # 优化现有策略
    STRATEGY_VALIDATION = "strategy_validation"     # 验证策略
    STRATEGY_MIGRATION = "strategy_migration"       # 迁移策略到新市场
    PORTFOLIO_CONSTRUCTION = "portfolio_construction" # 构建组合


class BountyStatus(Enum):
    """赏金状态"""
    OPEN = "open"               # 开放中
    CLAIMED = "claimed"         # 已被认领
    VALIDATING = "validating"   # 验证中
    COMPLETED = "completed"     # 已完成
    EXPIRED = "expired"         # 已过期
    CANCELLED = "cancelled"     # 已取消


@dataclass
class ValidationCriteria:
    """验证标准"""
    min_sharpe: float = 1.0
    min_win_rate: float = 0.5
    max_drawdown: float = 0.2
    min_trades: int = 30
    min_profit_factor: float = 1.5
    
    def to_dict(self) -> Dict:
        return {
            'min_sharpe': self.min_sharpe,
            'min_win_rate': self.min_win_rate,
            'max_drawdown': self.max_drawdown,
            'min_trades': self.min_trades,
            'min_profit_factor': self.min_profit_factor
        }
    
    def check(self, performance: Dict) -> bool:
        """检查表现是否达标"""
        return (
            performance.get('sharpe_ratio', 0) >= self.min_sharpe and
            performance.get('win_rate', 0) >= self.min_win_rate and
            performance.get('max_drawdown', 0) <= self.max_drawdown and
            performance.get('trades', 0) >= self.min_trades and
            performance.get('profit_factor', 0) >= self.min_profit_factor
        )


@dataclass
class Reward:
    """奖励结构"""
    base: float = 100.0             # 基础奖励
    bonus: float = 0.0              # 超额奖励
    token: str = "QUANT"            # 代币类型
    
    # 分级奖励
    tier_bonus: Dict[str, float] = field(default_factory=lambda: {
        'gold': 1.5,      # 夏普 > 2.0
        'silver': 1.2,    # 夏普 1.5-2.0
        'bronze': 1.0     # 夏普 1.0-1.5
    })
    
    def calculate(self, performance: Dict) -> float:
        """计算实际奖励"""
        sharpe = performance.get('sharpe_ratio', 0)
        
        # 确定等级
        if sharpe >= 2.0:
            tier = 'gold'
        elif sharpe >= 1.5:
            tier = 'silver'
        else:
            tier = 'bronze'
        
        multiplier = self.tier_bonus.get(tier, 1.0)
        return self.base * multiplier + self.bonus
    
    def to_dict(self) -> Dict:
        return {
            'base': self.base,
            'bonus': self.bonus,
            'token': self.token,
            'tier_bonus': self.tier_bonus
        }


@dataclass
class Bounty:
    """赏金任务"""
    # 基本信息
    id: str = field(default_factory=lambda: f"bounty_{uuid.uuid4().hex[:12]}")
    type: BountyType = BountyType.STRATEGY_DISCOVERY
    status: BountyStatus = BountyStatus.OPEN
    
    # 任务参数
    symbol: str = ""                    # 目标股票/标的
    timeframe: str = "1d"               # 时间周期
    market: str = "US_EQUITY"           # 市场
    data_range: Dict[str, str] = field(default_factory=dict)  # 数据范围
    
    # 标准和奖励
    criteria: ValidationCriteria = field(default_factory=ValidationCriteria)
    reward: Reward = field(default_factory=Reward)
    
    # 元信息
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deadline: Optional[str] = None
    priority: str = "medium"  # low, medium, high, critical
    
    # 认领信息
    claimed_by: Optional[str] = None
    claimed_at: Optional[str] = None
    
    # 提交记录
    submissions: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'type': self.type.value,
            'status': self.status.value,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'market': self.market,
            'data_range': self.data_range,
            'criteria': self.criteria.to_dict(),
            'reward': self.reward.to_dict(),
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'created_by': self.created_by,
            'created_at': self.created_at,
            'deadline': self.deadline,
            'priority': self.priority,
            'claimed_by': self.claimed_by,
            'claimed_at': self.claimed_at,
            'submissions': self.submissions
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Bounty':
        return cls(
            id=data['id'],
            type=BountyType(data['type']),
            status=BountyStatus(data['status']),
            symbol=data.get('symbol', ''),
            timeframe=data.get('timeframe', '1d'),
            market=data.get('market', 'US_EQUITY'),
            data_range=data.get('data_range', {}),
            criteria=ValidationCriteria(**data.get('criteria', {})),
            reward=Reward(**data.get('reward', {})),
            title=data.get('title', ''),
            description=data.get('description', ''),
            tags=data.get('tags', []),
            created_by=data.get('created_by', ''),
            created_at=data.get('created_at', datetime.now().isoformat()),
            deadline=data.get('deadline'),
            priority=data.get('priority', 'medium'),
            claimed_by=data.get('claimed_by'),
            claimed_at=data.get('claimed_at'),
            submissions=data.get('submissions', [])
        )
    
    def claim(self, agent_id: str) -> bool:
        """认领任务"""
        if self.status != BountyStatus.OPEN:
            return False
        
        self.status = BountyStatus.CLAIMED
        self.claimed_by = agent_id
        self.claimed_at = datetime.now().isoformat()
        return True
    
    def submit(self, gene_id: str, performance: Dict, agent_id: str) -> Dict:
        """提交结果"""
        submission = {
            'id': f"sub_{uuid.uuid4().hex[:8]}",
            'gene_id': gene_id,
            'performance': performance,
            'agent_id': agent_id,
            'submitted_at': datetime.now().isoformat(),
            'status': 'pending',
            'reward': 0
        }
        
        # 检查是否达标
        if self.criteria.check(performance):
            submission['status'] = 'passed'
            submission['reward'] = self.reward.calculate(performance)
            self.status = BountyStatus.COMPLETED
        else:
            submission['status'] = 'failed'
        
        self.submissions.append(submission)
        return submission


class BountyMarket:
    """赏金市场 - 管理所有赏金任务"""
    
    def __init__(self, storage_path: str = './bounty_market.json'):
        self.storage_path = storage_path
        self.bounties: Dict[str, Bounty] = {}
        self.load()
    
    def load(self):
        """加载市场数据"""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                for bounty_data in data.get('bounties', []):
                    bounty = Bounty.from_dict(bounty_data)
                    self.bounties[bounty.id] = bounty
            print(f'[BountyMarket] 加载了 {len(self.bounties)} 个赏金任务')
        except FileNotFoundError:
            print('[BountyMarket] 新建市场')
    
    def save(self):
        """保存市场数据"""
        data = {
            'bounties': [b.to_dict() for b in self.bounties.values()],
            'updated_at': datetime.now().isoformat()
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_bounty(self, **kwargs) -> Bounty:
        """创建新赏金"""
        bounty = Bounty(**kwargs)
        self.bounties[bounty.id] = bounty
        self.save()
        print(f'[BountyMarket] 创建赏金: {bounty.id}')
        return bounty
    
    def get_open_bounties(self) -> List[Bounty]:
        """获取开放中的赏金"""
        return [b for b in self.bounties.values() if b.status == BountyStatus.OPEN]
    
    def get_bounty(self, bounty_id: str) -> Optional[Bounty]:
        """获取特定赏金"""
        return self.bounties.get(bounty_id)
    
    def claim_bounty(self, bounty_id: str, agent_id: str) -> bool:
        """认领赏金"""
        bounty = self.bounties.get(bounty_id)
        if bounty and bounty.claim(agent_id):
            self.save()
            print(f'[BountyMarket] {agent_id} 认领了 {bounty_id}')
            return True
        return False
    
    def submit_solution(self, bounty_id: str, gene_id: str, performance: Dict, agent_id: str) -> Dict:
        """提交解决方案"""
        bounty = self.bounties.get(bounty_id)
        if not bounty:
            return {'error': 'Bounty not found'}
        
        if bounty.claimed_by != agent_id:
            return {'error': 'Not claimed by this agent'}
        
        result = bounty.submit(gene_id, performance, agent_id)
        self.save()
        
        print(f'[BountyMarket] {agent_id} 提交了 {bounty_id} 的解决方案')
        print(f'[BountyMarket] 状态: {result["status"]}, 奖励: {result["reward"]}')
        
        return result


class BountyTemplates:
    """赏金模板"""
    
    @staticmethod
    def tsla_discovery(creator: str = "user") -> Bounty:
        """TSLA 策略发现赏金"""
        return Bounty(
            type=BountyType.STRATEGY_DISCOVERY,
            symbol="TSLA",
            timeframe="1d",
            market="US_EQUITY",
            data_range={
                'start': (datetime.now() - timedelta(days=365*2)).isoformat(),
                'end': datetime.now().isoformat()
            },
            criteria=ValidationCriteria(
                min_sharpe=1.5,
                min_win_rate=0.55,
                max_drawdown=0.15,
                min_trades=50,
                min_profit_factor=1.5
            ),
            reward=Reward(
                base=100.0,
                bonus=50.0,
                token="QUANT",
                tier_bonus={
                    'gold': 2.0,      # 夏普 > 2.0 → 200 QUANT
                    'silver': 1.5,    # 夏普 1.5-2.0 → 150 QUANT
                    'bronze': 1.0     # 夏普 1.0-1.5 → 100 QUANT
                }
            ),
            title="发现 TSLA 的有效交易策略",
            description="使用遗传编程发现能在 TSLA 上获得稳定收益的交易策略",
            tags=["TSLA", "momentum", "breakout", "high-volatility"],
            created_by=creator,
            priority="high",
            deadline=(datetime.now() + timedelta(days=7)).isoformat()
        )
    
    @staticmethod
    def portfolio_optimization(creator: str = "user", symbols: List[str] = None) -> Bounty:
        """组合优化赏金"""
        symbols = symbols or ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        return Bounty(
            type=BountyType.PORTFOLIO_CONSTRUCTION,
            symbol=",".join(symbols),
            timeframe="1d",
            market="US_EQUITY",
            criteria=ValidationCriteria(
                min_sharpe=1.2,
                max_drawdown=0.2,
                min_trades=100
            ),
            reward=Reward(base=200.0, token="QUANT"),
            title=f"构建 {len(symbols)} 只股票的最优组合策略",
            description=f"发现能在 {', '.join(symbols)} 上分散风险并获得稳定收益的组合策略",
            tags=["portfolio", "diversification", "multi-asset"],
            created_by=creator,
            priority="medium"
        )


# 示例用法
if __name__ == '__main__':
    print('Quant EvoMap Bounty System')
    print('=' * 60)
    
    # 创建市场
    market = BountyMarket()
    
    # 创建 TSLA 赏金
    tsla_bounty = market.create_bounty(
        **BountyTemplates.tsla_discovery().to_dict()
    )
    print(f'\n创建赏金: {tsla_bounty.id}')
    print(f'目标: {tsla_bounty.symbol}')
    print(f'奖励: {tsla_bounty.reward.base} {tsla_bounty.reward.token}')
    
    # Agent 认领
    agent_id = "miner_agent_001"
    if market.claim_bounty(tsla_bounty.id, agent_id):
        print(f'\n{agent_id} 认领成功')
    
    # 模拟提交
    performance = {
        'sharpe_ratio': 1.8,
        'win_rate': 0.62,
        'max_drawdown': 0.12,
        'trades': 80,
        'profit_factor': 2.1
    }
    
    result = market.submit_solution(
        tsla_bounty.id,
        gene_id="gene_abc123",
        performance=performance,
        agent_id=agent_id
    )
    
    print(f'\n提交结果:')
    print(f'状态: {result["status"]}')
    print(f'奖励: {result["reward"]} {tsla_bounty.reward.token}')
    
    # 查看开放赏金
    open_bounties = market.get_open_bounties()
    print(f'\n开放中的赏金: {len(open_bounties)} 个')
