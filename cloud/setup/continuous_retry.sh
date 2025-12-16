#!/bin/bash
#
# Continuous retry script - keeps trying every 5 minutes
#

COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa2ktu74gnhxcctwnk65ntpj6gfb53ofanbz2ram3jkm62ke5ekpsa"
SUBNET_ID="ocid1.subnet.oc1.us-chicago-1.aaaaaaaabey5noelor2c66iabfefonumt3p3zwye3gjcfsprtsafumnc4mjq"
IMAGE_ID="ocid1.image.oc1.us-chicago-1.aaaaaaaakqxltqh3hcpm2mv5o47ar2qrlposgqgdsqkbercvqjrml3e6mvsq"
SSH_KEY=$(cat ~/.ssh/id_rsa.pub)

ADS=("TEQo:US-CHICAGO-1-AD-2" "TEQo:US-CHICAGO-1-AD-3" "TEQo:US-CHICAGO-1-AD-1")

echo "Starting continuous retry (every 5 minutes)"
echo "Press Ctrl+C to stop"
echo ""

ATTEMPT=1

while true; do
    echo "=== Attempt #$ATTEMPT at $(date) ==="

    for AD in "${ADS[@]}"; do
        echo "Trying $AD..."

        # Try with timeout
        RESULT=$(timeout 30 ~/.local/bin/oci compute instance launch \
            --compartment-id "$COMPARTMENT_ID" \
            --availability-domain "$AD" \
            --shape VM.Standard.A1.Flex \
            --shape-config '{"ocpus":1,"memory-in-gbs":6}' \
            --image-id "$IMAGE_ID" \
            --subnet-id "$SUBNET_ID" \
            --display-name "ultrathink-worker-ubuntu" \
            --assign-public-ip true \
            --metadata "{\"ssh_authorized_keys\":\"$SSH_KEY\"}" \
            2>&1 || echo "FAILED")

        if echo "$RESULT" | grep -q "Out.*capacity"; then
            echo "  ❌ Out of capacity"
        elif echo "$RESULT" | grep -q "FAILED\|timed out"; then
            echo "  ⏱️  Timeout/Error"
        elif echo "$RESULT" | grep -q '"id"'; then
            echo "  ✅ SUCCESS!"
            echo ""
            IP=$(echo "$RESULT" | grep -o '"public-ip": "[^"]*"' | cut -d'"' -f4)
            ID=$(echo "$RESULT" | grep -o '"id": "ocid[^"]*"' | head -1 | cut -d'"' -f4)
            echo "Instance ID: $ID"
            echo "Public IP: $IP"
            echo ""
            echo "Add to workers.txt: ubuntu@$IP"
            exit 0
        fi
    done

    echo "All ADs at capacity. Waiting 5 minutes..."
    echo ""
    ATTEMPT=$((ATTEMPT + 1))
    sleep 300
done
