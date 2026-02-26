#!/bin/bash
# Quant EvoMap UI 启动脚本

cd "$(dirname "$0")"

echo "🚀 Starting Quant EvoMap UI..."

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# 启动开发服务器
echo "✨ Starting Next.js dev server on port 3000..."
npm run dev

echo ""
echo "🌐 访问地址 / Access URLs:"
echo "   中文: http://localhost:3000/zh/evomap"
echo "   English: http://localhost:3000/en/evomap"
