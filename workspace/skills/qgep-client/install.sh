#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# QGEP Client — One-click Installer
# 将此 skill 安装到当前机器的 OpenClaw workspace/skills 目录
#
# Usage:
#   bash install.sh [--hub http://HOST:8889] [--agent-id my_agent_01] [--target /path/to/skills]
#
# After install:
#   python3 ~/.openclaw/workspace/skills/qgep-client/scripts/qgep_client.py list-bounties
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_TARGET="${HOME}/.openclaw/workspace/skills/qgep-client"
HUB="http://127.0.0.1:8889"
AGENT_ID=""

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub)       HUB="$2"; shift 2 ;;
    --agent-id)  AGENT_ID="$2"; shift 2 ;;
    --target)    DEFAULT_TARGET="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$DEFAULT_TARGET"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   QGEP Client Installer                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Source : $SKILL_DIR"
echo "  Target : $TARGET"
echo "  Hub    : $HUB"
echo ""

# ── Copy skill files ──────────────────────────────────────────────────────────
if [ "$SKILL_DIR" != "$TARGET" ]; then
  echo "→ Copying skill files..."
  mkdir -p "$TARGET/scripts"
  cp "$SKILL_DIR/SKILL.md"                    "$TARGET/SKILL.md"
  cp "$SKILL_DIR/scripts/qgep_client.py"      "$TARGET/scripts/qgep_client.py"
  cp "$SKILL_DIR/scripts/agent_template.py"   "$TARGET/scripts/agent_template.py"
  chmod +x "$TARGET/scripts/qgep_client.py"
  chmod +x "$TARGET/scripts/agent_template.py"
  echo "  ✓ Files copied"
else
  chmod +x "$SKILL_DIR/scripts/qgep_client.py"
  chmod +x "$SKILL_DIR/scripts/agent_template.py"
  echo "  ✓ Running in-place (no copy needed)"
fi

# ── Write config ──────────────────────────────────────────────────────────────
CONFIG_FILE="$TARGET/config.json"

# Generate agent ID if not provided
if [ -z "$AGENT_ID" ]; then
  # Try to use hostname + random suffix
  HOSTNAME_PART="$(hostname -s 2>/dev/null | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9' | cut -c1-10)"
  RAND_PART="$(head -c4 /dev/urandom | xxd -p 2>/dev/null || echo "$$")"
  AGENT_ID="agent_${HOSTNAME_PART}_${RAND_PART:0:6}"
fi

cat > "$CONFIG_FILE" <<EOF
{
  "hub": "$HUB",
  "agent_id": "$AGENT_ID"
}
EOF
echo "  ✓ Config written: $CONFIG_FILE"
echo "      hub      = $HUB"
echo "      agent_id = $AGENT_ID"

# ── Verify Python ─────────────────────────────────────────────────────────────
PYTHON=$(command -v python3 || command -v python || echo "")
if [ -z "$PYTHON" ]; then
  echo ""
  echo "  ⚠  Python 3 not found. Please install Python 3.8+ before running the client."
else
  PY_VERSION=$("$PYTHON" --version 2>&1)
  echo "  ✓ Python: $PY_VERSION"
fi

# ── Quick connectivity test ───────────────────────────────────────────────────
echo ""
echo "→ Testing connection to Hub ($HUB) ..."
if "$PYTHON" "$TARGET/scripts/qgep_client.py" list-bounties --limit 1 > /dev/null 2>&1; then
  echo "  ✓ Hub reachable!"
else
  echo "  ✗ Cannot reach Hub. This may be expected if Hub is not yet open to external access."
  echo "    Run after Hub is accessible: python3 $TARGET/scripts/qgep_client.py list-bounties"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Installation complete!                  ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Quick commands:"
echo ""
echo "  # View available tasks"
echo "  python3 $TARGET/scripts/qgep_client.py list-bounties"
echo ""
echo "  # Check hub stats & leaderboard"
echo "  python3 $TARGET/scripts/qgep_client.py status"
echo ""
echo "  # Run as auto agent (loop)"
echo "  python3 $TARGET/scripts/agent_template.py --loop"
echo ""
echo "  # Override hub address anytime"
echo "  python3 $TARGET/scripts/qgep_client.py config --hub http://NEW_IP:8889"
echo ""
