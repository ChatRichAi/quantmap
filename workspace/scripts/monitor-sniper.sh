#!/bin/bash
# EvoMap Sniper 监控脚本

LOG_FILE="$HOME/.openclaw/workspace/scripts/sniper.log"
PID_FILE="$HOME/.openclaw/workspace/scripts/sniper.pid"
ALERT_FILE="$HOME/.openclaw/workspace/scripts/sniper_alert.txt"

# 检查进程是否存活
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "[$(date)] ⚠️ Sniper 进程已停止，正在重启..." >> "$ALERT_FILE"
        cd "$HOME/.openclaw/workspace/scripts"
        nohup node smart-bounty-sniper.js > sniper.log 2>&1 &
        echo $! > "$PID_FILE"
        echo "[$(date)] ✅ Sniper 已重启，PID: $(cat "$PID_FILE")" >> "$ALERT_FILE"
    fi
fi

# 检查抢单成功
task_claimed=$(grep -c "🎉" "$LOG_FILE" 2>/dev/null || echo "0")
if [ "$task_claimed" -gt 0 ]; then
    last_claim=$(grep "🎉" "$LOG_FILE" | tail -1)
    echo "[$(date)] 🎉 抢单成功! $last_claim" >> "$ALERT_FILE"
fi

# 统计信息
total_scans=$(grep -c "发现.*任务" "$LOG_FILE" 2>/dev/null || echo "0")
echo "[$(date)] 📊 统计: 发现任务次数=$total_scans, 抢单成功=$task_claimed" >> "$ALERT_FILE"

# 保持日志文件大小
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null || echo 0) -gt 10485760 ]; then
    # 超过10MB，轮转日志
    mv "$LOG_FILE" "${LOG_FILE}.old"
    touch "$LOG_FILE"
fi
