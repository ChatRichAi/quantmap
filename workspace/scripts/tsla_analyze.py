#!/usr/bin/env python3
import yfinance as yf
import pandas as pd
import numpy as np

# 获取TSLA数据
symbol = 'TSLA'
ticker = yf.Ticker(symbol)

# 获取日线数据
df_daily = ticker.history(period='3mo', interval='1d')
df_hourly = ticker.history(period='1mo', interval='1h')

# 最新价格
latest = df_daily.iloc[-1]
current_price = latest['Close']
prev_close = df_daily.iloc[-2]['Close']
change_pct = (current_price - prev_close) / prev_close * 100

print(f'=== TSLA 技术分析 ===')
print(f'当前价格: ${current_price:.2f}')
print(f'涨跌: {change_pct:+.2f}%')
print(f'今日开盘: ${latest["Open"]:.2f}')
print(f'今日最高: ${latest["High"]:.2f}')
print(f'今日最低: ${latest["Low"]:.2f}')
print(f'成交量: {latest["Volume"]:,}')

# 计算MA
ma5 = df_daily['Close'].tail(5).mean()
ma10 = df_daily['Close'].tail(10).mean()
ma20 = df_daily['Close'].tail(20).mean()
ma50 = df_daily['Close'].tail(50).mean()

print(f'\n=== 均线系统 ===')
print(f'MA5:  ${ma5:.2f} {">价格" if current_price > ma5 else "<价格"}')
print(f'MA10: ${ma10:.2f} {">价格" if current_price > ma10 else "<价格"}')
print(f'MA20: ${ma20:.2f} {">价格" if current_price > ma20 else "<价格"}')
print(f'MA50: ${ma50:.2f} {">价格" if current_price > ma50 else "<价格"}')

# 均线排列
ma_bullish = ma5 > ma10 > ma20
ma_bearish = ma5 < ma10 < ma20
print(f'均线排列: {"多头排列" if ma_bullish else "空头排列" if ma_bearish else "震荡"}')

# 计算RSI
delta = df_daily['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))
rsi_current = rsi.iloc[-1]

print(f'\n=== 摆动指标 ===')
print(f'RSI(14): {rsi_current:.2f} ({"超买>70" if rsi_current > 70 else "超卖<30" if rsi_current < 30 else "中性"})')

# 计算MACD
exp1 = df_daily['Close'].ewm(span=12, adjust=False).mean()
exp2 = df_daily['Close'].ewm(span=26, adjust=False).mean()
macd = exp1 - exp2
signal = macd.ewm(span=9, adjust=False).mean()
hist = macd - signal

macd_current = macd.iloc[-1]
signal_current = signal.iloc[-1]
hist_current = hist.iloc[-1]
hist_prev = hist.iloc[-2]

print(f'MACD: {macd_current:.4f}')
print(f'Signal: {signal_current:.4f}')
print(f'Histogram: {hist_current:.4f} ({"扩张" if hist_current > hist_prev else "收缩"})')
macd_cross = (hist_prev < 0 and hist_current > 0) or (hist_prev > 0 and hist_current < 0)
if macd_cross:
    print(f'⚠️ MACD{"金叉" if hist_current > 0 else "死叉"}信号')

# 支撑阻力
high_20 = df_daily['High'].tail(20).max()
low_20 = df_daily['Low'].tail(20).min()

print(f'\n=== 支撑阻力 (20日) ===')
print(f'阻力位: ${high_20:.2f}')
print(f'支撑位: ${low_20:.2f}')
print(f'区间位置: {(current_price - low_20) / (high_20 - low_20) * 100:.1f}%')

# 成交量分析
avg_volume_20 = df_daily['Volume'].tail(20).mean()
volume_ratio = latest['Volume'] / avg_volume_20
print(f'\n=== 量价分析 ===')
print(f'20日均量: {avg_volume_20:,.0f}')
print(f'量比: {volume_ratio:.2f}x ({"放量" if volume_ratio > 1.3 else "缩量"})')

# K线形态
body = abs(latest['Close'] - latest['Open'])
upper_shadow = latest['High'] - max(latest['Close'], latest['Open'])
lower_shadow = min(latest['Close'], latest['Open']) - latest['Low']
is_yang = latest['Close'] > latest['Open']

print(f'\n=== K线形态 ===')
print(f'K线: {"阳线" if is_yang else "阴线"}')
print(f'实体: ${body:.2f}')
print(f'上影线: ${upper_shadow:.2f}')
print(f'下影线: ${lower_shadow:.2f}')

if body < (high_20 - low_20) * 0.01:
    print('形态: 十字星/纺锤线')
elif upper_shadow > body * 2 and lower_shadow < body:
    print('形态: 流星线')
elif lower_shadow > body * 2 and upper_shadow < body:
    print('形态: 锤子线')

print(f'\n=== 综合判断 ===')
# 多头信号
bull_signals = 0
if current_price > ma20: bull_signals += 1
if ma5 > ma10: bull_signals += 1
if rsi_current > 50 and rsi_current < 70: bull_signals += 1
if hist_current > 0: bull_signals += 1
if volume_ratio > 1.0: bull_signals += 1

# 空头信号
bear_signals = 0
if current_price < ma20: bear_signals += 1
if ma5 < ma10: bear_signals += 1
if rsi_current < 50: bear_signals += 1
if hist_current < 0: bear_signals += 1

if bull_signals >= 4:
    print('结论: 强势偏多')
elif bull_signals >= 3:
    print('结论: 偏多震荡')
elif bear_signals >= 4:
    print('结论: 强势偏空')
elif bear_signals >= 3:
    print('结论: 偏空震荡')
else:
    print('结论: 震荡整理')

print(f'(多头信号: {bull_signals}/5, 空头信号: {bear_signals}/5)')
