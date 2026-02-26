import yfinance as yf
import pandas as pd
import numpy as np

def analyze_stock(ticker, name):
    stock = yf.Ticker(ticker)
    hist = stock.history(period='1y')
    info = stock.info
    
    print(f'\n=== {name} ({ticker}) 技术分析 ===')
    
    # 当前价格和位置
    current = hist['Close'].iloc[-1]
    high_52w = info.get('fiftyTwoWeekHigh', hist['High'].max())
    low_52w = info.get('fiftyTwoWeekLow', hist['Low'].min())
    position = (current - low_52w) / (high_52w - low_52w) * 100
    
    print(f'当前价格: ${current:.2f}')
    print(f'52周区间: ${low_52w:.2f} - ${high_52w:.2f}')
    print(f'区间位置: {position:.1f}% (0%=低点, 100%=高点)')
    
    # 移动平均线
    hist['MA20'] = hist['Close'].rolling(20).mean()
    hist['MA50'] = hist['Close'].rolling(50).mean()
    hist['MA200'] = hist['Close'].rolling(200).mean()
    
    ma20 = hist['MA20'].iloc[-1]
    ma50 = hist['MA50'].iloc[-1]
    ma200 = hist['MA200'].iloc[-1]
    
    print(f'MA20: ${ma20:.2f}')
    print(f'MA50: ${ma50:.2f}')
    print(f'MA200: ${ma200:.2f}')
    
    # 趋势判断
    if current > ma50 > ma200:
        trend = 'UP'
    elif current < ma50 < ma200:
        trend = 'DOWN'
    else:
        trend = 'MIXED'
    print(f'趋势: {trend}')
    
    # RSI
    delta = hist['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    print(f'RSI(14): {rsi.iloc[-1]:.1f}')
    
    # 成交量分析
    avg_vol = hist['Volume'].rolling(20).mean().iloc[-1]
    last_vol = hist['Volume'].iloc[-1]
    print(f'成交量(20日均): {avg_vol/1e6:.1f}M')
    print(f'最新成交量: {last_vol/1e6:.1f}M')
    
    # PE数据
    trailing_pe = info.get('trailingPE', 'N/A')
    forward_pe = info.get('forwardPE', 'N/A')
    if isinstance(trailing_pe, (int, float)):
        print(f'Trailing PE: {trailing_pe:.1f}')
    else:
        print(f'Trailing PE: {trailing_pe}')
    if isinstance(forward_pe, (int, float)):
        print(f'Forward PE: {forward_pe:.1f}')
    else:
        print(f'Forward PE: {forward_pe}')
    
    # 支撑阻力（近期高低点）
    recent = hist.tail(60)
    resistance = recent['High'].max()
    support = recent['Low'].min()
    print(f'近期支撑: ${support:.2f}')
    print(f'近期阻力: ${resistance:.2f}')

analyze_stock('MSFT', 'Microsoft')
analyze_stock('AMZN', 'Amazon')