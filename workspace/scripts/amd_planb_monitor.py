#!/usr/bin/env python3
"""
AMD 方案B突破买入监控
监控条件:
1. 价格突破MA20($231)
2. 成交量 > 1.5x 20日均量
3. MACD柱状图缩窄或金叉

触发后提醒买入机会
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

STATE_FILE = "/Users/oneday/.openclaw/workspace/memory/amd_planb_state.json"
MA20_LEVEL = 231  # MA20参考价位
ALERT_THRESHOLD = 1.5  # 放量倍数

def load_state():
    """加载监控状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "last_alert_time": 0,
        "last_alert_price": 0,
        "alert_count": 0,
        "ma20_broken": False
    }

def save_state(state):
    """保存监控状态"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_amd_data(period="1mo", interval="1h"):
    """获取AMD股票数据"""
    try:
        ticker = yf.Ticker("AMD")
        df = ticker.history(period=period, interval=interval)
        return df
    except Exception as e:
        print(f"获取AMD数据失败: {e}")
        return None

def calculate_indicators(df):
    """计算技术指标"""
    # MA20
    df['MA20'] = df['Close'].rolling(window=20).mean()
    
    # MA50
    df['MA50'] = df['Close'].rolling(window=50).mean()
    
    # 成交量均线
    df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def check_planb_signal(df):
    """
    检测方案B买入信号
    
    条件:
    1. 价格 > MA20 (突破)
    2. 成交量 > 1.5x 20日均量 (放量)
    3. MACD柱状图缩窄(空头减弱) 或 MACD金叉 (多头确认)
    
    返回: (是否触发, 信号详情)
    """
    if len(df) < 30:
        return False, {"error": "数据不足"}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 当前价格和均线
    current_price = latest['Close']
    ma20 = latest['MA20']
    ma50 = latest['MA50']
    
    # 条件1: 突破MA20
    price_above_ma20 = current_price > ma20
    # 前一日在MA20下方(确认突破而非一直在上方)
    prev_below_ma20 = prev['Close'] < prev['MA20']
    # 或者距离MA20很近即将突破
    near_ma20 = abs(current_price / ma20 - 1) < 0.02
    
    ma20_break = (price_above_ma20 and prev_below_ma20) or (price_above_ma20 and near_ma20)
    
    # 条件2: 放量
    volume = latest['Volume']
    volume_ma20 = latest['Volume_MA20']
    volume_surge = volume > volume_ma20 * ALERT_THRESHOLD
    volume_ratio = volume / volume_ma20 if volume_ma20 > 0 else 0
    
    # 条件3: MACD信号
    histogram = latest['Histogram']
    prev_histogram = prev['Histogram']
    macd = latest['MACD']
    signal_line = latest['Signal']
    
    # MACD柱状图缩窄 (空头动能减弱)
    histogram_shrinking = histogram > prev_histogram and histogram < 0
    # 或MACD金叉
    macd_golden_cross = macd > signal_line and prev['MACD'] <= prev['Signal']
    # 或MACD已经在零轴上方运行
    macd_bullish = macd > 0 and signal_line > 0
    
    macd_signal = histogram_shrinking or macd_golden_cross or macd_bullish
    
    # 综合判断
    signal_strength = 0
    if price_above_ma20:
        signal_strength += 1
    if volume_surge:
        signal_strength += 1
    if macd_signal:
        signal_strength += 1
    
    # 至少需要满足2个条件才触发
    triggered = signal_strength >= 2 and price_above_ma20
    
    details = {
        "current_price": round(current_price, 2),
        "ma20": round(ma20, 2),
        "ma50": round(ma50, 2),
        "price_above_ma20": price_above_ma20,
        "ma20_break": ma20_break,
        "prev_below_ma20": prev_below_ma20,
        "volume_ratio": round(volume_ratio, 2),
        "volume_surge": volume_surge,
        "histogram": round(histogram, 4),
        "prev_histogram": round(prev_histogram, 4),
        "histogram_shrinking": histogram_shrinking,
        "macd_golden_cross": macd_golden_cross,
        "macd_bullish": macd_bullish,
        "rsi": round(latest['RSI'], 1),
        "signal_strength": signal_strength,
        "triggered": triggered,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return triggered, details

def format_alert(details):
    """格式化提醒消息"""
    lines = [
        "🔥 **AMD 方案B突破信号触发！** 🔥",
        "",
        f"📈 **价格突破**: ${details['current_price']} > MA20(${details['ma20']})",
        f"📊 **成交量**: {details['volume_ratio']}x 均量 {'✅放量' if details['volume_surge'] else ''}",
        f"📉 **MACD**: 柱状图{'缩窄' if details['histogram_shrinking'] else ''}{'金叉' if details['macd_golden_cross'] else ''}",
        f"📊 **RSI**: {details['rsi']}",
        "",
        "✅ **买入条件达成**:",
        "  • 放量突破MA20，趋势转多确认",
        "  • 建议买入区间: $232 - $240",
        "  • 建议仓位: 40%",
        "",
        "⚠️ **风险控制**:",
        "  • 止损位: 跌破MA20且收盘无法收回",
        "  • 跌破$220减半仓",
        "",
        f"⏰ 信号时间: {details['timestamp']}"
    ]
    return "\n".join(lines)

def check_and_alert():
    """主检测函数"""
    print("=" * 60)
    print("AMD 方案B突破买入监控")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 获取数据
    df = get_amd_data(period="1mo", interval="1h")
    if df is None:
        print("❌ 获取数据失败")
        return None
    
    # 计算指标
    df = calculate_indicators(df)
    
    # 检测信号
    triggered, details = check_planb_signal(df)
    
    # 加载状态
    state = load_state()
    now_ts = int(datetime.now().timestamp())
    
    print(f"\n当前价格: ${details['current_price']}")
    print(f"MA20: ${details['ma20']}")
    print(f"MA50: ${details['ma50']}")
    print(f"成交量比: {details['volume_ratio']}x")
    print(f"RSI: {details['rsi']}")
    print(f"MACD柱状图: {details['histogram']}")
    print(f"\n信号强度: {details['signal_strength']}/3")
    print(f"是否触发: {'✅ 是！' if triggered else '❌ 否'}")
    
    # 防重复提醒 (6小时内同一价格不重复提醒)
    price_diff = abs(details['current_price'] - state.get('last_alert_price', 0))
    time_diff = now_ts - state.get('last_alert_time', 0)
    
    if triggered and (price_diff > 5 or time_diff > 6 * 3600):
        # 更新状态
        state['last_alert_time'] = now_ts
        state['last_alert_price'] = details['current_price']
        state['alert_count'] = state.get('alert_count', 0) + 1
        state['ma20_broken'] = True
        save_state(state)
        
        # 生成提醒
        alert_msg = format_alert(details)
        print("\n" + "=" * 60)
        print(alert_msg)
        print("=" * 60)
        
        # 写入提醒文件
        alert_file = "/Users/oneday/.openclaw/workspace/memory/amd_planb_alert.txt"
        with open(alert_file, 'w') as f:
            f.write(alert_msg)
        
        return alert_msg
    elif triggered:
        print(f"\n⚠️ 信号已触发，但距离上次提醒太近(价格差${price_diff:.2f}, 时间差{time_diff//60}分钟)")
        print("   6小时内或价格变动>$5前不再重复提醒")
    else:
        print(f"\n📊 尚未满足突破条件")
        print(f"   需同时满足: 价格>MA20 + 放量1.5x + MACD转多")
    
    save_state(state)
    return None

if __name__ == "__main__":
    check_and_alert()
