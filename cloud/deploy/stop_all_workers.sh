#!/bin/bash
#
# Stop all ULTRATHINK workers
#

set -e

echo "======================================================================="
echo "Stopping All Workers"
echo "======================================================================="
echo ""

# Configuration
WORKERS_FILE="workers.txt"

# Check if workers file exists
if [ ! -f "$WORKERS_FILE" ]; then
    echo "Error: $WORKERS_FILE not found!"
    exit 1
fi

# Read workers
mapfile -t WORKERS < "$WORKERS_FILE"
WORKER_COUNT=${#WORKERS[@]}

echo "Stopping $WORKER_COUNT workers..."
echo ""

# Stop each worker
for i in "${!WORKERS[@]}"; do
    WORKER="${WORKERS[$i]}"
    WORKER_NUM=$((i + 1))

    echo "[$WORKER_NUM/$WORKER_COUNT] Stopping worker on $WORKER..."

    ssh "$WORKER" << 'EOF'
cd ~/ultrathink
if [ -f worker.pid ]; then
    kill $(cat worker.pid) 2>/dev/null || true
    rm worker.pid
    echo "  ✓ Worker stopped"
else
    echo "  • Worker not running (no PID file)"
fi
EOF

done

echo ""
echo "======================================================================="
echo "All workers stopped"
echo "======================================================================="
echo ""