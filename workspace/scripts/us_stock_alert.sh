#!/bin/bash
# 美股技术信号检测入口脚本
# 由cron触发，执行监控并发送通知

cd /Users/oneday/.openclaw/workspace/scripts
python3 us_stock_monitor.py

# 检查是否有新的提醒
ALERT_FILE="/Users/oneday/.openclaw/workspace/memory/stock_alert.txt"
if [ -f "$ALERT_FILE" ]; then
    # 读取提醒内容并输出(会被OpenClaw捕获)
    cat "$ALERT_FILE"
    # 删除已处理的提醒文件
    rm "$ALERT_FILE"
fi
