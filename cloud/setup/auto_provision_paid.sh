#!/bin/bash
#
# Automated Oracle Cloud PAID Instance Provisioning (VM.Standard.E4.Flex)
# Uses $300 credit - much better availability than free tier
#
# Usage:
#   ./auto_provision_paid.sh                    # Run in foreground
#   ./auto_provision_paid.sh --background       # Run in background
#   ./auto_provision_paid.sh --stop             # Stop background process
#

set -e

# Configuration
COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa2ktu74gnhxcctwnk65ntpj6gfb53ofanbz2ram3jkm62ke5ekpsa"
SUBNET_ID="ocid1.subnet.oc1.us-chicago-1.aaaaaaaabey5noelor2c66iabfefonumt3p3zwye3gjcfsprtsafumnc4mjq"
# x86_64 Ubuntu 22.04 image (compatible with E4.Flex)
IMAGE_ID="ocid1.image.oc1.us-chicago-1.aaaaaaaavrjuy2xsj5f2yqianpvnjqb3cgi4pa35cwloplsd4rntvuz6oz2a"
SSH_KEY=$(cat ~/.ssh/id_rsa.pub)

# PAID COMPUTE CONFIGURATION
# VM.Standard.E4.Flex: AMD EPYC, ~$0.015/OCPU/hour
# 4 instances x 2 OCPUs x 16GB = 8 cores, 64GB RAM
# Cost: ~$21/month or ~14 days on $300 credit for max performance
TARGET_INSTANCES=4
OCPU_COUNT=2           # OCPUs per instance (flexible: 1-64)
MEMORY_GB=16           # RAM per instance (16GB per OCPU minimum)
SHAPE="VM.Standard.E4.Flex"

# Retry configuration (paid instances have better availability)
MIN_WAIT=60         # 1 minute (faster retries since capacity better)
MAX_WAIT=300        # 5 minutes
CURRENT_WAIT=$MIN_WAIT

# Availability domains to try
ADS=("TEQo:US-CHICAGO-1-AD-1" "TEQo:US-CHICAGO-1-AD-2" "TEQo:US-CHICAGO-1-AD-3")

# Logging
LOG_DIR="$HOME/.oracle_auto_provision"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/provision_paid.log"
PID_FILE="$LOG_DIR/auto_provision_paid.pid"
WORKERS_FILE="$LOG_DIR/workers_paid.txt"

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
            echo "Auto-provisioner already running (PID: $PID)"
            echo "Log: tail -f $LOG_FILE"
            echo "Stop: $0 --stop"
            exit 1
        else
            rm -f "$PID_FILE"
        fi
    fi
}

# Stop background process
stop_background() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log "Stopping auto-provisioner (PID: $PID)..."
            kill "$PID"
            rm -f "$PID_FILE"
            log "✅ Stopped"
        else
            log "No running process found"
            rm -f "$PID_FILE"
        fi
    else
        log "No PID file found - not running"
    fi
    exit 0
}

# Get current instance count
get_instance_count() {
    ~/.local/bin/oci compute instance list \
        --compartment-id "$COMPARTMENT_ID" \
        --lifecycle-state RUNNING \
        --query 'length(data)' \
        --raw-output 2>/dev/null || echo "0"
}

# Create instance
create_instance() {
    local instance_num=$1
    local ad=$2
    local display_name="discovery-worker-paid-$instance_num"

    log "Attempting to create $display_name in $ad..."
    log "  Shape: $SHAPE ($OCPU_COUNT OCPUs, ${MEMORY_GB}GB RAM)"
    log "  Est. cost: ~\$0.88/month per OCPU"

    RESULT=$(~/.local/bin/oci compute instance launch \
        --availability-domain "$ad" \
        --compartment-id "$COMPARTMENT_ID" \
        --shape "$SHAPE" \
        --shape-config "{\"ocpus\":$OCPU_COUNT,\"memoryInGBs\":$MEMORY_GB}" \
        --display-name "$display_name" \
        --image-id "$IMAGE_ID" \
        --subnet-id "$SUBNET_ID" \
        --assign-public-ip true \
        --metadata "{\"ssh_authorized_keys\":\"$SSH_KEY\"}" \
        --wait-for-state RUNNING \
        --max-wait-seconds 300 \
        2>&1)

    if echo "$RESULT" | grep -q "Out of host capacity"; then
        log "❌ Out of capacity in $ad"
        return 1
    elif echo "$RESULT" | grep -q "OutOfHostCapacity"; then
        log "❌ Out of capacity in $ad"
        return 1
    elif echo "$RESULT" | grep -q '"lifecycle-state": "RUNNING"'; then
        # Extract instance ID and IP
        INSTANCE_ID=$(echo "$RESULT" | grep -o 'ocid1.instance[^"]*' | head -1)

        # Get public IP
        sleep 5
        PUBLIC_IP=$(~/.local/bin/oci compute instance list-vnics \
            --instance-id "$INSTANCE_ID" \
            --query 'data[0]."public-ip"' \
            --raw-output 2>/dev/null)

        log "✅ SUCCESS! Instance created:"
        log "   ID: $INSTANCE_ID"
        log "   IP: $PUBLIC_IP"
        log "   Shape: $SHAPE ($OCPU_COUNT OCPUs, ${MEMORY_GB}GB RAM)"

        # Save to workers file
        echo "$PUBLIC_IP" >> "$WORKERS_FILE"

        return 0
    else
        log "❌ Failed: $RESULT"
        return 1
    fi
}

