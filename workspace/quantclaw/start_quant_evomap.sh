#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/oneday/.openclaw/workspace/quantclaw"
LOG_DIR="$ROOT/logs"
API_LOG="$LOG_DIR/api_server.log"
MINER_LOG="$LOG_DIR/agent_miner.log"
VALIDATOR_LOG="$LOG_DIR/agent_validator.log"
OPTIMIZER_LOG="$LOG_DIR/agent_optimizer.log"
API_PORT="${API_PORT:-8889}"
API_BASE="http://127.0.0.1:${API_PORT}/api/v1"

mkdir -p "$LOG_DIR"

echo "[1/4] Starting API gateway on :${API_PORT} ..."
if lsof -i ":${API_PORT}" >/dev/null 2>&1; then
  if curl -fsS "http://127.0.0.1:${API_PORT}/api/v1/stats" >/dev/null 2>&1; then
    echo "  - Quant EvoMap API already running on :${API_PORT}, skip API start."
  else
    echo "  - Port ${API_PORT} is occupied by a non-Quant-EvoMap service."
    echo "    Please stop that process or run with another port, e.g. API_PORT=8891 $0"
    exit 1
  fi
else
  python3 -m uvicorn api_server:app --host 127.0.0.1 --port "${API_PORT}" --app-dir "$ROOT" >>"$API_LOG" 2>&1 &
  echo $! > "$ROOT/api_server.pid"
  sleep 2
fi

echo "[2/4] Starting evolver daemon ..."
python3 "$ROOT/evolver_daemon.py" start --db-path "$ROOT/evolution_hub.db"

echo "[3/4] Starting Miner/Validator/Optimizer agents ..."
if [ -f "$ROOT/agent_miner.pid" ] && kill -0 "$(cat "$ROOT/agent_miner.pid")" 2>/dev/null; then
  echo "  - Miner already running."
else
  python3 "$ROOT/agents/miner_agent.py" --agent-id miner_01 --api-base "$API_BASE" >>"$MINER_LOG" 2>&1 &
  echo $! > "$ROOT/agent_miner.pid"
fi

if [ -f "$ROOT/agent_validator.pid" ] && kill -0 "$(cat "$ROOT/agent_validator.pid")" 2>/dev/null; then
  echo "  - Validator already running."
else
  python3 "$ROOT/agents/validator_agent.py" --agent-id validator_01 --api-base "$API_BASE" >>"$VALIDATOR_LOG" 2>&1 &
  echo $! > "$ROOT/agent_validator.pid"
fi

if [ -f "$ROOT/agent_optimizer.pid" ] && kill -0 "$(cat "$ROOT/agent_optimizer.pid")" 2>/dev/null; then
  echo "  - Optimizer already running."
else
  python3 "$ROOT/agents/optimizer_agent.py" --agent-id optimizer_01 --api-base "$API_BASE" >>"$OPTIMIZER_LOG" 2>&1 &
  echo $! > "$ROOT/agent_optimizer.pid"
fi

echo "[4/4] Quick health check ..."
curl -fsS "http://127.0.0.1:${API_PORT}/api/v1/stats" >/dev/null && echo "  - API ok"
python3 "$ROOT/evolver_daemon.py" status --db-path "$ROOT/evolution_hub.db" || true
echo
echo "Quant EvoMap started."
echo "Logs: $LOG_DIR"
