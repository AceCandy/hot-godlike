#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
BACKEND_PYTHON="${BACKEND_PYTHON:-$BACKEND_DIR/.venv/bin/python}"
FRONTEND_API_BASE_URL="${VITE_API_BASE_URL:-http://localhost:$BACKEND_PORT/api}"

BACKEND_PID=""
FRONTEND_PID=""
CLEANUP_STARTED=0

log() {
  printf '[dev] %s\n' "$*"
}

fail() {
  printf '[dev] ERROR: %s\n' "$*" >&2
  exit 1
}

is_running() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null
}

terminate_tree() {
  local pid="$1"
  local child=""

  if [[ -z "$pid" ]]; then
    return
  fi

  if command -v pgrep >/dev/null 2>&1; then
    for child in $(pgrep -P "$pid" 2>/dev/null || true); do
      terminate_tree "$child"
    done
  fi

  if is_running "$pid"; then
    kill "$pid" 2>/dev/null || true
  fi
}

cleanup() {
  if [[ "$CLEANUP_STARTED" -eq 1 ]]; then
    return
  fi
  CLEANUP_STARTED=1
  trap - INT TERM EXIT

  # Ctrl+C 或任一服务退出时，统一收尾两个子进程，避免遗留端口占用。
  terminate_tree "$FRONTEND_PID"
  terminate_tree "$BACKEND_PID"

  wait "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" 2>/dev/null || true
}

shutdown() {
  cleanup
  exit 0
}

check_requirements() {
  [[ -x "$BACKEND_PYTHON" ]] || fail "未找到后端虚拟环境。请先执行：cd backend && python3 -m venv .venv && source .venv/bin/activate && python -m pip install -e '.[dev]'"
  "$BACKEND_PYTHON" -c "import uvicorn" >/dev/null 2>&1 || fail "后端虚拟环境缺少 uvicorn。请先执行：cd backend && source .venv/bin/activate && python -m pip install -e '.[dev]'"

  command -v npm >/dev/null 2>&1 || fail "未找到 npm，请先安装 Node.js / npm。"
  [[ -d "$FRONTEND_DIR/node_modules" ]] || fail "前端依赖未安装。请先执行：cd frontend && npm install"
}

start_backend() {
  log "启动后端：http://$BACKEND_HOST:$BACKEND_PORT"
  (
    cd "$BACKEND_DIR"
    exec "$BACKEND_PYTHON" -m uvicorn app.main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT"
  ) &
  BACKEND_PID="$!"
}

start_frontend() {
  log "启动前端：npm run dev"
  log "前端 API 地址：$FRONTEND_API_BASE_URL"
  (
    cd "$FRONTEND_DIR"
    VITE_API_BASE_URL="$FRONTEND_API_BASE_URL" exec npm run dev
  ) &
  FRONTEND_PID="$!"
}

watch_processes() {
  while true; do
    if ! is_running "$BACKEND_PID"; then
      local exit_code=0
      wait "$BACKEND_PID" || exit_code="$?"
      fail "后端进程已退出，exit code=$exit_code"
    fi
    if ! is_running "$FRONTEND_PID"; then
      local exit_code=0
      wait "$FRONTEND_PID" || exit_code="$?"
      fail "前端进程已退出，exit code=$exit_code"
    fi
    sleep 1
  done
}

main() {
  check_requirements
  trap shutdown INT TERM
  trap cleanup EXIT
  start_backend
  start_frontend

  log "服务启动中。按 Ctrl+C 停止前后端。"
  log "后端：http://$BACKEND_HOST:$BACKEND_PORT"
  log "前端：查看 Vite 输出的 Local 地址，默认 http://127.0.0.1:5173"
  watch_processes
}

main "$@"
