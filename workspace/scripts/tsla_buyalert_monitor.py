#!/usr/bin/env python3
"""
TSLA 买入时机监控脚本
监控三个买入方案:
A. 回调买入: $380-400 (企稳信号, RSI<35)
B. 突破买入: $425+ (放量突破MA20) / $450+ (趋势确认)
C. 极端回调: $315-340 (恐慌买入)

触发后发送买入提醒
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

STATE_FILE = "/Users/oneday/.openclaw/workspace/memory/tsla_buyalert_state.json"

def load_state():
    """加载监控状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "plan_a_alerted": False,
        "plan_b_alerted": False,
        "plan_c_alerted": False,
        "last_alert_time": 0,
        "last_alert_price": 0,
        "alert_count": 0
    }

def save_state(state):
    """保存监控状态"""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_tsla_data(period="3mo", interval="1h"):
    """获取TSLA股票数据"""
    try:
        ticker = yf.Ticker("TSLA")
        df = ticker.history(period=period, interval=interval)
        return df
    except Exception as e:
        print(f"获取TSLA数据失败: {e}")
        return None

def calculate_indicators(df):
    """计算技术指标"""
    # 移动平均线
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
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
    
    # 布林带
    df['BB_Middle'] = df['Close'].rolling(20).mean()
    df['BB_Upper'] = df['BB_Middle'] + 2 * df['Close'].rolling(20).std()
    df['BB_Lower'] = df['BB_Middle'] - 2 * df['Close'].rolling(20).std()
    
    # 20日高低点
    df['High_20d'] = df['High'].rolling(20).max()
    df['Low_20d'] = df['Low'].rolling(20).min()
    
    return df

def check_plan_a_support(df):
    """
    方案A: 回调至支撑位$380-400买入
    条件:
    1. 价格跌至$380-400区间
    2. RSI < 35 (超卖)
    3. 出现企稳K线(长下影/阳线)
    4. 缩量止跌或温和放量
    """
    if len(df) < 10:
        return False, {}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    current_price = latest['Close']
    
    # 价格在$380-400区间
    in_support_zone = 380 <= current_price <= 400
    
    # RSI < 35
    rsi_low = latest['RSI'] < 35
    
    # 企稳信号: 长下影线或阳线
    body = abs(latest['Close'] - latest['Open'])
    lower_shadow = min(latest['Close'], latest['Open']) - latest['Low']
    upper_shadow = latest['High'] - max(latest['Close'], latest['Open'])
    
    stabilization = (lower_shadow > body * 1.5) or (latest['Close'] > latest['Open'])
    
    # 成交量不异常放大(不是恐慌抛售)
    volume_normal = latest['Volume'] < latest['Volume_MA20'] * 1.5
    
    # 价格接近20日低点
    near_low = current_price <= latest['Low_20d'] * 1.05
    
    triggered = in_support_zone and (rsi_low or stabilization) and volume_normal
    
    details = {
        "plan": "A",
        "name": "回调支撑位买入",
        "price": round(current_price, 2),
        "in_zone": in_support_zone,
        "rsi": round(latest['RSI'], 1),
        "rsi_low": rsi_low,
        "stabilization": stabilization,
        "volume_ok": volume_normal,
        "near_low": near_low,
        "triggered": triggered
    }
    
    return triggered, details

def check_plan_b_breakout(df):
    """
    方案B: 突破买入 $425+ (MA20突破) / $450+ (趋势确认)
    条件:
    1. 价格突破$425 (MA20) 或 $450
    2. 成交量 > 1.3x 均量
    3. RSI > 50 向上
    4. MACD金叉或柱状图扩张
    """
    if len(df) < 20:
        return False, {}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    current_price = latest['Close']
    ma20 = latest['MA20']
    
    # 突破MA20或$450
    breakout_ma20 = current_price > ma20 and prev['Close'] <= prev['MA20']
    breakout_450 = current_price > 450 and prev['Close'] <= 450
    
    breakout = breakout_ma20 or breakout_450
    breakout_level = "$450" if breakout_450 else f"MA20(${ma20:.0f})"
    
    # 放量
    volume_surge = latest['Volume'] > latest['Volume_MA20'] * 1.3
    volume_ratio = latest['Volume'] / latest['Volume_MA20'] if latest['Volume_MA20'] > 0 else 0
    
    # RSI向上
    rsi_rising = latest['RSI'] > 50 and latest['RSI'] > prev['RSI']
    
    # MACD信号
    macd_golden = latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']
    histogram_expanding = latest['Histogram'] > prev['Histogram'] and latest['Histogram'] > 0
    macd_signal = macd_golden or histogram_expanding
    
    # 至少满足突破+放量+(RSI或MACD)
    triggered = breakout and volume_surge and (rsi_rising or macd_signal)
    
    details = {
        "plan": "B",
        "name": "突破追涨买入",
        "price": round(current_price, 2),
        "breakout": breakout,
        "breakout_level": breakout_level,
        "ma20": round(ma20, 2),
        "volume_ratio": round(volume_ratio, 2),
        "volume_surge": volume_surge,
        "rsi": round(latest['RSI'], 1),
        "rsi_rising": rsi_rising,
        "macd_golden": macd_golden,
        "histogram_expanding": histogram_expanding,
        "triggered": triggered
    }
    
    return triggered, details

