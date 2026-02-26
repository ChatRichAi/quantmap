#!/usr/bin/env python3
"""
Quant EvoMap Prototype - 策略挖掘引擎
一步到位实现：数据获取、特征工程、遗传编程、回测验证
"""

import numpy as np
import pandas as pd
import yfinance as yf
from gplearn.genetic import SymbolicRegressor
from gplearn.functions import make_function
from sklearn.metrics import mean_squared_error
from datetime import datetime, timedelta
import json
import pickle
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class DataLoader:
    """数据加载器 - 获取股票历史数据"""
    
    def __init__(self, cache_dir: str = './data_cache'):
        self.cache_dir = cache_dir
        import os
        os.makedirs(cache_dir, exist_ok=True)
    
    def load(self, symbol: str, period: str = '2y', interval: str = '1d') -> pd.DataFrame:
        """加载股票数据"""
        cache_file = f'{self.cache_dir}/{symbol}_{period}_{interval}.pkl'
        
        try:
            # 尝试从缓存加载
            df = pd.read_pickle(cache_file)
            print(f'[DataLoader] 从缓存加载 {symbol} 数据: {len(df)} 条')
        except:
            # 从 Yahoo Finance 下载
            print(f'[DataLoader] 下载 {symbol} 数据...')
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            df.to_pickle(cache_file)
            print(f'[DataLoader] 下载完成: {len(df)} 条')
        
        return df


class FeatureEngineer:
    """特征工程 - 构建技术分析特征"""
    
    def __init__(self):
        self.feature_names = []
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """创建特征矩阵"""
        data = df.copy()
        
        # 基础价格特征
        data['Returns'] = data['Close'].pct_change()
        data['LogReturns'] = np.log(data['Close'] / data['Close'].shift(1))
        
        # 移动平均线
        for period in [5, 10, 20, 50]:
            data[f'SMA_{period}'] = data['Close'].rolling(period).mean()
            data[f'EMA_{period}'] = data['Close'].ewm(span=period).mean()
            data[f'Close_to_SMA_{period}'] = data['Close'] / data[f'SMA_{period}']
        
        # 波动率特征
        for period in [5, 10, 20]:
            data[f'Volatility_{period}'] = data['Returns'].rolling(period).std()
        
        # 成交量特征
        data['Volume_SMA_20'] = data['Volume'].rolling(20).mean()
        data['Volume_Ratio'] = data['Volume'] / data['Volume_SMA_20']
        
        # 价格位置特征
        data['High_Low_Range'] = (data['High'] - data['Low']) / data['Close']
        data['Open_Close_Range'] = abs(data['Close'] - data['Open']) / data['Close']
        
        # 动量特征
        for period in [5, 10, 20]:
            data[f'Momentum_{period}'] = data['Close'].pct_change(period)
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = data['Close'].ewm(span=12).mean()
        ema_26 = data['Close'].ewm(span=26).mean()
        data['MACD'] = ema_12 - ema_26
        data['MACD_Signal'] = data['MACD'].ewm(span=9).mean()
        
        # 目标变量: 未来5日收益率 (用于监督学习)
        data['Target_5d'] = data['Close'].shift(-5) / data['Close'] - 1
        
        # 目标变量: 未来5日方向 (分类问题)
        data['Target_Direction'] = (data['Target_5d'] > 0).astype(int)
        
        self.feature_names = [c for c in data.columns if c not in ['Target_5d', 'Target_Direction']]
        
        return data.dropna()


class StrategyGene:
    """策略基因 - 可进化的交易策略编码"""
    
    def __init__(self, expression=None, params=None):
        self.id = self._generate_id()
        self.expression = expression  # GP 树表达式
        self.params = params or {
            'entry_threshold': 0.5,
            'exit_threshold': 0.3,
            'position_size': 0.1,
            'stop_loss': 0.05
        }
        self.fitness = None
        self.performance = {}
        self.generation = 0
        self.lineage = {'parents': [], 'mutations': []}
    
    def _generate_id(self) -> str:
        import uuid
        return f'gene_{uuid.uuid4().hex[:8]}'
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'expression': str(self.expression) if self.expression else None,
            'params': self.params,
            'fitness': self.fitness,
            'performance': self.performance,
            'generation': self.generation,
            'lineage': self.lineage
        }
    
    def generate_signal(self, features: pd.DataFrame) -> pd.Series:
        """根据基因表达式生成交易信号"""
        if self.expression is None:
            return pd.Series(0, index=features.index)
        
        try:
            # 使用 GP 表达式计算信号
            signal = self.expression.execute(features)
            return pd.Series(signal, index=features.index)
        except:
            return pd.Series(0, index=features.index)


