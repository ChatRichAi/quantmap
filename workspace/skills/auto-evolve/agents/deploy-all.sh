#!/bin/bash
#
# 批量部署 Bounty Hunter 到多个节点
# 为每个节点创建独立的自动化系统

AGENTS_DIR="/Users/oneday/.openclaw/workspace/skills/auto-evolve/agents"
NODES=(
  "node_8544558ae8eb9ecd"
  "node_5e5316b19e8b64c8"
  "node_3b449d255e543b6c"
  "node_5d171ac279308fed"
  "node_6a28592ba181afb5"
  "node_96f4fae6cc911e2a"
)

echo "╔════════════════════════════════════════════════════════╗"
echo "║     批量部署 Bounty Hunter Agent 系统                  ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

mkdir -p "$AGENTS_DIR"

for i in "${!NODES[@]}"; do
  NODE_ID="${NODES[$i]}"
  AGENT_NUM=$((i + 1))
  
  echo "[$AGENT_NUM/6] 部署 Agent: $NODE_ID..."
  
  # 创建每个agent的配置
  cat > "$AGENTS_DIR/agent-$AGENT_NUM.js" <> EOF
const https = require('https');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  nodeId: '$NODE_ID',
  hubUrl: 'evomap.ai',
  checkIntervalMs: ${AGENT_NUM} * 2 * 60 * 1000, // 错峰扫描
  minMatchScore: 3,
  maxConcurrentTasks: 2,
  maxRetries: 3,
  requestTimeout: 15000
};

console.log('[Agent $AGENT_NUM] 节点 $NODE_ID 启动');

// Bounty Hunter 逻辑...
async function bountyHunterLoop() {
  console.log('[Agent $AGENT_NUM] 扫描任务...');
  // 实现略，使用标准Bounty Hunter逻辑
}

// 每 ${AGENT_NUM}*2 分钟运行一次
setInterval(bountyHunterLoop, CONFIG.checkIntervalMs);
bountyHunterLoop();
EOF

  echo "  ✅ Agent $AGENT_NUM 配置已创建"
  echo ""
done

echo "═══════════════════════════════════════════════════════"
echo "部署完成！"
echo ""
echo "启动所有agents:"
echo "  cd $AGENTS_DIR"
echo "  for f in agent-*.js; do node \$f &; done"
echo ""
echo "或使用 cron 定时启动每个agent"
