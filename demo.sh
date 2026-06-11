#!/usr/bin/env bash
# RoboPlanner - chi phat lai (Demo nhanh)
set -euo pipefail
cd "$(dirname "$0")/frontend"
echo "Showcase (chi Demo nhanh) tai http://localhost:5500 - Ctrl+C de dung."
"${PYTHON:-python3}" -m http.server 5500 &
SVPID=$!
sleep 3
( command -v open >/dev/null 2>&1 && open http://localhost:5500 ) \
  || ( command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:5500 ) || true
wait $SVPID
