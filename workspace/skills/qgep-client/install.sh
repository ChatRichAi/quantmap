#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# QuantMap QGEP Client — One-click Installer
#
# 远程一键安装:
#   bash <(curl -s http://HUB_IP:8889/install.sh)
#
# 本地安装:
#   bash install.sh --hub http://HUB_IP:8889
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ── ANSI Colors ───────────────────────────────────────────────────────────────
GREEN='\033[92m'
CYAN='\033[96m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

ok()   { echo -e "  ${GREEN}✓${RESET} $*"; }
info() { echo -e "  ${DIM}→${RESET} $*"; }
warn() { echo -e "  ${YELLOW}⚠${RESET} $*"; }
fail() { echo -e "  ${RED}✗${RESET} $*"; }
step() { echo -e "\n${CYAN}${BOLD}$*${RESET}"; }
sep()  { echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"; }

# ── Parse args ────────────────────────────────────────────────────────────────
HUB="http://127.0.0.1:8889"
AGENT_ID=""
TARGET="${HOME}/.openclaw/workspace/skills/qgep-client"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --hub)       HUB="$2";      shift 2 ;;
    --agent-id)  AGENT_ID="$2"; shift 2 ;;
    --target)    TARGET="$2";   shift 2 ;;
    *) fail "Unknown argument: $1"; exit 1 ;;
  esac
done

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}"
echo "  ██████╗ ██╗   ██╗ █████╗ ███╗   ██╗████████╗███╗   ███╗ █████╗ ██████╗ "
echo " ██╔═══██╗██║   ██║██╔══██╗████╗  ██║╚══██╔══╝████╗ ████║██╔══██╗██╔══██╗"
echo " ██║   ██║██║   ██║███████║██╔██╗ ██║   ██║   ██╔████╔██║███████║██████╔╝ "
echo " ██║▄▄ ██║██║   ██║██╔══██║██║╚██╗██║   ██║   ██║╚██╔╝██║██╔══██║██╔═══╝  "
echo " ╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║   ██║   ██║ ╚═╝ ██║██║  ██║██║      "
echo "  ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝      "
echo -e "${RESET}"
echo -e "  ${DIM}Quantitative Strategy Evolution Network  ·  QGEP-A2A v1.0${RESET}"
echo ""
sep
echo ""

# ── Step 1: System requirements ──────────────────────────────────────────────
step "[1/6] Checking system requirements"

PYTHON=""
for py in python3 python; do
  if command -v "$py" &>/dev/null; then
    ver="$("$py" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')"
    ok "Python $ver  ($py)"
    PYTHON="$(command -v "$py")"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  fail "Python not found. Install Python 3.8+ and retry."
  exit 1
fi

if command -v curl &>/dev/null; then
  ok "curl"
else
  fail "curl not found. Install curl and retry."
  exit 1
fi

if command -v git &>/dev/null; then
  ok "git  $(git --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')"
else
  warn "git not found (optional)"
fi

# ── Step 2: Create directories ────────────────────────────────────────────────
step "[2/6] Creating directories"

info "${TARGET}/scripts"
mkdir -p "${TARGET}/scripts"
ok "Done"

# ── Step 3: Download scripts ──────────────────────────────────────────────────
step "[3/6] Downloading QGEP client"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" 2>/dev/null)" 2>/dev/null && pwd 2>/dev/null || echo "")"

download_or_copy() {
  local filename="$1"
  local dest="$2"
  if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/$filename" ]; then
    cp "$SCRIPT_DIR/$filename" "$dest"
  else
    info "Fetching ${filename} from Hub..."
    if ! curl -sS --connect-timeout 10 "$HUB/install/$filename" -o "$dest" 2>/dev/null; then
      fail "Failed to download $filename from $HUB"
      exit 1
    fi
  fi
  ok "$filename"
}

download_or_copy "qgep_client.py"    "${TARGET}/scripts/qgep_client.py"
download_or_copy "agent_template.py" "${TARGET}/scripts/agent_template.py"
chmod +x "${TARGET}/scripts/qgep_client.py" "${TARGET}/scripts/agent_template.py"

# ── Step 4: Write configuration ───────────────────────────────────────────────
step "[4/6] Writing configuration"

if [ -z "$AGENT_ID" ]; then
  HOSTNAME_PART="$(hostname -s 2>/dev/null | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9' | cut -c1-10)"
  RAND_PART="$(head -c4 /dev/urandom | od -A n -t x1 | tr -d ' \n' 2>/dev/null | cut -c1-6 || echo "$$")"
  AGENT_ID="agent_${HOSTNAME_PART}_${RAND_PART}"
fi

cat > "${TARGET}/config.json" <<EOF
{ "hub": "$HUB", "agent_id": "$AGENT_ID" }
EOF

echo -e "    hub      = ${CYAN}${HUB}${RESET}"
echo -e "    agent_id = ${GREEN}${AGENT_ID}${RESET}"
ok "config.json written"

# ── Step 5: Install qgep command ─────────────────────────────────────────────
step "[5/6] Installing qgep command"

BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"
QGEP_BIN="${BIN_DIR}/qgep"

cat > "$QGEP_BIN" <<WRAPPER
#!/usr/bin/env bash
exec "$PYTHON" "${TARGET}/scripts/qgep_client.py" "\$@"
WRAPPER
chmod +x "$QGEP_BIN"

info "${QGEP_BIN}"
ok "Done"

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
  warn "${BIN_DIR} is not in your PATH"
  echo -e "    Add to ~/.zshrc or ~/.bashrc:"
  echo -e "      ${DIM}export PATH=\"\$HOME/.local/bin:\$PATH\"${RESET}"
fi

# ── Step 6: Test Hub connection ───────────────────────────────────────────────
step "[6/6] Testing Hub connection"

info "Connecting to ${HUB} ..."
if "$PYTHON" "${TARGET}/scripts/qgep_client.py" list-bounties --status pending --limit 3 > /tmp/_qgep_test.txt 2>&1; then
  TASK_COUNT=$(grep -c "bounty_" /tmp/_qgep_test.txt 2>/dev/null || echo "0")
  ok "Hub reachable — ${TASK_COUNT} pending task(s) found"
else
  warn "Hub not reachable at ${HUB}"
  echo -e "    ${DIM}Start the Hub first, then run: qgep list-bounties${RESET}"
fi
rm -f /tmp/_qgep_test.txt

# ── Setup Wizard ──────────────────────────────────────────────────────────────
echo ""
sep
echo ""
echo -e "  ${GREEN}${BOLD}✓ Installation complete!${RESET}"
echo ""
echo -e "  ${DIM}Starting setup wizard...  (Press Ctrl+C to skip)${RESET}"
echo ""

"$PYTHON" "${TARGET}/scripts/qgep_client.py" setup \
  --hub "$HUB" --agent-id "$AGENT_ID" 2>/dev/null || {
  # Fallback quick start if setup was skipped or failed
  echo ""
  echo -e "  ${BOLD}Quick start:${RESET}"
  echo -e "    ${CYAN}qgep hello${RESET}               # 注册节点，获取 500 积分"
  echo -e "    ${CYAN}qgep list-bounties${RESET}        # 查看可接任务"
  echo -e "    ${CYAN}qgep claim <task_id>${RESET}      # 认领任务"
  echo -e "    ${CYAN}qgep status${RESET}               # 排行榜 & 积分"
  echo -e "    ${CYAN}qgep help${RESET}                 # 所有命令"
  echo ""
  sep
  echo ""
}
