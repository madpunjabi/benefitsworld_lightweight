#!/usr/bin/env bash
# Starts backend (:8000), frontend-agent (:5173), and frontend-lab (:5174).
# Ctrl-C stops all three.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$ROOT_DIR/backend/.venv" ]; then
  echo "Creating backend virtualenv..."
  python3 -m venv "$ROOT_DIR/backend/.venv"
  "$ROOT_DIR/backend/.venv/bin/pip" install --quiet --upgrade pip
  "$ROOT_DIR/backend/.venv/bin/pip" install --quiet -r "$ROOT_DIR/backend/requirements.txt"
fi

if [ ! -d "$ROOT_DIR/frontend-agent/node_modules" ]; then
  echo "Installing frontend-agent dependencies..."
  (cd "$ROOT_DIR/frontend-agent" && npm install --no-audit --no-fund)
fi

if [ ! -d "$ROOT_DIR/frontend-lab/node_modules" ]; then
  echo "Installing frontend-lab dependencies..."
  (cd "$ROOT_DIR/frontend-lab" && npm install --no-audit --no-fund)
fi

PIDS=()
cleanup() {
  echo "Stopping..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

(cd "$ROOT_DIR/backend" && ./.venv/bin/uvicorn app.main:app --port 8000) &
PIDS+=($!)

(cd "$ROOT_DIR/frontend-agent" && npm run dev) &
PIDS+=($!)

(cd "$ROOT_DIR/frontend-lab" && npm run dev) &
PIDS+=($!)

echo "backend:        http://localhost:8000"
echo "frontend-agent: http://localhost:5173"
echo "frontend-lab:   http://localhost:5174"

wait
