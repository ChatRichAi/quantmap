#!/usr/bin/env python3
"""
BABA (阿里巴巴) 买入时机监控
⚠️ 风险提示: BABA基本面承压，仅适合高风险偏好投资者

监控买入条件:
1. 价格跌至强支撑区间 $130-140 + 企稳信号
2. 放量突破关键阻力位 $170 + 趋势转多
3. 极端恐慌情况 $110-120 (历史大底区间)

注意: BABA存在中概股退市风险、地缘政治风险，请谨慎投资
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

STATE_FILE = "/Users/oneday/.openclaw/workspace/memory/baba_buyalert_state.json"

def load_state():
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
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_baba_data(period="3mo", interval="1d"):
    try:
        ticker = yf.Ticker("BABA")
        df = ticker.history(period=period, interval=interval)
        return df
    except Exception as e:
        print(f"获取BABA数据失败: {e}")
        return None

def calculate_indicators(df):
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()
    df['MA200'] = df['Close'].rolling(200).mean()
    df['Volume_MA20'] = df['Volume'].rolling(20).mean()
    
    # RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain / loss))
    
    # MACD
    exp1 = df['Close'].ewm(span=12).mean()
    exp2 = df['Close'].ewm(span=26).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    df['Histogram'] = df['MACD'] - df['Signal']
    
    return df

def check_plan_a_support(df):
    """
    方案A: 强支撑位买入 $130-140
    条件: 价格进入区间 + RSI超卖 + 缩量止跌
    """
    if len(df) < 10:
        return False, {}
    
    latest = df.iloc[-1]
    current_price = latest['Close']
    
    in_zone = 130 <= current_price <= 140
    rsi_oversold = latest['RSI'] < 35
    volume_shrink = latest['Volume'] < latest['Volume_MA20'] * 0.9
    
    # 企稳信号
    body = abs(latest['Close'] - latest['Open'])
    lower_shadow = min(latest['Close'], latest['Open']) - latest['Low']
    stabilization = lower_shadow > body * 1.2 or latest['Close'] > latest['Open']
    
    triggered = in_zone and (rsi_oversold or stabilization) and volume_shrink
    
    return triggered, {
        "plan": "A",
        "name": "强支撑位买入",
        "price": round(current_price, 2),
        "zone": "$130-140",
        "rsi": round(latest['RSI'], 1),
        "volume_ok": volume_shrink,
        "stabilization": stabilization,
        "triggered": triggered
    }

def check_plan_b_breakout(df):
    """
    方案B: 突破买入 $170+
    条件: 放量突破 + RSI>50 + MACD金叉
    """
    if len(df) < 20:
        return False, {}
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    current_price = latest['Close']
    
    breakout = current_price > 170
    volume_surge = latest['Volume'] > latest['Volume_MA20'] * 1.3
    rsi_strong = latest['RSI'] > 50
    macd_golden = latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']
    
    triggered = breakout and volume_surge and (rsi_strong or macd_golden)
    
    return triggered, {
        "plan": "B",
        "name": "突破追涨买入",
        "price": round(current_price, 2),
        "breakout": breakout,
        "volume_surge": volume_surge,
        "rsi": round(latest['RSI'], 1),
        "macd_golden": macd_golden,
        "triggered": triggered
    }

def check_plan_c_extreme(df):
    """
    方案C: 极端恐慌 $110-120
    历史大底区间，适合逆向投资者
    """
    if len(df) < 10:
        return False, {}
    
    latest = df.iloc[-1]
    current_price = latest['Close']
    
    in_extreme_zone = 110 <= current_price <= 120
    rsi_extreme = latest['RSI'] < 30
    
    triggered = in_extreme_zone and rsi_extreme
    
    return triggered, {
        "plan": "C",
        "name": "极端恐慌抄底",
        "price": round(current_price, 2),
        "zone": "$110-120",
        "rsi": round(latest['RSI'], 1),
        "triggered": triggered
    }

def format_alert(plan, details):
    if plan == "A":
        lines = [
            "🎯 **BABA 方案A - 强支撑位买入信号**",
            "",
            f"📉 **价格**: ${details['price']} (进入{details['zone']}支撑区)",
            f"📊 **RSI**: {details['rsi']}",
            f"✅ **企稳信号**: {'出现' if details['stabilization'] else '观察中'}",
            "",
            "💡 **买入建议**:",
            "  • 买入区间: $130 - $140",
            "  • 建议仓位: 20% (轻仓试探)",
            "  • 止损位: $120",
            "  • 目标位: $160 / $180",
            "",
            "⚠️ **风险提示**:",
            "  • BABA基本面承压，盈利下滑51.8%",
            "  • 机构持仓仅11.8%，缺乏大资金支撑",
            "  • 中概股政策风险、地缘政治风险",
            "  • 建议严格止损，控制仓位"
        ]
    elif plan == "B":
        lines = [
            "🚀 **BABA 方案B - 突破买入信号**",
            "",
            f"📈 **价格**: ${details['price']} (突破$170)",
            f"📊 **RSI**: {details['rsi']}",
            f"📈 **成交量**: {'放量' if details['volume_surge'] else '正常'}",
            "",
            "💡 **买入建议**:",
            "  • 买入区间: $170 - $175",
            "  • 建议仓位: 30%",
            "  • 止损位: $160",
            "  • 目标位: $190 / $210",
            "",
            "✅ 趋势转多确认，但仍需关注基本面改善"
        ]
    elif plan == "C":
        lines = [
            "🔥 **BABA 方案C - 极端恐慌抄底信号**",
            "",
            f"📉 **价格**: ${details['price']} (跌至{details['zone']})",
            f"📊 **RSI**: {details['rsi']} (极度超卖)",
            "",
            "💡 **买入建议**:",
            "  • 买入区间: $110 - $120",
            "  • 建议仓位: 40% (可重仓)",
            "  • 止损位: $100",
            "  • 目标位: $150 / $180",
            "",
            "🎯 **历史大底区间**，适合逆向投资者",
            "⚠️ 需承受较大波动，建议分批建仓"
        ]
    
    lines.extend([
        "",
        f"⏰ 信号时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "---",
        "⚠️ 重要提醒: BABA为中概股，存在退市风险，请谨慎投资！"
    ])
    
    return "\n".join(lines)

def check_and_alert():
    print("=" * 60)
    print("BABA 买入时机监控")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("⚠️  风险提示: BABA基本面承压，投资需谨慎")
    print("=" * 60)
    
    df = get_baba_data(period="6mo", interval="1d")
    if df is None:
        print("❌ 获取数据失败")
        return None
    
    df = calculate_indicators(df)
    state = load_state()
    now_ts = int(datetime.now().timestamp())
    
    current_price = df.iloc[-1]['Close']
    latest = df.iloc[-1]
    
    print(f"\n当前价格: ${current_price:.2f}")
    print(f"MA20: ${latest['MA20']:.2f}")
    print(f"MA50: ${latest['MA50']:.2f}")
    print(f"RSI: {latest['RSI']:.1f}")
    print(f"成交量比: {latest['Volume']/latest['Volume_MA20']:.2f}x")
    
    # 检查三个方案
    results = []
    triggered_a, details_a = check_plan_a_support(df)
    results.append(("A", triggered_a, details_a))
    print(f"\n方案A (支撑$130-140): {'✅ 触发!' if triggered_a else '❌ 未触发'}")
    
    triggered_b, details_b = check_plan_b_breakout(df)
    results.append(("B", triggered_b, details_b))
    print(f"方案B (突破$170): {'✅ 触发!' if triggered_b else '❌ 未触发'}")
    
    triggered_c, details_c = check_plan_c_extreme(df)
    results.append(("C", triggered_c, details_c))
    print(f"方案C (极端$110-120): {'✅ 触发!' if triggered_c else '❌ 未触发'}")
    
    # 防重复提醒
    alerts = []
    for plan, triggered, details in results:
        alert_key = f"plan_{plan.lower()}_alerted"
        time_diff = now_ts - state.get('last_alert_time', 0)
        
        if triggered and (not state.get(alert_key) or time_diff > 12 * 3600):  # 12小时防重复
            state[alert_key] = True
            state['last_alert_time'] = now_ts
            state['last_alert_price'] = current_price
            state['alert_count'] = state.get('alert_count', 0) + 1
            
            alert_msg = format_alert(plan, details)
            alerts.append(alert_msg)
            print(f"\n🚨 方案{plan}提醒已生成!")
    
    # 价格离开区间后重置
    if current_price > 145:
        state['plan_a_alerted'] = False
    if current_price < 165:
        state['plan_b_alerted'] = False
    if current_price > 125:
        state['plan_c_alerted'] = False
    
    save_state(state)
    
    if alerts:
        full_alert = "\n\n" + "="*60 + "\n\n".join(alerts) + "\n" + "="*60
        print(full_alert)
        
        alert_file = "/Users/oneday/.openclaw/workspace/memory/baba_buyalert.txt"
        with open(alert_file, 'w') as f:
            f.write(full_alert)
        
        return full_alert
    else:
        print(f"\n\n📊 暂无买入信号")
        print(f"当前${current_price:.2f}，距离方案A(${130}-{140})还有{((current_price-140)/current_price*100):.1f}%")
        print("监控区间: $130-140(方案A) | $170+(方案B) | $110-120(方案C)")
    
    return None

if __name__ == "__main__":
    check_and_alert()
