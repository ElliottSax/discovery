#!/bin/bash
#
# Automated Oracle Cloud A1.Flex Instance Provisioning
# Continuously retries until successful or manually stopped
#
# Usage:
#   ./auto_provision.sh                    # Run in foreground
#   ./auto_provision.sh --background       # Run in background
#   ./auto_provision.sh --stop             # Stop background process
#

set -e

# Configuration
COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa2ktu74gnhxcctwnk65ntpj6gfb53ofanbz2ram3jkm62ke5ekpsa"
SUBNET_ID="ocid1.subnet.oc1.us-chicago-1.aaaaaaaabey5noelor2c66iabfefonumt3p3zwye3gjcfsprtsafumnc4mjq"
IMAGE_ID="ocid1.image.oc1.us-chicago-1.aaaaaaaakqxltqh3hcpm2mv5o47ar2qrlposgqgdsqkbercvqjrml3e6mvsq"
SSH_KEY=$(cat ~/.ssh/id_rsa.pub)

# How many instances to create (4 total for free tier)
TARGET_INSTANCES=4

# Retry configuration
MIN_WAIT=300        # 5 minutes
MAX_WAIT=1800       # 30 minutes
CURRENT_WAIT=$MIN_WAIT

# Availability domains to try
ADS=("TEQo:US-CHICAGO-1-AD-1" "TEQo:US-CHICAGO-1-AD-2" "TEQo:US-CHICAGO-1-AD-3")

# Logging
LOG_DIR="$HOME/.oracle_auto_provision"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/provision.log"
PID_FILE="$LOG_DIR/auto_provision.pid"
SUCCESS_FILE="$LOG_DIR/success.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if already running
check_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Auto-provisioning already running (PID: $PID)${NC}"
            echo "Log file: $LOG_FILE"
            echo ""
            echo "To stop: $(readlink -f "$0") --stop"
            echo "To view logs: tail -f $LOG_FILE"
            exit 0
        else
            # Stale PID file
            rm "$PID_FILE"
        fi
    fi
}

# Stop background process
stop_background() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping auto-provisioning (PID: $PID)...${NC}"
            kill "$PID"
            rm "$PID_FILE"
            echo -e "${GREEN}Stopped${NC}"
        else
            echo -e "${YELLOW}No process running${NC}"
            rm "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}No background process found${NC}"
    fi
    exit 0
}

# Count current instances
count_instances() {
    ~/.local/bin/oci compute instance list \
        --compartment-id "$COMPARTMENT_ID" \
        --lifecycle-state RUNNING \
        --query 'data[?shape==`VM.Standard.A1.Flex`].id' \
        --raw-output 2>/dev/null | wc -l
}

# Try to create instance
try_create_instance() {
    local instance_num=$1
    local ad=$2

    log "Attempting to create instance $instance_num in $ad..."

    RESULT=$(~/.local/bin/oci compute instance launch \
        --compartment-id "$COMPARTMENT_ID" \
        --availability-domain "$ad" \
        --shape VM.Standard.A1.Flex \
        --shape-config '{"ocpus":1,"memory-in-gbs":6}' \
        --image-id "$IMAGE_ID" \
        --subnet-id "$SUBNET_ID" \
        --display-name "discovery-worker-$instance_num" \
        --assign-public-ip true \
        --metadata "{\"ssh_authorized_keys\":\"$SSH_KEY\"}" \
        2>&1 || echo "FAILED")

    if echo "$RESULT" | grep -qi "Out.*capacity"; then
        log "❌ Out of capacity in $ad"
        return 1
    elif echo "$RESULT" | grep -qi "FAILED\|error"; then
        log "❌ Failed: $(echo "$RESULT" | head -1)"
        return 1
    else
        log "✅ SUCCESS! Instance created in $ad"

        # Extract instance ID and IP
        INSTANCE_ID=$(echo "$RESULT" | grep -o 'ocid1.instance[^"]*' | head -1)

        # Wait for instance to get IP (max 60 seconds)
        for i in {1..12}; do
            sleep 5
            PUBLIC_IP=$(~/.local/bin/oci compute instance list-vnics \
                --instance-id "$INSTANCE_ID" \
                --query 'data[0]."public-ip"' \
                --raw-output 2>/dev/null || echo "")

            if [ -n "$PUBLIC_IP" ]; then
                log "🌐 Public IP: $PUBLIC_IP"
                echo "$PUBLIC_IP:8000" >> "$SUCCESS_FILE"

                # Add to workers.txt
                WORKERS_FILE="$(dirname "$0")/../deploy/workers.txt"
                if ! grep -q "$PUBLIC_IP" "$WORKERS_FILE" 2>/dev/null; then
                    echo "$PUBLIC_IP:8000" >> "$WORKERS_FILE"
                    log "📝 Added to workers.txt"
                fi

                break
            fi
        done

        return 0
    fi
}

