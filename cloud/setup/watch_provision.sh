#!/bin/bash
#
# Watch auto-provisioning progress in real-time
#

LOG_FILE="$HOME/.oracle_auto_provision/provision.log"
SUCCESS_FILE="$HOME/.oracle_auto_provision/success.txt"
PID_FILE="$HOME/.oracle_auto_provision/auto_provision.pid"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

clear

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Oracle A1 Auto-Provisioning - Live Monitor                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Auto-provisioning is RUNNING (PID: $PID)${NC}"
    else
        echo -e "${YELLOW}⚠ Auto-provisioning is NOT RUNNING${NC}"
        echo "Start with: ./auto_provision.sh --background"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Auto-provisioning is NOT RUNNING${NC}"
    echo "Start with: ./auto_provision.sh --background"
    exit 1
fi

# Count instances
CURRENT=$(~/.local/bin/oci compute instance list \
    --compartment-id ocid1.tenancy.oc1..aaaaaaaa2ktu74gnhxcctwnk65ntpj6gfb53ofanbz2ram3jkm62ke5ekpsa \
    --lifecycle-state RUNNING \
    --query 'data[?shape==`VM.Standard.A1.Flex`].id' \
    --raw-output 2>/dev/null | wc -l)

echo -e "Current instances: ${GREEN}$CURRENT${NC}/4"
echo ""

# Show successful provisions
if [ -f "$SUCCESS_FILE" ]; then
    echo -e "${GREEN}Successfully provisioned:${NC}"
    cat "$SUCCESS_FILE"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Live Log (Ctrl+C to exit):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Tail the log
if [ -f "$LOG_FILE" ]; then
    tail -f "$LOG_FILE"
else
    echo "Waiting for log file..."
    sleep 2
    tail -f "$LOG_FILE"
fi
