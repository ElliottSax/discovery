#!/bin/bash
# Start 24/7 Distributed Quant Analysis System

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

mkdir -p "$LOG_DIR"

echo "Starting 24/7 Distributed Quant Analysis System..."
echo "Project root: $PROJECT_ROOT"
echo "Logs: $LOG_DIR"
echo ""

# Check if already running
if [ -f "$LOG_DIR/24x7.pid" ]; then
    PID=$(cat "$LOG_DIR/24x7.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo "❌ System already running (PID: $PID)"
        echo "   Use ./scripts/stop_24x7.sh to stop it first"
        exit 1
    else
        echo "Removing stale PID file..."
        rm "$LOG_DIR/24x7.pid"
    fi
fi

# Start in background
cd "$PROJECT_ROOT"
nohup python3 scripts/run_24x7_distributed.py >> "$LOG_DIR/24x7_stdout.log" 2>&1 &
PID=$!

# Save PID
echo $PID > "$LOG_DIR/24x7.pid"

echo "✅ System started (PID: $PID)"
echo ""
echo "Monitor logs:"
echo "  tail -f $LOG_DIR/distributed_24x7.log"
echo "  tail -f $LOG_DIR/24x7_stdout.log"
echo ""
echo "Check status:"
echo "  ./scripts/status_24x7.sh"
echo ""
echo "Stop system:"
echo "  ./scripts/stop_24x7.sh"
echo ""
