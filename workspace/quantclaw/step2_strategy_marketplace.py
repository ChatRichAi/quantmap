"""
QuantClaw Community Edition - Step 2: 策略市场 (Strategy Marketplace)
买卖验证过的策略的完整交易系统
"""

import asyncio
import json
import hashlib
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random


class OrderType(Enum):
    """订单类型"""
    BUY = "buy"       # 买入策略
    SELL = "sell"     # 卖出策略


class OrderStatus(Enum):
    """订单状态"""
    OPEN = "open"           # 开放中
    MATCHED = "matched"     # 已匹配
    EXECUTED = "executed"   # 已执行
    CANCELLED = "cancelled" # 已取消
    EXPIRED = "expired"     # 已过期


class StrategyStatus(Enum):
    """策略上架状态"""
    PENDING = "pending"     # 待审核
    LISTED = "listed"       # 已上架
    DELISTED = "delisted"   # 已下架
    SOLD = "sold"           # 已售出


@dataclass
class StrategyListing:
    """
    策略上架信息
    
    卖家将自己的验证策略上架到市场
    """
    listing_id: str
    seller_id: str
    
    # 策略信息 (引用 evolution_ecosystem 中的 Bundle)
    bundle_id: str
    gene_id: str
    capsule_id: str
    
    # 策略描述
    title: str
    description: str
    strategy_type: str  # "mean_reversion", "momentum", "arbitrage", etc.
    
    # 性能指标 (决定价格的重要参考)
    sharpe_ratio: float
    max_drawdown: float
    annual_return: float
    win_rate: float
    backtest_period: str
    
    # 验证信息
    validation_count: int       # 被验证的次数
    validator_scores: List[float]  # 各验证者的评分
    
    # 定价
    price: float                # 价格 ( credits )
    price_model: str            # "fixed", "auction", "performance_based"
    
    # 销售条款
    license_type: str           # "one_time", "subscription", "royalty"
    royalty_rate: float = 0.0   # 版税率 (如果 license_type == "royalty")
    
    # 状态
    status: StrategyStatus = StrategyStatus.PENDING
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    listed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # 销售统计
    views: int = 0
    inquiries: int = 0
    sales_count: int = 0
    total_revenue: float = 0.0
    
    def compute_score(self) -> float:
        """计算策略评分 (用于排序和推荐)"""
        # 夏普比率权重 40%
        sharpe_score = min(self.sharpe_ratio / 3.0, 1.0) * 40
        
        # 收益权重 30%
        return_score = min(self.annual_return / 0.5, 1.0) * 30
        
        # 回撤惩罚 20%
        drawdown_score = max(0, 1 - self.max_drawdown / 0.3) * 20
        
        # 验证次数权重 10%
        validation_score = min(self.validation_count / 5, 1.0) * 10
        
        return sharpe_score + return_score + drawdown_score + validation_score
    
    def to_dict(self) -> Dict:
        return {
            "listing_id": self.listing_id,
            "seller_id": self.seller_id,
            "bundle_id": self.bundle_id,
            "title": self.title,
            "description": self.description,
            "strategy_type": self.strategy_type,
            "performance": {
                "sharpe_ratio": self.sharpe_ratio,
                "max_drawdown": self.max_drawdown,
                "annual_return": self.annual_return,
                "win_rate": self.win_rate
            },
            "price": self.price,
            "license_type": self.license_type,
            "score": self.compute_score(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class Order:
    """
    买卖订单
    """
    order_id: str
    order_type: OrderType
    
    # 交易者
    trader_id: str
    
    # 价格条件
    price: float                    # 期望价格
    
    # 标的
    listing_id: Optional[str] = None  # 指定策略 (市价单可为空)
    strategy_type: Optional[str] = None  # 策略类型筛选
    
    price_tolerance: float = 0.1    # 价格容忍度 (±10%)
    
    # 数量
    quantity: int = 1               # 购买数量 (通常策略是1份)
    
    # 性能要求 (买家可以设置筛选条件)
    min_sharpe: Optional[float] = None
    max_drawdown: Optional[float] = None
    min_validation_count: int = 1
    
    # 状态
    status: OrderStatus = OrderStatus.OPEN
    
    # 匹配信息
    matched_with: Optional[str] = None  # 匹配的订单ID
    matched_price: Optional[float] = None
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    
    def is_match(self, listing: StrategyListing) -> bool:
        """检查是否与上架策略匹配"""
        # 价格检查
        if abs(listing.price - self.price) > self.price * self.price_tolerance:
            return False
        
        # 策略类型检查
        if self.strategy_type and listing.strategy_type != self.strategy_type:
            return False
        
        # 性能指标检查
        if self.min_sharpe and listing.sharpe_ratio < self.min_sharpe:
            return False
        
        if self.max_drawdown and listing.max_drawdown > self.max_drawdown:
            return False
        
        if listing.validation_count < self.min_validation_count:
            return False
        
        return True


@dataclass
class Transaction:
    """
    交易记录
    """
    tx_id: str
    
    # 参与方
    buyer_id: str
    seller_id: str
    listing_id: str
    
    # 交易内容
    bundle_id: str          # 转移的策略Bundle
    
    # 金额
    price: float            # 成交价
    platform_fee: float     # 平台费用 (2%)
    seller_revenue: float   # 卖家实得
    
    # 许可
    license_type: str
    royalty_rate: float
    
    # 状态
    status: str = "completed"  # pending/completed/disputed/refunded
    
    # 时间
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # 评价
    buyer_rating: Optional[int] = None
    seller_rating: Optional[int] = None
    review_text: Optional[str] = None


@dataclass
class Portfolio:
    """
    用户的策略投资组合
    """
    user_id: str
    
    # 持有的策略
    holdings: Dict[str, Dict] = field(default_factory=dict)
    # {
    #   "bundle_id": {
    #       "listing_id": "...",
    #       "purchase_price": 100.0,
    #       "purchased_at": "...",
    #       "license_type": "...",
    #       "usage_count": 0,
    #       "profit_generated": 0.0
    #   }
    # }
    
    # 组合表现
    total_invested: float = 0.0
    total_value: float = 0.0
    unrealized_pnl: float = 0.0
    
    def add_strategy(self, tx: Transaction):
        """添加策略到组合"""
        self.holdings[tx.bundle_id] = {
            "listing_id": tx.listing_id,
            "purchase_price": tx.price,
            "purchased_at": tx.created_at.isoformat(),
            "license_type": tx.license_type,
            "royalty_rate": tx.royalty_rate,
            "usage_count": 0,
            "profit_generated": 0.0,
            "royalty_paid": 0.0
        }
        self.total_invested += tx.price
    
    def record_usage(self, bundle_id: str, profit: float):
        """记录策略使用情况和收益"""
        if bundle_id in self.holdings:
            self.holdings[bundle_id]["usage_count"] += 1
            self.holdings[bundle_id]["profit_generated"] += profit
            
            # 计算版税
            if self.holdings[bundle_id]["license_type"] == "royalty":
                royalty = profit * self.holdings[bundle_id]["royalty_rate"]
                self.holdings[bundle_id]["royalty_paid"] += royalty
                return royalty
        
        return 0.0


class StrategyMarketplace:
    """
    策略市场主控制器
    
    功能:
    1. 策略上架审核
    2. 订单匹配引擎
    3. 交易执行
    4. 投资组合管理
    5. 评价系统
    """
    
    def __init__(self, db_path: str = "strategy_marketplace.db"):
        self.db_path = db_path
        self.platform_fee_rate = 0.02  # 2%平台费
        
        # 内存缓存
        self.listings: Dict[str, StrategyListing] = {}
        self.orders: Dict[str, Order] = {}
        self.portfolios: Dict[str, Portfolio] = {}
        
        self._init_database()
        self._load_from_db()
    
    def _init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 上架表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listings (
                listing_id TEXT PRIMARY KEY,
                seller_id TEXT,
                bundle_id TEXT,
                gene_id TEXT,
                capsule_id TEXT,
                title TEXT,
                description TEXT,
                strategy_type TEXT,
                sharpe_ratio REAL,
                max_drawdown REAL,
                annual_return REAL,
                win_rate REAL,
                backtest_period TEXT,
                validation_count INTEGER,
                validator_scores TEXT,
                price REAL,
                price_model TEXT,
                license_type TEXT,
                royalty_rate REAL,
                status TEXT,
                created_at TEXT,
                listed_at TEXT,
                expires_at TEXT,
                views INTEGER,
                inquiries INTEGER,
                sales_count INTEGER,
                total_revenue REAL
            )
        ''')
        
        # 订单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                order_type TEXT,
                trader_id TEXT,
                listing_id TEXT,
                strategy_type TEXT,
                price REAL,
                price_tolerance REAL,
                quantity INTEGER,
                min_sharpe REAL,
                max_drawdown REAL,
                min_validation_count INTEGER,
                status TEXT,
                matched_with TEXT,
                matched_price REAL,
                created_at TEXT,
                expires_at TEXT,
                executed_at TEXT
            )
        ''')
        
        # 交易表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                tx_id TEXT PRIMARY KEY,
                buyer_id TEXT,
                seller_id TEXT,
                listing_id TEXT,
                bundle_id TEXT,
                price REAL,
                platform_fee REAL,
                seller_revenue REAL,
                license_type TEXT,
                royalty_rate REAL,
                status TEXT,
                created_at TEXT,
                completed_at TEXT,
                buyer_rating INTEGER,
                seller_rating INTEGER,
                review_text TEXT
            )
        ''')
        
        # 投资组合表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolios (
                user_id TEXT PRIMARY KEY,
                holdings TEXT,
                total_invested REAL,
                total_value REAL,
                unrealized_pnl REAL,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _load_from_db(self):
        """从数据库加载数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 加载上架数据
        cursor.execute('SELECT * FROM listings WHERE status = ?', (StrategyStatus.LISTED.value,))
        for row in cursor.fetchall():
            listing = self._row_to_listing(row)
            self.listings[listing.listing_id] = listing
        
        # 加载开放订单
        cursor.execute('SELECT * FROM orders WHERE status = ?', (OrderStatus.OPEN.value,))
        for row in cursor.fetchall():
            order = self._row_to_order(row)
            self.orders[order.order_id] = order
        
        conn.close()
    
    # ==================== 上架管理 ====================
    
    def list_strategy(self, listing: StrategyListing) -> str:
        """
        上架策略
        
        流程:
        1. 验证策略Bundle
        2. 审核性能指标
        3. 生成listing_id
        4. 保存到数据库
        """
        # 生成listing_id
        listing.listing_id = f"LIST_{int(datetime.now().timestamp())}_{random.randint(1000,9999)}"
        
        # 自动审核 (简化版)
        if self._auto_audit(listing):
            listing.status = StrategyStatus.LISTED
            listing.listed_at = datetime.now()
            listing.expires_at = datetime.now() + timedelta(days=30)
        
        # 保存
        self.listings[listing.listing_id] = listing
        self._save_listing(listing)
        
        # 尝试匹配现有买单
        asyncio.create_task(self._try_match_buy_orders(listing))
        
        print(f"✅ Strategy listed: {listing.title} @ {listing.price} credits")
        print(f"   Score: {listing.compute_score():.1f}/100")
        
        return listing.listing_id
    
    def _auto_audit(self, listing: StrategyListing) -> bool:
        """自动审核策略"""
        # 检查最低要求
        if listing.sharpe_ratio < 0.5:
            print(f"❌ Audit failed: Sharpe ratio too low ({listing.sharpe_ratio})")
            return False
        
        if listing.max_drawdown > 0.5:
            print(f"❌ Audit failed: Drawdown too high ({listing.max_drawdown})")
            return False
        
        if listing.validation_count < 2:
            print(f"❌ Audit failed: Insufficient validation ({listing.validation_count})")
            return False
        
        return True
    
    def delist_strategy(self, listing_id: str, seller_id: str) -> bool:
        """下架策略"""
        if listing_id not in self.listings:
            return False
        
        listing = self.listings[listing_id]
        if listing.seller_id != seller_id:
            return False
        
        listing.status = StrategyStatus.DELISTED
        self._save_listing(listing)
        del self.listings[listing_id]
        
        return True
    
    # ==================== 订单管理 ====================
    
    def place_order(self, order: Order) -> str:
        """
        提交订单
        
        如果是买单，立即尝试匹配
        """
        order.order_id = f"ORDER_{int(datetime.now().timestamp())}_{random.randint(1000,9999)}"
        order.expires_at = datetime.now() + timedelta(hours=24)
        
        self.orders[order.order_id] = order
        self._save_order(order)
        
        print(f"📊 Order placed: {order.order_type.value} @ {order.price} credits")
        
        # 买单立即尝试匹配
        if order.order_type == OrderType.BUY:
            asyncio.create_task(self._match_order(order))
        
        return order.order_id
    
    def cancel_order(self, order_id: str, trader_id: str) -> bool:
        """取消订单"""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        if order.trader_id != trader_id:
            return False
        
        if order.status != OrderStatus.OPEN:
            return False
        
        order.status = OrderStatus.CANCELLED
        self._save_order(order)
        del self.orders[order_id]
        
        return True
    
    async def _match_order(self, order: Order):
        """匹配订单"""
        if order.order_type != OrderType.BUY:
            return
        
        # 查找匹配的上架策略
        matches = []
        for listing in self.listings.values():
            if listing.status == StrategyStatus.LISTED and order.is_match(listing):
                matches.append(listing)
        
        # 按评分排序
        matches.sort(key=lambda x: -x.compute_score())
        
        # 选择最佳匹配
        if matches:
            best_match = matches[0]
            await self._execute_trade(order, best_match)
    
    async def _try_match_buy_orders(self, listing: StrategyListing):
        """尝试匹配现有买单"""
        for order in self.orders.values():
            if (order.order_type == OrderType.BUY and 
                order.status == OrderStatus.OPEN and
                order.is_match(listing)):
                
                await self._execute_trade(order, listing)
                break  # 一个策略只匹配一个买单
    
    async def _execute_trade(self, buy_order: Order, listing: StrategyListing):
        """执行交易"""
        # 创建交易记录
        tx = Transaction(
            tx_id=f"TX_{int(datetime.now().timestamp())}",
            buyer_id=buy_order.trader_id,
            seller_id=listing.seller_id,
            listing_id=listing.listing_id,
            bundle_id=listing.bundle_id,
            price=listing.price,
            platform_fee=listing.price * self.platform_fee_rate,
            seller_revenue=listing.price * (1 - self.platform_fee_rate),
            license_type=listing.license_type,
            royalty_rate=listing.royalty_rate
        )
        
        tx.completed_at = datetime.now()
        
        # 更新订单状态
        buy_order.status = OrderStatus.EXECUTED
        buy_order.matched_with = listing.listing_id
        buy_order.matched_price = listing.price
        buy_order.executed_at = datetime.now()
        
        # 更新上架状态
        listing.status = StrategyStatus.SOLD
        listing.sales_count += 1
        listing.total_revenue += tx.seller_revenue
        
        # 更新买家投资组合
        if buy_order.trader_id not in self.portfolios:
            self.portfolios[buy_order.trader_id] = Portfolio(user_id=buy_order.trader_id)
        
        self.portfolios[buy_order.trader_id].add_strategy(tx)
        
        # 保存所有更改
        self._save_transaction(tx)
        self._save_order(buy_order)
        self._save_listing(listing)
        self._save_portfolio(self.portfolios[buy_order.trader_id])
        
        print(f"💰 Trade executed: {tx.tx_id}")
        print(f"   Buyer: {tx.buyer_id}")
        print(f"   Seller: {tx.seller_id}")
        print(f"   Price: {tx.price} credits")
        print(f"   Platform fee: {tx.platform_fee} credits")
        print(f"   Seller gets: {tx.seller_revenue} credits")
    
    # ==================== 查询功能 ====================
    
    def search_strategies(self, 
                         strategy_type: Optional[str] = None,
                         min_sharpe: Optional[float] = None,
                         max_price: Optional[float] = None,
                         sort_by: str = "score") -> List[StrategyListing]:
        """搜索策略"""
        results = []
        
        for listing in self.listings.values():
            if listing.status != StrategyStatus.LISTED:
                continue
            
            if strategy_type and listing.strategy_type != strategy_type:
                continue
            
            if min_sharpe and listing.sharpe_ratio < min_sharpe:
                continue
            
            if max_price and listing.price > max_price:
                continue
            
            results.append(listing)
        
        # 排序
        if sort_by == "score":
            results.sort(key=lambda x: -x.compute_score())
        elif sort_by == "price":
            results.sort(key=lambda x: x.price)
        elif sort_by == "sharpe":
            results.sort(key=lambda x: -x.sharpe_ratio)
        
        return results
    
    def get_recommendations(self, user_id: str, n: int = 5) -> List[StrategyListing]:
        """为用户推荐策略"""
        # 获取用户现有组合
        portfolio = self.portfolios.get(user_id)
        
        # 简单推荐：高分且不同类型的策略
        candidates = []
        owned_types = set()
        
        if portfolio:
            for bundle_id, holding in portfolio.holdings.items():
                # 这里应该从bundle获取策略类型
                pass
        
        for listing in self.listings.values():
            if listing.status == StrategyStatus.LISTED:
                if listing.strategy_type not in owned_types:
                    candidates.append(listing)
        
        candidates.sort(key=lambda x: -x.compute_score())
        
        return candidates[:n]
    
    def get_portfolio(self, user_id: str) -> Optional[Portfolio]:
        """获取用户投资组合"""
        return self.portfolios.get(user_id)
    
    def get_market_stats(self) -> Dict:
        """获取市场统计"""
        total_listings = len([l for l in self.listings.values() if l.status == StrategyStatus.LISTED])
        total_orders = len([o for o in self.orders.values() if o.status == OrderStatus.OPEN])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*), SUM(price) FROM transactions WHERE status = ?', ("completed",))
        result = cursor.fetchone()
        total_transactions = result[0] or 0
        total_volume = result[1] or 0
        
        conn.close()
        
        return {
            "active_listings": total_listings,
            "open_orders": total_orders,
            "total_transactions": total_transactions,
            "total_volume": total_volume,
            "average_price": total_volume / total_transactions if total_transactions > 0 else 0
        }
    
    # ==================== 数据库操作 ====================
    
    def _save_listing(self, listing: StrategyListing):
        """保存上架信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO listings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            listing.listing_id, listing.seller_id, listing.bundle_id, listing.gene_id, listing.capsule_id,
            listing.title, listing.description, listing.strategy_type,
            listing.sharpe_ratio, listing.max_drawdown, listing.annual_return, listing.win_rate, listing.backtest_period,
            listing.validation_count, json.dumps(listing.validator_scores),
            listing.price, listing.price_model, listing.license_type, listing.royalty_rate,
            listing.status.value, listing.created_at.isoformat(),
            listing.listed_at.isoformat() if listing.listed_at else None,
            listing.expires_at.isoformat() if listing.expires_at else None,
            listing.views, listing.inquiries, listing.sales_count, listing.total_revenue
        ))
        
        conn.commit()
        conn.close()
    
    def _save_order(self, order: Order):
        """保存订单"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order.order_id, order.order_type.value, order.trader_id, order.listing_id, order.strategy_type,
            order.price, order.price_tolerance, order.quantity,
            order.min_sharpe, order.max_drawdown, order.min_validation_count,
            order.status.value, order.matched_with, order.matched_price,
            order.created_at.isoformat(),
            order.expires_at.isoformat() if order.expires_at else None,
            order.executed_at.isoformat() if order.executed_at else None
        ))
        
        conn.commit()
        conn.close()
    
    def _save_transaction(self, tx: Transaction):
        """保存交易"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tx.tx_id, tx.buyer_id, tx.seller_id, tx.listing_id, tx.bundle_id,
            tx.price, tx.platform_fee, tx.seller_revenue, tx.license_type, tx.royalty_rate,
            tx.status, tx.created_at.isoformat(),
            tx.completed_at.isoformat() if tx.completed_at else None,
            tx.buyer_rating, tx.seller_rating, tx.review_text
        ))
        
        conn.commit()
        conn.close()
    
    def _save_portfolio(self, portfolio: Portfolio):
        """保存投资组合"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO portfolios VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            portfolio.user_id, json.dumps(portfolio.holdings),
            portfolio.total_invested, portfolio.total_value, portfolio.unrealized_pnl,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def _row_to_listing(self, row) -> StrategyListing:
        """数据库行转对象"""
        return StrategyListing(
            listing_id=row[0],
            seller_id=row[1],
            bundle_id=row[2],
            gene_id=row[3],
            capsule_id=row[4],
            title=row[5],
            description=row[6],
            strategy_type=row[7],
            sharpe_ratio=row[8],
            max_drawdown=row[9],
            annual_return=row[10],
            win_rate=row[11],
            backtest_period=row[12],
            validation_count=row[13],
            validator_scores=json.loads(row[14]) if row[14] else [],
            price=row[15],
            price_model=row[16],
            license_type=row[17],
            royalty_rate=row[18],
            status=StrategyStatus(row[19]),
            created_at=datetime.fromisoformat(row[20]),
            listed_at=datetime.fromisoformat(row[21]) if row[21] else None,
            expires_at=datetime.fromisoformat(row[22]) if row[22] else None,
            views=row[23],
            inquiries=row[24],
            sales_count=row[25],
            total_revenue=row[26]
        )
    
    def _row_to_order(self, row) -> Order:
        """数据库行转对象"""
        return Order(
            order_id=row[0],
            order_type=OrderType(row[1]),
            trader_id=row[2],
            listing_id=row[3],
            strategy_type=row[4],
            price=row[5],
            price_tolerance=row[6],
            quantity=row[7],
            min_sharpe=row[8],
            max_drawdown=row[9],
            min_validation_count=row[10],
            status=OrderStatus(row[11]),
            matched_with=row[12],
            matched_price=row[13],
            created_at=datetime.fromisoformat(row[14]),
            expires_at=datetime.fromisoformat(row[15]) if row[15] else None,
            executed_at=datetime.fromisoformat(row[16]) if row[16] else None
        )


# ==================== 演示 ====================

def demo_marketplace():
    """演示策略市场"""
    print("="*80)
    print("QuantClaw Strategy Marketplace Demo")
    print("="*80)
    
    # 创建市场
    market = StrategyMarketplace(db_path="demo_market.db")
    
    # 1. 卖家上架策略
    print("\n[Step 1] Seller listing strategies...")
    
    strategy1 = StrategyListing(
        listing_id="",
        seller_id="seller_alice",
        bundle_id="bundle_001",
        gene_id="gene_rsi_mr",
        capsule_id="capsule_001",
        title="RSI Mean Reversion Pro",
        description="High-performance RSI mean reversion strategy with dynamic thresholds",
        strategy_type="mean_reversion",
        sharpe_ratio=1.8,
        max_drawdown=0.15,
        annual_return=0.25,
        win_rate=0.62,
        backtest_period="2020-2024",
        validation_count=5,
        validator_scores=[0.85, 0.88, 0.82, 0.90, 0.87],
        price=500.0,
        price_model="fixed",
        license_type="one_time"
    )
    
    listing_id1 = market.list_strategy(strategy1)
    
    strategy2 = StrategyListing(
        listing_id="",
        seller_id="seller_bob",
        bundle_id="bundle_002",
        gene_id="gene_momentum",
        capsule_id="capsule_002",
        title="Momentum Breakout Elite",
        description="Trend following strategy with volume confirmation",
        strategy_type="momentum",
        sharpe_ratio=1.5,
        max_drawdown=0.20,
        annual_return=0.30,
        win_rate=0.58,
        backtest_period="2019-2024",
        validation_count=4,
        validator_scores=[0.80, 0.85, 0.82, 0.83],
        price=800.0,
        price_model="fixed",
        license_type="royalty",
        royalty_rate=0.05  # 5%版税
    )
    
    listing_id2 = market.list_strategy(strategy2)
    
    # 2. 买家搜索策略
    print("\n[Step 2] Buyer searching strategies...")
    results = market.search_strategies(min_sharpe=1.5, sort_by="score")
    
    print(f"   Found {len(results)} strategies:")
    for r in results:
        print(f"   - {r.title} (Score: {r.compute_score():.1f}, Price: {r.price} credits)")
    
    # 3. 买家提交买单
    print("\n[Step 3] Buyer placing orders...")
    
    buy_order = Order(
        order_id="",
        order_type=OrderType.BUY,
        trader_id="buyer_charlie",
        strategy_type="mean_reversion",
        price=550.0,
        price_tolerance=0.2,
        min_sharpe=1.5,
        min_validation_count=3
    )
    
    order_id = market.place_order(buy_order)
    
    # 4. 查看市场统计
    print("\n[Step 4] Market statistics:")
    stats = market.get_market_stats()
    print(f"   Active listings: {stats['active_listings']}")
    print(f"   Open orders: {stats['open_orders']}")
    print(f"   Total transactions: {stats['total_transactions']}")
    print(f"   Total volume: {stats['total_volume']} credits")
    
    # 5. 查看投资组合
    print("\n[Step 5] Buyer's portfolio:")
    portfolio = market.get_portfolio("buyer_charlie")
    if portfolio:
        print(f"   Total invested: {portfolio.total_invested} credits")
        print(f"   Holdings: {len(portfolio.holdings)} strategies")
    
    print("\n" + "="*80)
    print("Marketplace Demo Complete!")
    print("="*80)
    
    return market


if __name__ == "__main__":
    market = demo_marketplace()