# Main provisioning loop
provision_instances() {
    local attempt=1

    TOTAL_CORES=$((TARGET_INSTANCES * OCPU_COUNT))
    TOTAL_RAM=$((TARGET_INSTANCES * MEMORY_GB))

    log "========================================="
    log "PAID COMPUTE AUTO-PROVISIONER STARTED"
    log "========================================="
    log "Target: $TARGET_INSTANCES instances"
    log "Shape: $SHAPE"
    log "Per instance: $OCPU_COUNT OCPUs, ${MEMORY_GB}GB RAM"
    log "Total when complete: ${TOTAL_CORES} cores, ${TOTAL_RAM}GB RAM"
    log "Estimated cost: ~\$21/month for 4x instances (2 OCPUs each)"
    log "$300 credit should last ~14 months at this usage"
    log "========================================="

    while true; do
        CURRENT_COUNT=$(get_instance_count)
        NEEDED=$((TARGET_INSTANCES - CURRENT_COUNT))

        log ""
        log "Attempt #$attempt - Current instances: $CURRENT_COUNT/$TARGET_INSTANCES"
        log "Need to provision: $NEEDED more instance(s)"

        if [ "$NEEDED" -le 0 ]; then
            log "🎉 All $TARGET_INSTANCES instances provisioned!"
            log "Workers: $(cat $WORKERS_FILE 2>/dev/null | tr '\n' ', ')"
            log "Total compute: $((TARGET_INSTANCES * OCPU_COUNT)) cores, $((TARGET_INSTANCES * MEMORY_GB))GB RAM"
            return 0
        fi

        # Try each availability domain
        local success=false
        for ad in "${ADS[@]}"; do
            NEXT_NUM=$((CURRENT_COUNT + 1))
            if create_instance "$NEXT_NUM" "$ad"; then
                success=true
                CURRENT_WAIT=$MIN_WAIT  # Reset wait time on success
                break
            fi
        done

        if [ "$success" = false ]; then
            log "⏳ All ADs at capacity. Waiting $CURRENT_WAIT seconds..."
            log "   (Next try: $(date -d "+$CURRENT_WAIT seconds" '+%H:%M:%S'))"
            sleep "$CURRENT_WAIT"

            # Exponential backoff
            CURRENT_WAIT=$((CURRENT_WAIT * 2))
            if [ "$CURRENT_WAIT" -gt "$MAX_WAIT" ]; then
                CURRENT_WAIT=$MAX_WAIT
            fi
        fi

        attempt=$((attempt + 1))
    done
}

# Handle command line arguments
case "${1:-}" in
    --background)
        check_running
        log "Starting in background mode..."
        nohup "$0" --foreground-worker >> "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        log "Background process started (PID: $(cat $PID_FILE))"
        log "Monitor: tail -f $LOG_FILE"
        log "Stop: $0 --stop"
        exit 0
        ;;
    --foreground-worker)
        # Internal flag for background execution - don't check if running
        provision_instances
        ;;
    --stop)
        stop_background
        ;;
    --status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "✅ Running (PID: $PID)"
                echo "Instances: $(get_instance_count)/$TARGET_INSTANCES"
                [ -f "$WORKERS_FILE" ] && echo "Workers: $(cat $WORKERS_FILE | tr '\n' ', ')"
            else
                echo "❌ Not running (stale PID file)"
            fi
        else
            echo "❌ Not running"
        fi
        exit 0
        ;;
    "")
        # Run in foreground
        check_running
        provision_instances
        ;;
    *)
        echo "Usage: $0 [--background|--stop|--status]"
        exit 1
        ;;
esac
