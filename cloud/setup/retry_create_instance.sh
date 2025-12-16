#!/bin/bash
#
# Retry Oracle Cloud instance creation across availability domains
#

set -e

COMPARTMENT_ID="ocid1.tenancy.oc1..aaaaaaaa2ktu74gnhxcctwnk65ntpj6gfb53ofanbz2ram3jkm62ke5ekpsa"
SUBNET_ID="ocid1.subnet.oc1.us-chicago-1.aaaaaaaabey5noelor2c66iabfefonumt3p3zwye3gjcfsprtsafumnc4mjq"
IMAGE_ID="ocid1.image.oc1.us-chicago-1.aaaaaaaakqxltqh3hcpm2mv5o47ar2qrlposgqgdsqkbercvqjrml3e6mvsq"
SSH_KEY=$(cat ~/.ssh/id_rsa.pub)

ADS=("TEQo:US-CHICAGO-1-AD-1" "TEQo:US-CHICAGO-1-AD-2" "TEQo:US-CHICAGO-1-AD-3")

echo "Attempting to create Ubuntu instance across availability domains..."
echo ""

for AD in "${ADS[@]}"; do
    echo "Trying $AD..."

    RESULT=$(~/.local/bin/oci compute instance launch \
        --compartment-id "$COMPARTMENT_ID" \
        --availability-domain "$AD" \
        --shape VM.Standard.A1.Flex \
        --shape-config '{"ocpus":1,"memory-in-gbs":6}' \
        --image-id "$IMAGE_ID" \
        --subnet-id "$SUBNET_ID" \
        --display-name "ultrathink-worker-2" \
        --assign-public-ip true \
        --metadata "{\"ssh_authorized_keys\":\"$SSH_KEY\"}" \
        2>&1 || echo "FAILED")

    if echo "$RESULT" | grep -q "Out.*capacity"; then
        echo "  ❌ Out of capacity in $AD"
        echo ""
        continue
    elif echo "$RESULT" | grep -q "FAILED"; then
        echo "  ❌ Failed in $AD"
        echo "  Error: $RESULT"
        echo ""
        continue
    else
        echo "  ✅ SUCCESS in $AD!"
        echo ""
        echo "$RESULT" | grep -E "(id|public-ip)" || echo "$RESULT"
        exit 0
    fi
done

echo "❌ All availability domains are at capacity"
echo "Try again later (best times: 5-8 AM Chicago time)"
exit 1
