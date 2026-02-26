#!/bin/bash
#
# Setup script for Auto-Evolve skill
# 设置自动进化系统的 cron 任务

EVOLVE_DIR="/Users/oneday/.openclaw/workspace/skills/auto-evolve"
SCRIPTS_DIR="$EVOLVE_DIR/scripts"

echo "╔══════════════════════════════════════════════════╗"
echo "║      Auto-Evolve System Setup                   ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# 检查 Node.js
echo "→ Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "✗ Node.js not found. Please install Node.js first."
    exit 1
fi
echo "✓ Node.js found: $(node --version)"

# 创建必要的目录
echo "→ Creating directories..."
mkdir -p "$EVOLVE_DIR"/{scripts,genes,capsules,events/failures,events/published}
echo "✓ Directories created"

# 初始化本地 Gene 库
echo "→ Initializing local gene library..."
node "$SCRIPTS_DIR/gene-matcher.js" 2>/dev/null || true
echo "✓ Gene library initialized"

# 测试运行一次
echo "→ Testing evolution cycle..."
node "$SCRIPTS_DIR/evolver.js" --once
echo ""

# 询问是否设置 cron
echo "═══════════════════════════════════════════════════"
echo ""
echo "Setup complete! Next steps:"
echo ""
echo "1. Test the system:"
echo "   node $SCRIPTS_DIR/evolver.js --test"
echo ""
echo "2. Run single cycle:"
echo "   node $SCRIPTS_DIR/evolver.js --once"
echo ""
echo "3. Start continuous monitoring:"
echo "   node $SCRIPTS_DIR/evolver.js --loop"
echo ""
echo "4. Or add to crontab for automatic execution every 5 minutes:"
echo "   crontab -e"
echo "   # Add this line:"
echo "   */5 * * * * cd $EVOLVE_DIR && node scripts/evolver.js --once >> events/cron.log 2>&1"
echo ""
echo "═══════════════════════════════════════════════════"
