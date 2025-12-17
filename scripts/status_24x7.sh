#!/bin/bash
# Check status of 24/7 Distributed Quant Analysis System

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
STATUS_FILE="$LOG_DIR/24x7_status.json"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         24/7 Distributed Quant Analysis System Status             ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if running
if [ -f "$LOG_DIR/24x7.pid" ]; then
    PID=$(cat "$LOG_DIR/24x7.pid")
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Process Status: RUNNING (PID: $PID)"

        # Get CPU and memory usage
        if command -v ps &> /dev/null; then
            CPU=$(ps -p $PID -o %cpu --no-headers | xargs)
            MEM=$(ps -p $PID -o %mem --no-headers | xargs)
            RSS=$(ps -p $PID -o rss --no-headers | xargs)
            RSS_MB=$((RSS / 1024))
            echo "   CPU: ${CPU}%"
            echo "   Memory: ${MEM}% (${RSS_MB} MB)"
        fi
    else
        echo "❌ Process Status: NOT RUNNING (stale PID: $PID)"
    fi
else
    echo "❌ Process Status: NOT RUNNING"
fi

echo ""

# Check status file
if [ -f "$STATUS_FILE" ]; then
    echo "📊 System Statistics:"
    echo "──────────────────────────────────────────────────────────────────"

    if command -v python3 &> /dev/null; then
        python3 << EOF
import json
from datetime import datetime

with open("$STATUS_FILE") as f:
    status = json.load(f)

print(f"   Running: {status.get('running', 'N/A')}")

if status.get('start_time'):
    start = datetime.fromisoformat(status['start_time'])
    print(f"   Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")

uptime_hours = status.get('uptime_hours')
if uptime_hours:
    days = int(uptime_hours // 24)
    hours = int(uptime_hours % 24)
    minutes = int((uptime_hours * 60) % 60)
    print(f"   Uptime: {days}d {hours}h {minutes}m")

print(f"   Total cycles: {status.get('total_cycles', 0)}")
print(f"   Successful: {status.get('successful_cycles', 0)}")
print(f"   Failed: {status.get('failed_cycles', 0)}")

success_rate = status.get('success_rate', 0)
print(f"   Success rate: {success_rate*100:.1f}%")

print(f"   Total trades analyzed: {status.get('total_trades_analyzed', 0):,}")

avg_throughput = status.get('average_throughput', 0)
print(f"   Average throughput: {avg_throughput:.1f} trades/sec")

print(f"   Workers available: {status.get('workers_available', 0)}")

if status.get('last_success'):
    last_success = datetime.fromisoformat(status['last_success'])
    print(f"   Last success: {last_success.strftime('%Y-%m-%d %H:%M:%S')}")

if status.get('consecutive_failures', 0) > 0:
    print(f"   ⚠️  Consecutive failures: {status['consecutive_failures']}")

updated = datetime.fromisoformat(status['updated_at'])
print(f"   Updated: {updated.strftime('%Y-%m-%d %H:%M:%S')}")
EOF
    else
        cat "$STATUS_FILE"
    fi
else
    echo "⚠️  No status file found"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "Log files:"
echo "  Main: $LOG_DIR/distributed_24x7.log"
echo "  Output: $LOG_DIR/24x7_stdout.log"
echo "  Status: $STATUS_FILE"
echo ""
echo "Results directory:"
echo "  $PROJECT_ROOT/data/analysis/24x7/"
echo ""
