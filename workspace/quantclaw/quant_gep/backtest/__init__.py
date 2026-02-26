"""
Quant-GEP Backtest - 标准化回测接口

统一多市场回测，标准化绩效计算
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional, Protocol, Tuple, Any
import statistics

from ..core.gene_ast import GeneExpression, MarketContext


class MarketType(Enum):
    """市场类型"""
    A_SHARE = "a_share"      # A股
    US_STOCK = "us_stock"    # 美股
    CRYPTO = "crypto"        # 加密货币
    FOREX = "forex"          # 外汇


class TimeFrame(Enum):
    """时间框架"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"


@dataclass
class MarketData:
    """市场数据结构"""
    symbol: str
    timeframe: TimeFrame
    timestamps: List[int]  # UTC毫秒时间戳
    opens: List[float]
    highs: List[float]
    lows: List[float]
    closes: List[float]
    volumes: List[float]
    
    def __len__(self) -> int:
        return len(self.timestamps)
    
    def get_context(self, index: int) -> MarketContext:
        """获取指定位置的MarketContext"""
        history = [
            {
                "open": self.opens[i],
                "high": self.highs[i],
                "low": self.lows[i],
                "close": self.closes[i],
                "volume": self.volumes[i]
            }
            for i in range(max(0, index - 50), index)
        ]
        
        return MarketContext(
            symbol=self.symbol,
            timestamp=self.timestamps[index],
            open=self.opens[index],
            high=self.highs[index],
            low=self.lows[index],
            close=self.closes[index],
            volume=self.volumes[index],
            history=history
        )
    
    def slice(self, start: int, end: int) -> MarketData:
        """切片"""
        return MarketData(
            symbol=self.symbol,
            timeframe=self.timeframe,
            timestamps=self.timestamps[start:end],
            opens=self.opens[start:end],
            highs=self.highs[start:end],
            lows=self.lows[start:end],
            closes=self.closes[start:end],
            volumes=self.volumes[start:end]
        )


@dataclass
class Trade:
    """交易记录"""
    entry_time: int
    exit_time: Optional[int] = None
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    size: float = 1.0
    side: str = "long"  # "long" or "short"
    pnl: float = 0.0
    pnl_pct: float = 0.0
    status: str = "open"  # "open", "closed"


@dataclass
class BacktestResult:
    """回测结果"""
    # 基本统计
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # 收益指标
    total_return: float = 0.0
    annual_return: float = 0.0
    
    # 风险指标
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    volatility: float = 0.0
    
    # 风险调整收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # 交易统计
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    
    # 时间统计
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    
    # 详细记录
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "annual_return": self.annual_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "profit_factor": self.profit_factor,
        }


class BacktestAdapter(ABC):
    """
    回测适配器基类
    
    统一多市场回测接口
    """
    
    def __init__(self, market_type: MarketType):
        self.market_type = market_type
    
    @abstractmethod
    def get_data(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000
    ) -> MarketData:
        """获取市场数据"""
        pass
    
    @abstractmethod
    def run(
        self,
        gene: GeneExpression,
        data: MarketData,
        initial_capital: float = 10000.0,
        position_size: float = 1.0
    ) -> BacktestResult:
        """
        执行回测
        
        Args:
            gene: 策略基因
            data: 市场数据
            initial_capital: 初始资金
            position_size: 仓位大小
        """
        pass


