#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/oneday/.openclaw/workspace/quantclaw"

stop_pid_file() {
  local pid_file="$1"
  local name="$2"
  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file")"
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 1
      kill -9 "$pid" 2>/dev/null || true
      echo "Stopped $name (pid=$pid)"
    else
      echo "$name not running (stale pid: $pid)"
    fi
    rm -f "$pid_file"
  else
    echo "$name pid file not found"
  fi
}

echo "[1/3] Stopping agents ..."
stop_pid_file "$ROOT/agent_miner.pid" "miner"
stop_pid_file "$ROOT/agent_validator.pid" "validator"
stop_pid_file "$ROOT/agent_optimizer.pid" "optimizer"

echo "[2/3] Stopping evolver daemon ..."
python3 "$ROOT/evolver_daemon.py" stop --db-path "$ROOT/evolution_hub.db" || true

echo "[3/3] Stopping API gateway ..."
stop_pid_file "$ROOT/api_server.pid" "api_server"

echo "Quant EvoMap stopped."
