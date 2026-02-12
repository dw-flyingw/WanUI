#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$SCRIPT_DIR/.streamlit.pid"

# Check if already running
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "WanUI is already running (PID $PID)"
        exit 1
    else
        echo "Removing stale PID file"
        rm -f "$PIDFILE"
    fi
fi

# Activate venv
source "$SCRIPT_DIR/.venv/bin/activate"

# Apply patches
echo "Checking patches..."
python "$SCRIPT_DIR/patch.py" status || python "$SCRIPT_DIR/patch.py" patch

# Start Streamlit in background
echo "Starting WanUI..."
nohup streamlit run "$SCRIPT_DIR/app.py" \
    --server.port=8560 \
    --server.address=0.0.0.0 \
    > "$SCRIPT_DIR/nohup.out" 2>&1 &

echo $! > "$PIDFILE"
echo "WanUI started (PID $!)"
echo "Logs: $SCRIPT_DIR/nohup.out"
