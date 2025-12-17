#!/bin/bash
# Stop 24/7 Distributed Quant Analysis System

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

echo "Stopping 24/7 Distributed Quant Analysis System..."

if [ ! -f "$LOG_DIR/24x7.pid" ]; then
    echo "❌ PID file not found. System may not be running."
    exit 1
fi

PID=$(cat "$LOG_DIR/24x7.pid")

if ! ps -p $PID > /dev/null 2>&1; then
    echo "❌ Process not running (PID: $PID)"
    rm "$LOG_DIR/24x7.pid"
    exit 1
fi

echo "Sending SIGINT to process $PID..."
kill -INT $PID

# Wait for graceful shutdown (max 30 seconds)
for i in {1..30}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "✅ System stopped gracefully"
        rm "$LOG_DIR/24x7.pid"
        exit 0
    fi
    sleep 1
done

echo "⚠️  Process still running, sending SIGTERM..."
kill -TERM $PID
sleep 2

if ps -p $PID > /dev/null 2>&1; then
    echo "❌ Process still running, sending SIGKILL..."
    kill -9 $PID
    sleep 1
fi

rm "$LOG_DIR/24x7.pid"
echo "✅ System stopped"
