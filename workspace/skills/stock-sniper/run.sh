#!/bin/bash
# 股票狙击手快速启动脚本

cd "$(dirname "$0")"

# 检查参数
if [ $# -eq 0 ]; then
    echo "🎯 股票狙击手 - 快速启动"
    echo ""
    echo "使用方法:"
    echo "  ./run.sh scan              # 扫描市场异动"
    echo "  ./run.sh analyze 000001    # 分析指定股票"
    echo "  ./run.sh analyze 000001 平安银行  # 分析指定股票（带名称）"
    echo ""
    exit 1
fi

COMMAND=$1

if [ "$COMMAND" = "scan" ]; then
    echo "🚀 启动市场异动扫描..."
    python3 scripts/stock_sniper.py --scan --top 8
elif [ "$COMMAND" = "analyze" ]; then
    CODE=$2
    NAME=$3
    if [ -z "$CODE" ]; then
        echo "❌ 请提供股票代码"
        exit 1
    fi
    echo "🚀 分析股票 $CODE ${NAME:+($NAME)}..."
    if [ -z "$NAME" ]; then
        python3 scripts/stock_sniper.py --code "$CODE"
    else
        python3 scripts/stock_sniper.py --code "$CODE" --name "$NAME"
    fi
else
    echo "❌ 未知命令: $COMMAND"
    echo "可用命令: scan, analyze"
    exit 1
fi
