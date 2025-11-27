#!/bin/bash
# Quick status check for autonomous system

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     24/7 AUTONOMOUS PATTERN DISCOVERY - ULTRATHINK STATUS     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if running
if pgrep -f "orchestrator_24x7" > /dev/null; then
    echo "✅ Status: RUNNING"
    PID=$(pgrep -f "orchestrator_24x7")
    echo "   PID: $PID"

    # Get uptime
    START_TIME=$(ps -p $PID -o lstart= 2>/dev/null)
    echo "   Started: $START_TIME"
else
    echo "❌ Status: STOPPED"
    echo ""
    echo "To start: ./scripts/start_autonomous_system.sh"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 DISCOVERIES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "data/patterns/discoveries.jsonl" ]; then
    TOTAL=$(wc -l < data/patterns/discoveries.jsonl)
    echo "Total discoveries: $TOTAL"

    echo ""
    echo "Latest 5 discoveries:"
    tail -5 data/patterns/discoveries.jsonl | while read line; do
        TYPE=$(echo "$line" | jq -r '.type')
        TIME=$(echo "$line" | jq -r '.timestamp | split("T")[1] | split(".")[0]')
        echo "  [$TIME] $TYPE"
    done
else
    echo "No discoveries yet"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 RECENT LOGS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "logs/orchestrator.log" ]; then
    tail -10 logs/orchestrator.log | grep -E "INFO|SUCCESS|ERROR" | tail -5
else
    echo "No logs yet"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💾 PIPELINE DATA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "data/pipeline" ]; then
    TRADE_FILES=$(ls -1 data/pipeline/trades_*.json 2>/dev/null | wc -l)
    ANALYTICS_FILES=$(ls -1 data/pipeline/analytics_*.json 2>/dev/null | wc -l)
    echo "Trade files: $TRADE_FILES"
    echo "Analytics files: $ANALYTICS_FILES"

    if [ $TRADE_FILES -gt 0 ]; then
        LATEST=$(ls -t data/pipeline/trades_*.json | head -1)
        echo "Latest: $(basename $LATEST)"
    fi
else
    echo "No pipeline data yet"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Commands:"
echo "  ./scripts/status.sh           - Show this status"
echo "  tail -f logs/orchestrator.log - Watch live logs"
echo "  pkill -f orchestrator_24x7    - Stop system"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