class BacktestEngine:
    """回测引擎 - 验证策略表现"""
    
    def __init__(self, initial_capital: float = 100000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
    
    def run(self, data: pd.DataFrame, signal: pd.Series, params: Dict) -> Dict:
        """运行回测"""
        df = data.copy()
        df['Signal'] = signal
        
        # 生成交易信号
        entry_threshold = params.get('entry_threshold', 0.5)
        df['Position'] = 0
        df.loc[df['Signal'] > entry_threshold, 'Position'] = 1
        df.loc[df['Signal'] < -entry_threshold, 'Position'] = -1
        
        # 持仓变化
        df['Position_Change'] = df['Position'].diff().abs()
        
        # 计算收益
        df['Strategy_Returns'] = df['Position'].shift(1) * df['Returns']
        df['Strategy_Returns'] -= df['Position_Change'] * self.commission
        
        # 计算累计收益
        df['Cumulative_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        df['Buy_Hold_Returns'] = (1 + df['Returns']).cumprod()
        
        # 计算指标
        total_return = df['Cumulative_Returns'].iloc[-1] - 1
        buy_hold_return = df['Buy_Hold_Returns'].iloc[-1] - 1
        
        returns = df['Strategy_Returns'].dropna()
        
        # 夏普比率 (年化)
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if returns.std() != 0 else 0
        
        # 最大回撤
        cumulative = df['Cumulative_Returns']
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 胜率
        winning_trades = (returns > 0).sum()
        total_trades = (returns != 0).sum()
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 交易次数
        trades = df['Position_Change'].sum() / 2
        
        return {
            'total_return': total_return,
            'buy_hold_return': buy_hold_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'trades': trades,
            'equity_curve': df['Cumulative_Returns'].tolist(),
            'df': df
        }


class GeneticMiner:
    """遗传挖掘引擎 - 使用遗传编程发现策略"""
    
    def __init__(self, population_size: int = 100, generations: int = 50):
        self.population_size = population_size
        self.generations = generations
        self.genes = []
        self.best_gene = None
    
    def _create_gp_estimator(self):
        """创建 GP 估计器"""
        # 定义自定义函数
        def rsi_signal(x):
            """RSI 信号"""
            return np.where(x < 30, 1, np.where(x > 70, -1, 0))
        
        def momentum_signal(x):
            """动量信号"""
            return np.sign(x)
        
        rsi_fn = make_function(function=rsi_signal, name='rsi_signal', arity=1)
        momentum_fn = make_function(function=momentum_signal, name='momentum_signal', arity=1)
        
        estimator = SymbolicRegressor(
            population_size=self.population_size,
            generations=self.generations,
            stopping_criteria=0.01,
            p_crossover=0.7,
            p_subtree_mutation=0.1,
            p_hoist_mutation=0.05,
            p_point_mutation=0.1,
            max_samples=0.9,
            verbose=1,
            parsimony_coefficient=0.01,
            random_state=42,
            function_set=('add', 'sub', 'mul', 'div', 'sqrt', 'log', 'abs', 'neg', 'inv'),
            metric='mse'
        )
        
        return estimator
    
    def mine(self, data: pd.DataFrame, feature_cols: List[str], target_col: str = 'Target_5d') -> StrategyGene:
        """挖掘策略"""
        print(f'[GeneticMiner] 开始挖掘策略...')
        print(f'[GeneticMiner] 数据量: {len(data)} 条')
        print(f'[GeneticMiner] 特征数: {len(feature_cols)} 个')
        
        # 准备数据
        X = data[feature_cols].values
        y = data[target_col].values
        
        # 划分训练集和测试集
        train_size = int(len(X) * 0.7)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        # 训练 GP
        gp = self._create_gp_estimator()
        gp.fit(X_train, y_train)
        
        # 创建策略基因
        gene = StrategyGene(expression=gp._program)
        gene.fitness = gp.score(X_test, y_test)
        
        # 在测试集上评估
        y_pred = gp.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        
        print(f'[GeneticMiner] 挖掘完成')
        print(f'[GeneticMiner] 基因 ID: {gene.id}')
        print(f'[GeneticMiner] 适应度: {gene.fitness:.4f}')
        print(f'[GeneticMiner] MSE: {mse:.6f}')
        
        self.best_gene = gene
        return gene


class QuantEvoMap:
    """Quant EvoMap 主控器"""
    
    def __init__(self):
        self.data_loader = DataLoader()
        self.feature_engineer = FeatureEngineer()
        self.genetic_miner = GeneticMiner()
        self.backtest_engine = BacktestEngine()
        self.gene_library = []
    
    def discover_strategy(self, symbol: str, save_results: bool = True) -> Dict:
        """发现策略 - 一站式流程"""
        print(f'\n{"="*60}')
        print(f'Quant EvoMap - 策略发现')
        print(f'目标: {symbol}')
        print(f'{"="*60}\n')
        
        # 1. 加载数据
        print('[Step 1/4] 加载数据...')
        raw_data = self.data_loader.load(symbol)
        
        # 2. 特征工程
        print('[Step 2/4] 特征工程...')
        feature_data = self.feature_engineer.create_features(raw_data)
        feature_cols = [c for c in feature_data.columns if c not in ['Target_5d', 'Target_Direction']]
        print(f'特征数: {len(feature_cols)}')
        
        # 3. 遗传挖掘
        print('[Step 3/4] 遗传挖掘...')
        gene = self.genetic_miner.mine(feature_data, feature_cols)
        
        # 4. 回测验证
        print('[Step 4/4] 回测验证...')
        signal = gene.generate_signal(feature_data[feature_cols])
        backtest_result = self.backtest_engine.run(feature_data, signal, gene.params)
        
        # 更新基因表现
        gene.performance = {
            'total_return': backtest_result['total_return'],
            'sharpe_ratio': backtest_result['sharpe_ratio'],
            'max_drawdown': backtest_result['max_drawdown'],
            'win_rate': backtest_result['win_rate'],
            'trades': backtest_result['trades']
        }
        
        # 保存到基因库
        self.gene_library.append(gene)
        
        # 打印结果
        print(f'\n{"="*60}')
        print('策略发现完成!')
        print(f'{"="*60}')
        print(f'基因 ID: {gene.id}')
        print(f'总收益率: {backtest_result["total_return"]:.2%}')
        print(f'买入持有: {backtest_result["buy_hold_return"]:.2%}')
        print(f'夏普比率: {backtest_result["sharpe_ratio"]:.2f}')
        print(f'最大回撤: {backtest_result["max_drawdown"]:.2%}')
        print(f'胜率: {backtest_result["win_rate"]:.2%}')
        print(f'交易次数: {backtest_result["trades"]:.0f}')
        print(f'{"="*60}\n')
        
        # 保存结果
        if save_results:
            self._save_results(gene, backtest_result, symbol)
        
        return {
            'gene': gene.to_dict(),
            'backtest': backtest_result,
            'symbol': symbol
        }
    
    def _save_results(self, gene: StrategyGene, backtest: Dict, symbol: str):
        """保存结果"""
        import os
        os.makedirs('./results', exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'./results/{symbol}_{gene.id}_{timestamp}.json'
        
        result = {
            'symbol': symbol,
            'timestamp': timestamp,
            'gene': gene.to_dict(),
            'backtest': {
                k: v for k, v in backtest.items() 
                if k not in ['df', 'equity_curve']
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f'[QuantEvoMap] 结果已保存: {filename}')


def main():
    """主函数"""
    print('\n' + '='*60)
    print('Quant EvoMap Prototype v0.1')
    print('遗传编程驱动的策略挖掘系统')
    print('='*60 + '\n')
    
    # 创建系统
    evomap = QuantEvoMap()
    
    # 发现 TSLA 策略
    result = evomap.discover_strategy('TSLA')
    
    # 发现 AAPL 策略
    result2 = evomap.discover_strategy('AAPL')
    
    print('\n' + '='*60)
    print('所有策略发现完成!')
    print(f'基因库中策略数: {len(evomap.gene_library)}')
    print('='*60 + '\n')


if __name__ == '__main__':
    main()
