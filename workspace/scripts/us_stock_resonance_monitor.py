#!/usr/bin/env python3
"""
美股多周期K线共振突破监控
监控标的: MSFT, AMZN
监控周期: 15分钟 / 1小时 / 4小时 / 1日
信号类型: 多周期共振突破 (2个以上周期同时突破 = 共振)
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# 监控配置
WATCHLIST = {
    "MSFT": {"name": "微软", "ma_period": 20},
    "AMZN": {"name": "亚马逊", "ma_period": 20}
}

# 周期配置
TIMEFRAMES = {
    "15m": {"interval": "15m", "period": "5d", "weight": 1},
    "1h": {"interval": "1h", "period": "1mo", "weight": 2},
    "4h": {"interval": "1h", "period": "3mo", "weight": 3},  # 通过重采样模拟4h
    "1d": {"interval": "1d", "period": "6mo", "weight": 4}
}

STATE_FILE = "/Users/oneday/.openclaw/workspace/memory/stock_resonance_state.json"

def load_state():
    """加载上次的状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"last_alerts": {}, "breakout_history": {}}

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

def resample_to_4h(df):
    """将1小时数据重采样为4小时"""
    if df is None or len(df) == 0:
        return None
    df_4h = df.resample('4h').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    return df_4h

def calculate_ma(df, period=20):
    """计算移动平均线"""
    if df is None or len(df) < period:
        return None
    df['MA20'] = df['Close'].rolling(window=period).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA5'] = df['Close'].rolling(window=5).mean()
    return df

def detect_breakout(df, timeframe_name):
    """
    检测突破信号
    返回: (是否突破, 突破类型, 详细信息)
    """
    if df is None or len(df) < 5:
        return False, None, None
    
    df = calculate_ma(df)
    if df is None:
        return False, None, None
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    current_price = latest['Close']
    current_ma20 = latest['MA20']
    current_ma10 = latest['MA10']
    current_ma5 = latest['MA5']
    
    # 获取近期高低点
    recent_high = df['High'].tail(20).max()
    recent_low = df['Low'].tail(20).min()
    
    signals = []
    
    # 1. MA20突破 (价格站上20日均线)
    if current_price > current_ma20 and prev['Close'] <= prev['MA20']:
        signals.append({
            "type": "MA20突破",
            "strength": "medium",
            "price": round(current_price, 2),
            "ma20": round(current_ma20, 2),
            "description": f"价格上破MA20"
        })
    
    # 2. 多头排列 (MA5 > MA10 > MA20)
    if current_ma5 > current_ma10 > current_ma20:
        # 检查是否刚形成多头排列
        if not (prev['MA5'] > prev['MA10'] > prev['MA20']):
            signals.append({
                "type": "多头排列形成",
                "strength": "strong",
                "price": round(current_price, 2),
                "description": "MA5>MA10>MA20多头排列确立"
            })
    
    # 3. 前高突破 (突破20日高点)
    if current_price > recent_high * 0.995 and prev['Close'] <= recent_high:
        signals.append({
            "type": "前高突破",
            "strength": "strong",
            "price": round(current_price, 2),
            "high_20": round(recent_high, 2),
            "description": f"突破20日高点"
        })
    
    # 4. 放量上涨 (涨幅>2%且成交量放大)
    price_change = (current_price - prev['Close']) / prev['Close'] * 100
    avg_volume = df['Volume'].tail(20).mean()
    volume_ratio = latest['Volume'] / avg_volume if avg_volume > 0 else 0
    
    if price_change > 2 and volume_ratio > 1.3:
        signals.append({
            "type": "放量上涨",
            "strength": "medium",
            "price": round(current_price, 2),
            "change_pct": round(price_change, 2),
            "volume_ratio": round(volume_ratio, 2),
            "description": f"放量上涨+{price_change:.1f}%"
        })
    
    # 返回最强的信号
    if signals:
        # 按强度排序
        strength_order = {"strong": 3, "medium": 2, "weak": 1}
        signals.sort(key=lambda x: strength_order.get(x["strength"], 0), reverse=True)
        strongest = signals[0]
        return True, strongest["type"], strongest
    
    return False, None, None

