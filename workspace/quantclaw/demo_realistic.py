"""
QuantClaw Pro - 真实股票数据演示
使用具有代表性的真实股票特征模式
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 导入系统模块
import sys
sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from perception_layer import PerceptionLayer
from cognition_layer import CognitionLayer, PersonalityClassifier
from decision_layer import DecisionLayer, MarketRegime
from quantclaw_pro import QuantClawPro


def create_realistic_stock_data(ticker: str, pattern: str, days: int = 100) -> pd.DataFrame:
    """
    创建具有真实特征模式的股票数据
    
    Args:
        ticker: 股票代码
        pattern: 价格模式类型
            - 'stable_growth': 稳健增长 (INTJ/ENTJ)
            - 'high_volatility': 高波动 (ESTP/ESFP)
            - 'value_stable': 价值稳定 (ISTJ/ISFJ)
            - 'mean_reverting': 均值回归 (ISFP/ISTP)
            - 'trending': 强趋势 (INTJ/ENFP)
            - 'contrarian': 逆向波动 (INFJ)
        days: 数据天数
    """
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    if pattern == 'stable_growth':
        # INTJ/ENTJ 模式: 稳健上升趋势，低波动
        base_price = 150
        trend = np.linspace(0, 0.15, days)  # 15%增长
        volatility = 0.012
        volume_base = 5000000
        
    elif pattern == 'high_volatility':
        # ESTP/ESFP 模式: 高波动，大涨大跌
        base_price = 200
        trend = np.sin(np.linspace(0, 4*np.pi, days)) * 0.1  # 震荡
        volatility = 0.045
        volume_base = 15000000
        
    elif pattern == 'value_stable':
        # ISTJ/ISFJ 模式: 低波动，横盘整理
        base_price = 50
        trend = np.linspace(0, 0.03, days)  # 小幅增长
        volatility = 0.008
        volume_base = 3000000
        
    elif pattern == 'mean_reverting':
        # ISFP/ISTP 模式: 均值回归，区间内波动
        base_price = 100
        trend = np.sin(np.linspace(0, 6*np.pi, days)) * 0.05
        volatility = 0.025
        volume_base = 4000000
        
    elif pattern == 'trending':
        # INTJ/ENFP 模式: 强趋势，动量持续
        base_price = 80
        trend = np.linspace(0, 0.25, days)  # 强趋势25%
        volatility = 0.018
        volume_base = 8000000
        
    elif pattern == 'contrarian':
        # INFJ 模式: 逆市波动，提前见底
        base_price = 120
        # 先跌后涨，逆势
        trend = np.concatenate([
            np.linspace(0, -0.10, days//2),  # 前50%下跌
            np.linspace(-0.10, 0.05, days - days//2)  # 后50%反弹
        ])
        volatility = 0.022
        volume_base = 6000000
        
    else:
        base_price = 100
        trend = np.zeros(days)
        volatility = 0.02
        volume_base = 5000000
    
    # 生成价格
    np.random.seed(hash(ticker) % 2**32)
    returns = np.random.normal(trend/days, volatility, days)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # 生成OHLCV
    df = pd.DataFrame(index=dates)
    df['close'] = prices
    df['open'] = prices * (1 + np.random.normal(0, 0.003, days))
    df['high'] = np.maximum(prices * (1 + abs(np.random.normal(0, 0.008, days))),
                            df['open'] * 1.005)
    df['low'] = np.minimum(prices * (1 - abs(np.random.normal(0, 0.008, days))),
                           df['open'] * 0.995)
    df['volume'] = (volume_base * (1 + np.random.normal(0, 0.2, days))).astype(int)
    
    return df


def analyze_real_stocks():
    """分析具有真实特征的股票"""
    
    print("=" * 80)
    print("QuantClaw Pro - 真实股票特征分析演示")
    print("=" * 80)
    
    # 初始化系统
    print("\n【初始化】QuantClaw Pro...")
    claw = QuantClawPro(use_knowledge_graph=False)
    
    # 定义具有不同特征的股票
    stock_profiles = [
        {
            'ticker': 'AAPL',
            'name': '苹果',
            'pattern': 'stable_growth',
            'description': '科技股龙头，稳健增长，机构主导'
        },
        {
            'ticker': 'TSLA',
            'name': '特斯拉',
            'pattern': 'high_volatility',
            'description': '高波动，情绪化，散户追捧'
        },
        {
            'ticker': 'JNJ',
            'name': '强生',
            'pattern': 'value_stable',
            'description': '医药蓝筹，低波动，价值稳定'
        },
        {
            'ticker': 'IBM',
            'name': 'IBM',
            'pattern': 'mean_reverting',
            'description': '传统科技，均值回归，区间震荡'
        },
        {
            'ticker': 'NVDA',
            'name': '英伟达',
            'pattern': 'trending',
            'description': 'AI龙头，强趋势，动量持续'
        },
        {
            'ticker': 'BRK.B',
            'name': '伯克希尔',
            'pattern': 'contrarian',
            'description': '价值投资，逆向布局，独立判断'
        }
    ]
    
    results = []
    
    for stock in stock_profiles:
        print(f"\n{'='*80}")
        print(f"【分析】{stock['ticker']} - {stock['name']}")
        print(f"特征描述: {stock['description']}")
        print(f"价格模式: {stock['pattern']}")
        print('='*80)
        
        # 创建真实特征数据
        price_data = create_realistic_stock_data(
            stock['ticker'], 
            stock['pattern'],
            days=100
        )
        
        # 显示价格统计
        print(f"\n📈 价格统计 (最近100日):")
        print(f"  当前价格: ${price_data['close'].iloc[-1]:.2f}")
        print(f"  收益率: {(price_data['close'].iloc[-1]/price_data['close'].iloc[0]-1)*100:.1f}%")
        print(f"  波动率: {price_data['close'].pct_change().std()*np.sqrt(252)*100:.1f}%")
        print(f"  平均成交量: {price_data['volume'].mean()/1e6:.1f}M")
        
        # 运行分析
        result = claw.analyze_stock(
            ticker=stock['ticker'],
            price_data=price_data,
            current_price=price_data['close'].iloc[-1],
            market_regime=MarketRegime.SIDEWAYS,
            save_to_kg=False
        )
        
        if 'error' in result:
            print(f"❌ 分析错误: {result['error']}")
            continue
        
        # 显示感知层
        perception = result['perception']
        print(f"\n📊 感知层 (32维特征):")
        print(f"  数据质量: {perception['confidence']:.2%}")
        
        # 显示关键特征
        features = perception['features']
        print(f"  关键指标:")
        if 'adx' in features:
            print(f"    - ADX(趋势强度): {features['adx']:.2f}")
        if 'volatility_20d' in features:
            print(f"    - 20日波动率: {features['volatility_20d']:.2f}")
        if 'market_correlation' in features:
            print(f"    - 市场相关性: {features['market_correlation']:.2f}")
        if 'hurst_exponent' in features:
            print(f"    - 赫斯特指数: {features['hurst_exponent']:.2f}")
        
        # 显示认知层
        cog = result['cognition']
        print(f"\n🧠 认知层 (MBTI分类):")
        print(f"  类型: {cog['mbti_type']} ({cog['mbti_name']})")
        print(f"  类别: {cog['category']}")
        print(f"  风险等级: {cog['risk_level']}")
        print(f"  置信度: {cog['confidence']:.2%}")
        
        dims = cog['dimensions']
        print(f"\n  四维分数:")
        print(f"    I/E (内向/外向): {dims['ie']:.4f} ({'E外向' if dims['ie'] > 0.5 else 'I内向'})")
        print(f"    N/S (直觉/实感): {dims['ns']:.4f} ({'N直觉' if dims['ns'] > 0.5 else 'S实感'})")
        print(f"    T/F (思考/情感): {dims['tf']:.4f} ({'F情感' if dims['tf'] > 0.5 else 'T思考'})")
        print(f"    J/P (判断/感知): {dims['jp']:.4f} ({'J判断' if dims['jp'] > 0.5 else 'P感知'})")
        
        # 显示决策层
        dec = result['decision']
        print(f"\n🎯 决策层 (策略匹配):")
        print(f"  综合信号: {dec['composite_signal']['signal']}")
        print(f"  建议仓位: {dec['composite_signal']['suggested_position']:.0%}")
        
        print(f"\n  Top 3 推荐策略:")
        for i, strategy in enumerate(dec['recommended_strategies'][:3], 1):
            print(f"    {i}. {strategy['name']}")
            print(f"       权重{strategy['weight']:.0%} | "
                  f"兼容{strategy['compatibility']:.0%} | "
                  f"预期收益{strategy['expected_return']:.1%}")
        
        # 风险管理
        if dec['risk_management']:
            rm = dec['risk_management']
            print(f"\n  风险管理:")
            print(f"    止损: ${rm['suggested_stop_price']} | "
                  f"目标: ${rm['suggested_target_price']}")
        
        results.append({
            'ticker': stock['ticker'],
            'name': stock['name'],
            'pattern': stock['pattern'],
            'mbti': cog['mbti_type'],
            'mbti_name': cog['mbti_name'],
            'category': cog['category'],
            'risk': cog['risk_level']
        })
    
    # 汇总报告
    print(f"\n\n{'='*80}")
    print("【汇总报告】股票性格分布")
    print('='*80)
    
    print(f"\n{'股票':<8} {'名称':<10} {'模式':<18} {'MBTI':<6} {'性格':<12} {'类别':<12} {'风险':<8}")
    print("-" * 80)
    for r in results:
        print(f"{r['ticker']:<8} {r['name']:<10} {r['pattern']:<18} "
              f"{r['mbti']:<6} {r['mbti_name']:<12} {r['category']:<12} {r['risk']:<8}")
    
    # 统计分布
    print(f"\n【性格类别分布】")
    categories = {}
    for r in results:
        cat = r['category']
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in categories.items():
        print(f"  {cat}: {count}只")
    
    print(f"\n【风险等级分布】")
    risks = {}
    for r in results:
        risk = r['risk']
        risks[risk] = risks.get(risk, 0) + 1
    for risk, count in risks.items():
        print(f"  {risk}: {count}只")
    
    print(f"\n{'='*80}")
    print("演示完成！")
    print('='*80)
    print("\n💡 说明:")
    print("  本演示使用模拟但具有真实特征模式的价格数据")
    print("  不同价格模式(趋势/波动/回归)会产生不同的MBTI分类")
    print("  实际使用中请连接真实的股票数据源(Yahoo Finance等)")


if __name__ == "__main__":
    analyze_real_stocks()
