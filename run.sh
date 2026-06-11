#!/usr/bin/env bash
# RoboPlanner (AI20K-162) - chay showcase web 1 cham
set -euo pipefail
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"

if [ ! -x ".venv/bin/python" ]; then
  echo "[1/3] Tao venv..."
  "$PY" -m venv .venv
fi
if [ ! -f ".venv/.deps_ok" ]; then
  echo "[2/3] Cai thu vien lan dau (~1-2 phut)..."
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
  touch .venv/.deps_ok
fi
[ -f .env ] || echo "[!] Chua co .env - Demo nhanh van chay; Chay that can GEMINI_API_KEY (cp .env.example .env)."

echo "[3/3] http://localhost:8000  - Ctrl+C de dung."
.venv/bin/python -m uvicorn src.main:app --port 8000 &
SVPID=$!
sleep 4
( command -v open >/dev/null 2>&1 && open http://localhost:8000 ) \
  || ( command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8000 ) || true
wait $SVPID