def check_plan_c_panic(df):
    """
    方案C: 极端回调 $315-340 恐慌买入
    条件:
    1. 价格跌至$315-340区间 (接近52周低点$315)
    2. RSI < 30 (明显超卖)
    3. 成交量异常放大(恐慌盘涌出)
    4. 出现长下影线(抄底盘介入)
    """
    if len(df) < 10:
        return False, {}
    
    latest = df.iloc[-1]
    current_price = latest['Close']
    
    # 价格在$315-340区间
    in_panic_zone = 315 <= current_price <= 340
    
    # RSI明显超卖
    rsi_panic = latest['RSI'] < 30
    
    # 成交量放大(恐慌)
    volume_panic = latest['Volume'] > latest['Volume_MA20'] * 1.5
    volume_ratio = latest['Volume'] / latest['Volume_MA20'] if latest['Volume_MA20'] > 0 else 0
    
    # 长下影线(抄底信号)
    body = abs(latest['Close'] - latest['Open'])
    lower_shadow = min(latest['Close'], latest['Open']) - latest['Low']
    long_shadow = lower_shadow > body * 2
    
    # 接近52周低点
    near_52w_low = current_price <= 340
    
    triggered = in_panic_zone and rsi_panic and (volume_panic or long_shadow)
    
    details = {
        "plan": "C",
        "name": "恐慌极端买入",
        "price": round(current_price, 2),
        "in_zone": in_panic_zone,
        "rsi": round(latest['RSI'], 1),
        "rsi_panic": rsi_panic,
        "volume_panic": volume_panic,
        "volume_ratio": round(volume_ratio, 2),
        "long_shadow": long_shadow,
        "near_52w_low": near_52w_low,
        "triggered": triggered
    }
    
    return triggered, details

def format_alert(plan, details):
    """格式化提醒消息"""
    
    if plan == "A":
        lines = [
            "🎯 **TSLA 方案A - 回调支撑位买入信号！**",
            "",
            f"📉 **价格**: ${details['price']} (进入$380-400支撑区)",
            f"📊 **RSI**: {details['rsi']} ({'超卖' if details['rsi'] < 35 else '接近超卖'})",
            f"✅ **企稳信号**: {'出现' if details['stabilization'] else '观察中'}",
            f"📈 **位置**: {'接近20日低点' if details['near_low'] else '正常区间'}",
            "",
            "💡 **买入建议**:",
            "  • 买入区间: $380 - $400",
            "  • 建议仓位: 20-25%",
            "  • 止损位: $375 (跌破支撑)",
            "  • 目标位: $425 / $450 / $499",
            "",
            "⚠️ **注意**: 确认缩量止跌后再介入，避免接飞刀"
        ]
    
    elif plan == "B":
        lines = [
            "🚀 **TSLA 方案B - 突破追涨买入信号！**",
            "",
            f"📈 **价格**: ${details['price']} (突破{details['breakout_level']})",
            f"📊 **成交量**: {details['volume_ratio']}x 均量 {'✅放量' if details['volume_surge'] else ''}",
            f"📈 **RSI**: {details['rsi']} ({'向上' if details['rsi_rising'] else '观察'})",
            f"📉 **MACD**: {'金叉' if details['macd_golden'] else '柱状图扩张' if details['histogram_expanding'] else '多头'}",
            "",
            "💡 **买入建议**:",
            f"  • 买入区间: ${details['price']:.0f} - ${details['price']+5:.0f}",
            "  • 建议仓位: 30-35%",
            "  • 止损位: $415 (跌破突破位)",
            "  • 目标位: $450 / $480 / $499",
            "",
            "✅ **趋势确认**: 放量突破，可顺势追涨"
        ]
    
    elif plan == "C":
        lines = [
            "🔥 **TSLA 方案C - 极端恐慌买入信号！**",
            "",
            f"📉 **价格**: ${details['price']} (深度回调至$315-340)",
            f"📊 **RSI**: {details['rsi']} (严重超卖)",
            f"⚡ **恐慌信号**: {'成交量异常' if details['volume_panic'] else ''} {'长下影线' if details['long_shadow'] else ''}",
            f"📍 **位置**: {'接近52周低点' if details['near_52w_low'] else '深度回调区'}",
            "",
            "💡 **买入建议**:",
            "  • 买入区间: $315 - $340",
            "  • 建议仓位: 40-50% (可重仓)",
            "  • 止损位: $305 (极端情况)",
            "  • 目标位: $380 / $420 / $450",
            "",
            "🎯 **机会型买入**: 长期投资价值区域，适合逆向投资者"
        ]
    
    lines.extend([
        "",
        f"⏰ 信号时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "---",
        "💡 建议结合大盘环境和个人风险承受能力决策"
    ])
    
    return "\n".join(lines)

