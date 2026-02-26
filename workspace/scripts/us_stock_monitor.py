#!/usr/bin/env python3
"""
美股技术信号监控脚本
监控标的: MSFT, AMZN
监控信号: 放量阳线、底背离
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# 监控配置
WATCHLIST = {
    "MSFT": {"name": "微软", "alert_price_low": 392, "alert_price_high": 420},
    "AMZN": {"name": "亚马逊", "alert_price_low": 197, "alert_price_high": 220}
}

STATE_FILE = "/Users/oneday/.openclaw/workspace/memory/stock_signals_state.json"

def load_state():
    """加载上次的状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    """保存状态"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_stock_data(symbol, period="1mo", interval="1h"):
    """获取股票数据"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        return df
    except Exception as e:
        print(f"获取{symbol}数据失败: {e}")
        return None

def detect_volume_surge(df, threshold=1.5):
    """
    检测放量阳线信号
    条件:
    1. 当日收盘价 > 开盘价 (阳线)
    2. 成交量 > 前N日平均成交量 * threshold
    3. 涨幅 > 1%
    """
    if len(df) < 5:
        return False, None
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 阳线判断
    is_yang = latest['Close'] > latest['Open']
    
    # 涨幅判断 (>1%)
    price_change = (latest['Close'] - prev['Close']) / prev['Close'] * 100
    is_up = price_change > 1.0
    
    # 放量判断
    avg_volume = df['Volume'].tail(20).mean()
    is_volume_surge = latest['Volume'] > avg_volume * threshold
    
    signal = {
        "type": "放量阳线",
        "price": round(latest['Close'], 2),
        "open": round(latest['Open'], 2),
        "change_pct": round(price_change, 2),
        "volume": int(latest['Volume']),
        "avg_volume_20d": int(avg_volume),
        "volume_ratio": round(latest['Volume'] / avg_volume, 2)
    }
    
    return is_yang and is_up and is_volume_surge, signal

def detect_bullish_divergence(df):
    """
    检测底背离信号
    条件:
    1. 价格创近期新低
    2. MACD或RSI未创新低 (背离)
    3. 出现企稳K线
    """
    if len(df) < 20:
        return False, None
    
    # 计算RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 计算MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 取最近10天数据
    recent = df.tail(10)
    
    # 价格新低判断
    price_low = df['Close'].tail(20).min()
    price_recent_low = recent['Close'].min()
    
    # 如果最近价格是20日最低点或接近最低点
    is_price_low = price_recent_low <= price_low * 1.02
    
    # RSI背离判断: 价格新低但RSI未新低
    rsi_low = df['RSI'].tail(20).min()
    rsi_recent_low = recent['RSI'].min()
    rsi_divergence = price_recent_low <= price_low * 1.01 and rsi_recent_low > rsi_low * 1.05
    
    # MACD背离判断
    macd_low = df['MACD'].tail(20).min()
    macd_recent_low = recent['MACD'].min()
    macd_divergence = price_recent_low <= price_low * 1.01 and macd_recent_low > macd_low * 1.05
    
    # 企稳判断: 最近一根K线收阳或十字星
    latest = df.iloc[-1]
    is_stabilize = latest['Close'] >= latest['Open'] * 0.995
    
    has_divergence = rsi_divergence or macd_divergence
    
    signal = {
        "type": "底背离",
        "price": round(latest['Close'], 2),
        "rsi": round(latest['RSI'], 2),
        "macd": round(latest['MACD'], 4),
        "rsi_divergence": rsi_divergence,
        "macd_divergence": macd_divergence,
        "price_low_20d": round(price_low, 2),
        "is_stabilize": is_stabilize
    }
    
    return is_price_low and has_divergence and is_stabilize, signal

def check_signals():
    """主检测函数"""
    results = []
    state = load_state()
    
    for symbol, config in WATCHLIST.items():
        print(f"\n🔍 正在分析 {symbol} ({config['name']})...")
        
        # 获取日线数据(用于背离判断)
        df_daily = get_stock_data(symbol, period="3mo", interval="1d")
        # 获取小时线数据(用于放量判断)
        df_hourly = get_stock_data(symbol, period="1mo", interval="1h")
        
        if df_daily is None or df_hourly is None:
            continue
        
        current_price = df_daily.iloc[-1]['Close']
        
        # 检测放量阳线 (使用小时线)
        volume_signal, volume_details = detect_volume_surge(df_hourly)
        
        # 检测底背离 (使用日线)
        divergence_signal, divergence_details = detect_bullish_divergence(df_daily)
        
        result = {
            "symbol": symbol,
            "name": config['name'],
            "current_price": round(current_price, 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "volume_signal": volume_signal,
            "divergence_signal": divergence_signal,
            "volume_details": volume_details,
            "divergence_details": divergence_details,
            "alert_triggered": False
        }
        
        # 判断是否需要提醒
        alert_key = f"{symbol}_alert"
        last_alert = state.get(alert_key, 0)
        now_ts = int(datetime.now().timestamp())
        
        # 同一信号6小时内不重复提醒
        if (volume_signal or divergence_signal) and (now_ts - last_alert > 6 * 3600):
            result["alert_triggered"] = True
            state[alert_key] = now_ts
        
        results.append(result)
        
        # 打印结果
        print(f"  现价: ${current_price:.2f}")
        print(f"  放量阳线: {'✅ 信号出现!' if volume_signal else '❌ 未出现'}")
        print(f"  底背离: {'✅ 信号出现!' if divergence_signal else '❌ 未出现'}")
    
    save_state(state)
    return results

def format_alert(results):
    """格式化提醒消息"""
    alerts = [r for r in results if r["alert_triggered"]]
    
    if not alerts:
        return None
    
    msg_lines = ["🚨 **技术信号提醒** 🚨", ""]
    
    for r in alerts:
        msg_lines.append(f"📈 **{r['symbol']}** ({r['name']}) - ${r['current_price']}")
        
        if r["volume_signal"]:
            d = r["volume_details"]
            msg_lines.append(f"  ✅ **放量阳线信号**")
            msg_lines.append(f"     涨幅: +{d['change_pct']}%")
            msg_lines.append(f"     成交量: {d['volume_ratio']}倍于20日均量")
        
        if r["divergence_signal"]:
            d = r["divergence_details"]
            msg_lines.append(f"  ✅ **底背离信号**")
            msg_lines.append(f"     RSI: {d['rsi']}")
            msg_lines.append(f"     RSI背离: {'是' if d['rsi_divergence'] else '否'}")
            msg_lines.append(f"     MACD背离: {'是' if d['macd_divergence'] else '否'}")
        
        msg_lines.append("")
    
    msg_lines.append("---")
    msg_lines.append("💡 建议结合基本面和市场情绪综合判断")
    
    return "\n".join(msg_lines)

if __name__ == "__main__":
    print("=" * 50)
    print("美股技术信号监控")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    results = check_signals()
    alert_msg = format_alert(results)
    
    # 输出提醒(如果有)
    if alert_msg:
        print("\n" + "=" * 50)
        print(alert_msg)
        print("=" * 50)
        
        # 将提醒写入文件，供外部读取
        alert_file = "/Users/oneday/.openclaw/workspace/memory/stock_alert.txt"
        with open(alert_file, 'w') as f:
            f.write(alert_msg)
    else:
        print("\n📊 暂无新的技术信号")
        
    print("\n监控完成")
