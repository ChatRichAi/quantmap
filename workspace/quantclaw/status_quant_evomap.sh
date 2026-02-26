#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/oneday/.openclaw/workspace/quantclaw"
API_PORT="${API_PORT:-8889}"

check_pid() {
  local pid_file="$1"
  local name="$2"
  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      echo "$name: running (pid=$pid)"
    else
      echo "$name: stale pid file (pid=$pid)"
    fi
  else
    echo "$name: not running"
  fi
}

echo "=== Quant EvoMap Status ==="
check_pid "$ROOT/api_server.pid" "api_server"
check_pid "$ROOT/agent_miner.pid" "agent_miner"
check_pid "$ROOT/agent_validator.pid" "agent_validator"
check_pid "$ROOT/agent_optimizer.pid" "agent_optimizer"

echo
python3 "$ROOT/evolver_daemon.py" status --db-path "$ROOT/evolution_hub.db" || true

echo
if curl -fsS "http://127.0.0.1:${API_PORT}/api/v1/stats" >/dev/null 2>&1; then
  echo "api_health: ok (:${API_PORT})"
else
  echo "api_health: failed (:${API_PORT})"
fi