def check_and_alert():
    """主检测函数"""
    print("=" * 60)
    print("TSLA 买入时机监控")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 获取数据
    df = get_tsla_data(period="3mo", interval="1h")
    if df is None:
        print("❌ 获取数据失败")
        return None
    
    # 计算指标
    df = calculate_indicators(df)
    
    # 加载状态
    state = load_state()
    now_ts = int(datetime.now().timestamp())
    
    # 获取当前价格
    current_price = df.iloc[-1]['Close']
    latest = df.iloc[-1]
    
    print(f"\n当前价格: ${current_price:.2f}")
    print(f"MA20: ${latest['MA20']:.2f}")
    print(f"MA50: ${latest['MA50']:.2f}")
    print(f"20日高点: ${latest['High_20d']:.2f}")
    print(f"20日低点: ${latest['Low_20d']:.2f}")
    print(f"RSI: {latest['RSI']:.1f}")
    print(f"成交量比: {latest['Volume']/latest['Volume_MA20']:.2f}x")
    print(f"MACD柱状图: {latest['Histogram']:.4f}")
    
    # 检测三个方案
    results = []
    
    # 方案A: 回调支撑
    triggered_a, details_a = check_plan_a_support(df)
    results.append(("A", triggered_a, details_a))
    print(f"\n方案A (回调$380-400): {'✅ 触发!' if triggered_a else '❌ 未触发'}")
    
    # 方案B: 突破追涨
    triggered_b, details_b = check_plan_b_breakout(df)
    results.append(("B", triggered_b, details_b))
    print(f"方案B (突破$425+): {'✅ 触发!' if triggered_b else '❌ 未触发'}")
    
    # 方案C: 极端回调
    triggered_c, details_c = check_plan_c_panic(df)
    results.append(("C", triggered_c, details_c))
    print(f"方案C (恐慌$315-340): {'✅ 触发!' if triggered_c else '❌ 未触发'}")
    
    # 防重复提醒 (同一方案6小时内不重复)
    alerts = []
    for plan, triggered, details in results:
        alert_key = f"plan_{plan.lower()}_alerted"
        last_alert = state.get(alert_key, False)
        time_diff = now_ts - state.get('last_alert_time', 0)
        
        if triggered and (not last_alert or time_diff > 6 * 3600):
            # 更新状态
            state[alert_key] = True
            state['last_alert_time'] = now_ts
            state['last_alert_price'] = current_price
            state['alert_count'] = state.get('alert_count', 0) + 1
            
            # 生成提醒
            alert_msg = format_alert(plan, details)
            alerts.append(alert_msg)
            print(f"\n🚨 方案{plan}提醒已生成!")
        elif triggered:
            print(f"\n⚠️ 方案{plan}已触发，但距离上次提醒太近({time_diff//3600}小时)")
    
    # 价格离开区间后重置状态
    if current_price > 410:
        state['plan_a_alerted'] = False
    if current_price < 415:
        state['plan_b_alerted'] = False
    if current_price > 350:
        state['plan_c_alerted'] = False
    
    save_state(state)
    
    # 输出提醒
    if alerts:
        full_alert = "\n\n" + "="*60 + "\n\n".join(alerts) + "\n" + "="*60
        print(full_alert)
        
        # 写入提醒文件
        alert_file = "/Users/oneday/.openclaw/workspace/memory/tsla_buyalert.txt"
        with open(alert_file, 'w') as f:
            f.write(full_alert)
        
        return full_alert
    else:
        print("\n\n📊 暂无买入信号，继续监控...")
        print("监控区间: $315-340(方案C) | $380-400(方案A) | $425+/450+(方案B)")
    
    return None

if __name__ == "__main__":
    check_and_alert()