# Main provisioning loop
provision_loop() {
    log "=========================================="
    log "Oracle A1.Flex Auto-Provisioning Started"
    log "Target: $TARGET_INSTANCES instances"
    log "=========================================="

    ATTEMPT=0

    while true; do
        ATTEMPT=$((ATTEMPT + 1))
        CURRENT_COUNT=$(count_instances)

        log ""
        log "Attempt #$ATTEMPT - Current instances: $CURRENT_COUNT/$TARGET_INSTANCES"

        if [ "$CURRENT_COUNT" -ge "$TARGET_INSTANCES" ]; then
            log "🎉 SUCCESS! All $TARGET_INSTANCES instances provisioned!"
            log ""
            log "Instances:"
            if [ -f "$SUCCESS_FILE" ]; then
                cat "$SUCCESS_FILE" | tee -a "$LOG_FILE"
            fi
            log ""
            log "Next steps:"
            log "1. Deploy workers: cd cloud/deploy && ./deploy_workers.sh"
            log "2. Start services: ./start_all_workers.sh"

            # Clean up PID file if running in background
            [ -f "$PID_FILE" ] && rm "$PID_FILE"

            exit 0
        fi

        NEEDED=$((TARGET_INSTANCES - CURRENT_COUNT))
        log "Need to provision: $NEEDED more instance(s)"

        # Try each availability domain
        SUCCESS=false
        for AD in "${ADS[@]}"; do
            INSTANCE_NUM=$((CURRENT_COUNT + 1))

            if try_create_instance "$INSTANCE_NUM" "$AD"; then
                SUCCESS=true
                CURRENT_WAIT=$MIN_WAIT  # Reset wait time on success
                break
            fi
        done

        # If no success, wait and retry with backoff
        if [ "$SUCCESS" = false ]; then
            log "⏳ All ADs at capacity. Waiting $CURRENT_WAIT seconds..."
            log "   (Next try: $(date -d "+$CURRENT_WAIT seconds" '+%H:%M:%S'))"

            sleep "$CURRENT_WAIT"

            # Exponential backoff (but cap at MAX_WAIT)
            CURRENT_WAIT=$((CURRENT_WAIT * 3 / 2))
            if [ "$CURRENT_WAIT" -gt "$MAX_WAIT" ]; then
                CURRENT_WAIT=$MAX_WAIT
            fi
        fi
    done
}

# Handle command line arguments
case "${1:-}" in
    --background|-b)
        check_running
        echo -e "${BLUE}Starting auto-provisioning in background...${NC}"

        # Fork to background and run provision_loop
        (
            provision_loop
        ) > "$LOG_FILE" 2>&1 &

        BG_PID=$!
        echo $BG_PID > "$PID_FILE"
        echo -e "${GREEN}Started with PID: $BG_PID${NC}"
        echo ""
        echo "Monitor progress:"
        echo "  tail -f $LOG_FILE"
        echo ""
        echo "Stop process:"
        echo "  $(readlink -f "$0") --stop"
        ;;
    --stop|-s)
        stop_background
        ;;
    --status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo -e "${GREEN}Running (PID: $PID)${NC}"
                echo "Current instances: $(count_instances)/$TARGET_INSTANCES"
                echo ""
                echo "Recent log:"
                tail -5 "$LOG_FILE"
            else
                echo -e "${YELLOW}Not running (stale PID file)${NC}"
                rm "$PID_FILE"
            fi
        else
            echo -e "${YELLOW}Not running${NC}"
        fi
        ;;
    --help|-h)
        echo "Oracle Cloud A1.Flex Auto-Provisioning"
        echo ""
        echo "Usage:"
        echo "  ./auto_provision.sh              Run in foreground"
        echo "  ./auto_provision.sh --background  Run in background"
        echo "  ./auto_provision.sh --stop       Stop background process"
        echo "  ./auto_provision.sh --status     Check status"
        echo ""
        echo "Logs: $LOG_FILE"
        ;;
    *)
        check_running
        provision_loop
        ;;
esac