class SimpleBacktestEngine(BacktestAdapter):
    """
    简单回测引擎
    
    基于信号的回测，gene产生买卖信号
    """
    
    def __init__(self):
        super().__init__(MarketType.CRYPTO)
        self.data_cache: Dict[str, MarketData] = {}
    
    def get_data(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000
    ) -> MarketData:
        """获取数据 (子类应重写此方法连接真实数据源)"""
        # 返回模拟数据作为示例
        return self._generate_mock_data(symbol, timeframe, limit)
    
    def _generate_mock_data(self, symbol: str, timeframe: TimeFrame, limit: int) -> MarketData:
        """生成模拟数据用于测试"""
        import random
        
        base_price = 100.0
        timestamps = []
        opens, highs, lows, closes, volumes = [], [], [], [], []
        
        now = int(datetime.now().timestamp() * 1000)
        
        for i in range(limit):
            timestamps.append(now - (limit - i) * 3600000)  # 每小时
            
            change = random.gauss(0, 0.02)
            close = base_price * (1 + change)
            open_price = base_price
            high = max(open_price, close) * (1 + abs(random.gauss(0, 0.01)))
            low = min(open_price, close) * (1 - abs(random.gauss(0, 0.01)))
            volume = random.uniform(1000, 10000)
            
            opens.append(open_price)
            highs.append(high)
            lows.append(low)
            closes.append(close)
            volumes.append(volume)
            
            base_price = close
        
        return MarketData(
            symbol=symbol,
            timeframe=timeframe,
            timestamps=timestamps,
            opens=opens,
            highs=highs,
            lows=lows,
            closes=closes,
            volumes=volumes
        )
    
    def run(
        self,
        gene: GeneExpression,
        data: MarketData,
        initial_capital: float = 10000.0,
        position_size: float = 1.0
    ) -> BacktestResult:
        """执行回测"""
        result = BacktestResult()
        result.start_time = data.timestamps[0]
        result.end_time = data.timestamps[-1]
        
        equity = initial_capital
        result.equity_curve.append(equity)
        
        current_trade: Optional[Trade] = None
        
        # 预留足够的历史数据用于指标计算
        start_idx = 50
        
        for i in range(start_idx, len(data)):
            context = data.get_context(i)
            
            try:
                signal = gene.evaluate(context)
            except Exception:
                signal = False
            
            # 交易逻辑
            if signal and current_trade is None:
                # 买入信号
                current_trade = Trade(
                    entry_time=data.timestamps[i],
                    entry_price=data.closes[i],
                    size=position_size,
                    side="long"
                )
            
            elif not signal and current_trade is not None:
                # 卖出信号
                current_trade.exit_time = data.timestamps[i]
                current_trade.exit_price = data.closes[i]
                current_trade.status = "closed"
                
                # 计算盈亏
                pnl = (current_trade.exit_price - current_trade.entry_price) * current_trade.size
                current_trade.pnl = pnl
                current_trade.pnl_pct = pnl / current_trade.entry_price
                
                equity += pnl
                result.trades.append(current_trade)
                current_trade = None
            
            result.equity_curve.append(equity)
        
        # 关闭未平仓的交易
        if current_trade is not None:
            current_trade.exit_time = data.timestamps[-1]
            current_trade.exit_price = data.closes[-1]
            current_trade.status = "closed"
            pnl = (current_trade.exit_price - current_trade.entry_price) * current_trade.size
            current_trade.pnl = pnl
            current_trade.pnl_pct = pnl / current_trade.entry_price
            result.trades.append(current_trade)
        
        # 计算绩效指标
        self._calculate_metrics(result, initial_capital)
        
        return result
    
    def _calculate_metrics(self, result: BacktestResult, initial_capital: float) -> None:
        """计算绩效指标"""
        trades = result.trades
        
        if not trades:
            return
        
        # 基本统计
        result.total_trades = len(trades)
        result.winning_trades = sum(1 for t in trades if t.pnl > 0)
        result.losing_trades = sum(1 for t in trades if t.pnl <= 0)
        result.win_rate = result.winning_trades / result.total_trades if result.total_trades > 0 else 0
        
        # 收益
        total_pnl = sum(t.pnl for t in trades)
        result.total_return = total_pnl / initial_capital
        
        # 年化收益 (简化计算)
        days = (result.end_time - result.start_time) / (1000 * 86400) if result.end_time and result.start_time else 365
        if days > 0:
            result.annual_return = (1 + result.total_return) ** (365 / days) - 1
        
        # 最大回撤
        peak = initial_capital
        max_dd = 0
        dd_duration = 0
        max_dd_duration = 0
        
        for equity in result.equity_curve:
            if equity > peak:
                peak = equity
                dd_duration = 0
            else:
                dd = (peak - equity) / peak
                if dd > max_dd:
                    max_dd = dd
                dd_duration += 1
                max_dd_duration = max(max_dd_duration, dd_duration)
        
        result.max_drawdown = max_dd
        result.max_drawdown_duration = max_dd_duration
        
        # 平均盈亏
        wins = [t.pnl for t in trades if t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl <= 0]
        
        result.avg_win = statistics.mean(wins) if wins else 0
        result.avg_loss = statistics.mean(losses) if losses else 0
        
        # 盈亏比
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 1
        result.profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # 夏普比率 (简化)
        if len(result.equity_curve) > 1:
            returns = [(result.equity_curve[i] - result.equity_curve[i-1]) / result.equity_curve[i-1] 
                      for i in range(1, len(result.equity_curve))]
            if returns:
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns) if len(returns) > 1 else 0.01
                result.sharpe_ratio = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
        
        # Calmar比率
        result.calmar_ratio = result.annual_return / result.max_drawdown if result.max_drawdown > 0 else 0


class AShareAdapter(SimpleBacktestEngine):
    """A股回测适配器"""
    
    def __init__(self):
        super().__init__()
        self.market_type = MarketType.A_SHARE
    
    def get_data(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000
    ) -> MarketData:
        """
        从akshare获取A股数据
        
        TODO: 集成akshare
        """
        # 返回模拟数据
        return self._generate_mock_data(symbol, timeframe, limit)


class USStockAdapter(SimpleBacktestEngine):
    """美股回测适配器"""
    
    def __init__(self):
        super().__init__()
        self.market_type = MarketType.US_STOCK
    
    def get_data(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000
    ) -> MarketData:
        """
        从yfinance获取美股数据
        
        TODO: 集成yfinance
        """
        return self._generate_mock_data(symbol, timeframe, limit)


class CryptoAdapter(SimpleBacktestEngine):
    """加密货币回测适配器"""
    
    def __init__(self):
        super().__init__()
        self.market_type = MarketType.CRYPTO
    
    def get_data(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000
    ) -> MarketData:
        """
        从OKX获取加密货币数据
        
        TODO: 集成OKX API
        """
        return self._generate_mock_data(symbol, timeframe, limit)


# 便捷函数
def create_adapter(market_type: MarketType) -> BacktestAdapter:
    """根据市场类型创建适配器"""
    adapters = {
        MarketType.A_SHARE: AShareAdapter,
        MarketType.US_STOCK: USStockAdapter,
        MarketType.CRYPTO: CryptoAdapter,
    }
    
    adapter_class = adapters.get(market_type, SimpleBacktestEngine)
    return adapter_class()


def quick_backtest(
    gene: GeneExpression,
    symbol: str = "BTC-USDT",
    market_type: MarketType = MarketType.CRYPTO,
    timeframe: TimeFrame = TimeFrame.H1
) -> BacktestResult:
    """快速回测"""
    adapter = create_adapter(market_type)
    data = adapter.get_data(symbol, timeframe, limit=500)
    return adapter.run(gene, data)
