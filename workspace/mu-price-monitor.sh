#!/bin/bash
# MU交易监控脚本

PRICE_FILE="/tmp/mu_price.json"
STATE_FILE="$HOME/.openclaw/workspace/mu-monitor-state.json"
LOG_FILE="$HOME/.openclaw/workspace/mu-monitor.log"

# 获取MU价格
fetch_price() {
    # 使用yfinance或类似方式获取
    python3 << 'PYEOF'
import json
try:
    import yfinance as yf
    ticker = yf.Ticker("MU")
    data = ticker.history(period="1d", interval="1m")
    if not data.empty:
        current = data['Close'].iloc[-1]
        info = {
            "symbol": "MU",
            "price": round(current, 2),
            "timestamp": str(data.index[-1])
        }
        print(json.dumps(info))
    else:
        print(json.dumps({"error": "No data"}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
PYEOF
}

# 检查关键点位
check_levels() {
    local price=$1
    local alerts=()
    
    if (( $(echo "$price <= 400" | bc -l) )) && (( $(echo "$price > 395" | bc -l) )); then
        alerts+=("💚 入场机会: 价格$price接近$400建仓点")
    fi
    
    if (( $(echo "$price <= 390" | bc -l) )) && (( $(echo "$price > 385" | bc -l) )); then
        alerts+=("💚 加仓机会: 价格$price接近$390加仓点")
    fi
    
    if (( $(echo "$price <= 380" | bc -l) )); then
        alerts+=("🚨 止损警告: 价格跌破$380，考虑减仓")
    fi
    
    if (( $(echo "$price >= 414" | bc -l) )) && (( $(echo "$price < 420" | bc -l) )); then
        alerts+=("📊 观察突破: 价格触及$414阻力位")
    fi
    
    if (( $(echo "$price >= 455" | bc -l) )); then
        alerts+=("🚀 突破信号: 价格突破$455，可考虑追买")
    fi
    
    printf '%s\n' "${alerts[@]}"
}

# 记录日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 主逻辑
main() {
    log "开始检查MU价格..."
    
    price_data=$(fetch_price)
    
    if echo "$price_data" | grep -q "error"; then
        log "获取价格失败: $price_data"
        exit 1
    fi
    
    price=$(echo "$price_data" | python3 -c "import json,sys; print(json.load(sys.stdin)['price'])")
    
    log "当前价格: $price"
    
    # 检查关键点位
    alerts=$(check_levels "$price")
    
    if [ -n "$alerts" ]; then
        echo "$alerts"
        log "触发提醒: $alerts"
    else
        log "价格$price未触及关键点位"
    fi
    
    # 更新状态文件
    python3 << PYEOF
import json
import datetime

try:
    with open("$STATE_FILE", "r") as f:
        state = json.load(f)
    
    state["currentPrice"] = $price
    state["lastCheck"] = datetime.datetime.now().isoformat()
    state["checkCount"] = state.get("checkCount", 0) + 1
    
    with open("$STATE_FILE", "w") as f:
        json.dump(state, f, indent=2)
except Exception as e:
    print(f"更新状态失败: {e}")
PYEOF
}

main "$@"
