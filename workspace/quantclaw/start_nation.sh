#!/bin/bash
# Quant Genius Nation - 启动脚本

cd /Users/oneday/.openclaw/workspace/quantclaw

# 确保日志目录存在
mkdir -p logs

# 检查 Python 环境
echo "🧬 QUANT GENIUS NATION"
echo "======================"
echo ""

echo "Checking environment..."
python3 --version
echo ""

# 运行模式选择
case "${1:-single}" in
    single)
        echo "Mode: SINGLE CYCLE"
        echo ""
        python3 quant_genius_nation.py --mode single
        ;;
    continuous)
        echo "Mode: CONTINUOUS (Daemon)"
        echo "Press Ctrl+C to stop"
        echo ""
        python3 evolution_daemon.py
        ;;
    status)
        echo "Mode: STATUS CHECK"
        echo ""
        if [ -f logs/daemon_status.json ]; then
            cat logs/daemon_status.json | python3 -m json.tool
        else
            echo "No status file found. Daemon may not be running."
        fi
        ;;
    mine)
        echo "Mode: MATERIAL MINING ONLY"
        echo ""
        python3 data_source_expansion.py
        ;;
    report)
        echo "Mode: GENERATE REPORT"
        echo ""
        if [ -f logs/evolution_history.jsonl ]; then
            echo "Recent cycles:"
            tail -20 logs/evolution_history.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    d = json.loads(line)
    print(f\"Cycle {d['cycle']}: {d['result'].get('success', False)} ({d['duration']:.0f}s)\")
"
        fi
        ;;
    *)
        echo "Usage: $0 [single|continuous|status|mine|report]"
        echo ""
        echo "Commands:"
        echo "  single      - Run one evolution cycle"
        echo "  continuous  - Start 24x7 daemon"
        echo "  status      - Check daemon status"
        echo "  mine        - Mine materials only"
        echo "  report      - Show evolution report"
        exit 1
        ;;
esac
