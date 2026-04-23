#!/usr/bin/env bash
# start_api.sh — keeps the Mealy API alive in a background tmux session
# for up to 36 hours. Safe to run multiple times; won't start a duplicate.
#
# Usage:
#   ./start_api.sh          — start (or reattach if already running)
#   ./start_api.sh stop     — kill the background session
#   ./start_api.sh status   — check if running
#   ./start_api.sh logs     — tail the live log

set -euo pipefail

SESSION="mealy-api"
LOG="$(dirname "$0")/api.log"
PYTHON="$(dirname "$0")/venv_archive/bin/python3"
SCRIPT="$(dirname "$0")/app.py"
MAX_HOURS=36

cd "$(dirname "$0")"

case "${1:-start}" in

  stop)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      tmux kill-session -t "$SESSION"
      echo "[mealy] API session '$SESSION' stopped."
    else
      echo "[mealy] No session named '$SESSION' is running."
    fi
    exit 0
    ;;

  status)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "[mealy] API is RUNNING in tmux session '$SESSION'."
      echo "[mealy] Tail logs: ./start_api.sh logs"
      echo "[mealy] Attach:   tmux attach -t $SESSION"
      echo "[mealy] URL:      http://localhost:5001"
    else
      echo "[mealy] API is NOT running."
    fi
    exit 0
    ;;

  logs)
    tail -f "$LOG"
    exit 0
    ;;

  start)
    if tmux has-session -t "$SESSION" 2>/dev/null; then
      echo "[mealy] Already running — session '$SESSION' exists."
      echo "[mealy] http://localhost:5001 is live."
      echo "[mealy] Run './start_api.sh stop' to kill it."
      exit 0
    fi

    echo "[mealy] Starting API in background tmux session '$SESSION'..."
    echo "[mealy] Will stay alive for up to ${MAX_HOURS} hours."
    echo "[mealy] Log → $LOG"

    # Start detached tmux session; auto-kill after MAX_HOURS via timeout
    tmux new-session -d -s "$SESSION" -x 220 -y 50 \
      "timeout ${MAX_HOURS}h $PYTHON $SCRIPT 2>&1 | tee $LOG; echo '[mealy] Session ended.'"

    # Wait up to 15s for Flask to respond
    echo -n "[mealy] Waiting for /health"
    for i in $(seq 1 30); do
      if curl -sf http://localhost:5001/health > /dev/null 2>&1; then
        echo " — online!"
        echo "[mealy] API ready → http://localhost:5001"
        echo "[mealy] Commands:"
        echo "         ./start_api.sh status   — check"
        echo "         ./start_api.sh logs     — live log"
        echo "         ./start_api.sh stop     — kill"
        exit 0
      fi
      echo -n "."
      sleep 0.5
    done

    echo ""
    echo "[mealy] Flask started but /health hasn't responded yet (models may still be loading)."
    echo "[mealy] Check: ./start_api.sh logs"
    echo "[mealy] URL:   http://localhost:5001"
    ;;

  *)
    echo "Usage: $0 [start|stop|status|logs]"
    exit 1
    ;;
esac
