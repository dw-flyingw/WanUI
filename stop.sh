#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$SCRIPT_DIR/.streamlit.pid"

if [ ! -f "$PIDFILE" ]; then
    echo "WanUI is not running (no PID file)"
    exit 0
fi

PID=$(cat "$PIDFILE")
if kill -0 "$PID" 2>/dev/null; then
    echo "Stopping WanUI (PID $PID)..."
    kill "$PID"
    # Wait up to 10 seconds for graceful shutdown
    for i in $(seq 1 10); do
        if ! kill -0 "$PID" 2>/dev/null; then
            break
        fi
        sleep 1
    done
    # Force kill if still running
    if kill -0 "$PID" 2>/dev/null; then
        echo "Force killing..."
        kill -9 "$PID"
    fi
    echo "WanUI stopped"
else
    echo "WanUI is not running (stale PID $PID)"
fi

rm -f "$PIDFILE"