def check_multi_timeframe_resonance(symbol, config):
    """
    检查多周期共振
    返回各周期信号和共振强度
    """
    print(f"\n🔍 分析 {symbol} ({config['name']}) 多周期信号...")
    
    results = {
        "symbol": symbol,
        "name": config['name'],
        "timeframes": {},
        "resonance_count": 0,
        "resonance_score": 0,
        "signals": []
    }
    
    # 获取各周期数据
    for tf_name, tf_config in TIMEFRAMES.items():
        print(f"  📊 获取 {tf_name} 数据...")
        
        if tf_name == "4h":
            # 4小时需要特殊处理：获取1小时数据然后重采样
            df_1h = get_stock_data(symbol, period="3mo", interval="1h")
            df = resample_to_4h(df_1h)
        else:
            df = get_stock_data(symbol, period=tf_config["period"], interval=tf_config["interval"])
        
        if df is None or len(df) < 5:
            results["timeframes"][tf_name] = {"error": "数据获取失败"}
            continue
        
        # 检测突破信号
        has_breakout, breakout_type, details = detect_breakout(df, tf_name)
        
        current_price = df.iloc[-1]['Close']
        
        tf_result = {
            "current_price": round(current_price, 2),
            "has_breakout": has_breakout,
            "breakout_type": breakout_type,
            "details": details,
            "weight": tf_config["weight"]
        }
        
        results["timeframes"][tf_name] = tf_result
        
        if has_breakout:
            results["resonance_count"] += 1
            results["resonance_score"] += tf_config["weight"]
            results["signals"].append({
                "timeframe": tf_name,
                "type": breakout_type,
                "details": details
            })
    
    # 判断共振级别
    if results["resonance_count"] >= 3:
        results["resonance_level"] = "🔥 强共振"
        results["should_alert"] = True
    elif results["resonance_count"] == 2:
        results["resonance_level"] = "⚡ 中等共振"
        results["should_alert"] = True
    else:
        results["resonance_level"] = "○ 无共振"
        results["should_alert"] = False
    
    return results

def check_all_stocks():
    """检查所有股票的共振信号"""
    all_results = []
    state = load_state()
    
    for symbol, config in WATCHLIST.items():
        result = check_multi_timeframe_resonance(symbol, config)
        all_results.append(result)
        
        # 打印结果
        print(f"\n  📈 {symbol} 多周期分析结果:")
        print(f"     信号周期数: {result['resonance_count']}/4")
        print(f"     共振强度: {result['resonance_level']}")
        print(f"     共振得分: {result['resonance_score']}")
        
        for tf, data in result['timeframes'].items():
            if isinstance(data, dict) and data.get('has_breakout'):
                print(f"     ✅ {tf}: {data['breakout_type']}")
    
    # 保存结果到状态
    state["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    state["latest_results"] = all_results
    save_state(state)
    
    return all_results

def format_resonance_alert(results):
    """格式化共振提醒消息"""
    resonance_results = [r for r in results if r.get("should_alert", False)]
    
    if not resonance_results:
        return None
    
    msg_lines = [
        "🚨 **多周期共振突破信号** 🚨",
        f"⏰ 检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        ""
    ]
    
    for r in resonance_results:
        msg_lines.append(f"📊 **{r['symbol']}** ({r['name']}) - {r['resonance_level']}")
        msg_lines.append(f"   共振得分: {r['resonance_score']}/10 | 信号周期: {r['resonance_count']}/4")
        msg_lines.append("")
        
        # 显示各周期信号
        for signal in r['signals']:
            tf = signal['timeframe']
            sig_type = signal['type']
            details = signal.get('details', {})
            price = details.get('price', 'N/A')
            msg_lines.append(f"   ✅ **{tf}**: {sig_type} @ ${price}")
        
        msg_lines.append("")
    
    msg_lines.append("---")
    msg_lines.append("💡 **共振信号说明**:")
    msg_lines.append("   • 2个周期同步 = 中等共振 ⚡")
    msg_lines.append("   • 3个周期以上同步 = 强共振 🔥")
    msg_lines.append("   • 周期越大(日线>小时)，信号越可靠")
    
    return "\n".join(msg_lines)

def main():
    """主函数"""
    print("=" * 60)
    print("📊 美股多周期K线共振突破监控")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📈 监控周期: 15分钟 | 1小时 | 4小时 | 1日")
    print("=" * 60)
    
    results = check_all_stocks()
    alert_msg = format_resonance_alert(results)
    
    print("\n" + "=" * 60)
    if alert_msg:
        print(alert_msg)
        print("=" * 60)
        
        # 将提醒写入文件
        alert_file = "/Users/oneday/.openclaw/workspace/memory/stock_resonance_alert.txt"
        with open(alert_file, 'w') as f:
            f.write(alert_msg)
        print(f"\n✅ 共振信号已保存到: {alert_file}")
    else:
        print("📊 暂无多周期共振突破信号")
        print("=" * 60)
    
    print("\n监控完成")

if __name__ == "__main__":
    main()
