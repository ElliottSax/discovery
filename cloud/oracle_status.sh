#!/bin/bash
#
# Oracle Cloud Infrastructure Quick Status Check
# Shows current state of Oracle Cloud setup
#

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║              Oracle Cloud Infrastructure Status                   ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Function to check status
check_item() {
    local item="$1"
    local condition="$2"
    local description="$3"

    if eval "$condition"; then
        echo -e "${GREEN}✅${NC} $item"
        [ -n "$description" ] && echo "   $description"
    else
        echo -e "${RED}❌${NC} $item"
        [ -n "$description" ] && echo "   $description"
    fi
}

# Function to check warning
check_warning() {
    local item="$1"
    local condition="$2"
    local description="$3"

    if eval "$condition"; then
        echo -e "${YELLOW}⚠️${NC}  $item"
        [ -n "$description" ] && echo "   $description"
    else
        echo -e "${GREEN}✅${NC} $item"
        [ -n "$description" ] && echo "   $description"
    fi
}

echo -e "${BOLD}1. Local Configuration${NC}"
echo "------------------------"

# Check SSH keys
check_item "SSH Keys" "[ -f ~/.ssh/id_rsa.pub ]" "Location: ~/.ssh/id_rsa.pub"

# Check OCI API keys
check_item "OCI API Keys" "[ -f ~/.oci/oci_api_key.pem ]" "Location: ~/.oci/"

# Check OCI CLI
if command -v oci &> /dev/null; then
    OCI_VERSION=$(oci --version 2>&1 | cut -d' ' -f2)
    check_item "OCI CLI" "true" "Version: $OCI_VERSION"
else
    check_item "OCI CLI" "false" "Run: ./setup/install_oci_cli.sh"
fi

# Check OCI config
check_item "OCI Config" "[ -f ~/.oci/config ]" "Location: ~/.oci/config"

# Check .env file
PROJECT_ROOT="$(dirname $0)/.."
if [ -f "$PROJECT_ROOT/.env" ]; then
    source <(grep -E '^ORACLE_' "$PROJECT_ROOT/.env" | sed 's/^/export /')
    if [ -n "$ORACLE_FINGERPRINT" ] && [ "$ORACLE_FINGERPRINT" != "" ]; then
        check_item ".env Configuration" "true" "Fingerprint configured"
    else
        check_warning ".env Configuration" "true" "Missing fingerprint"
    fi
else
    check_item ".env Configuration" "false" "File not found"
fi

echo ""
echo -e "${BOLD}2. Oracle Cloud Resources${NC}"
echo "---------------------------"

# Test OCI connection
if command -v oci &> /dev/null && [ -f ~/.oci/config ]; then
    if oci iam region list &> /dev/null; then
        check_item "Oracle Cloud Connection" "true" "API access verified"
    else
        check_item "Oracle Cloud Connection" "false" "Check fingerprint/config"
    fi
else
    echo -e "${YELLOW}⚠️${NC}  Oracle Cloud Connection"
    echo "   OCI CLI not configured"
fi

echo ""
echo -e "${BOLD}3. Worker Configuration${NC}"
echo "------------------------"

# Check workers.txt
WORKERS_FILE="$PROJECT_ROOT/cloud/deploy/workers.txt"
if [ -f "$WORKERS_FILE" ]; then
    WORKER_COUNT=$(grep -v '^#' "$WORKERS_FILE" | grep -c '^[0-9]' || echo "0")
    if [ "$WORKER_COUNT" -gt 0 ]; then
        check_item "Workers Configured" "true" "Found $WORKER_COUNT workers"
        echo "   Workers:"
        grep -v '^#' "$WORKERS_FILE" | grep '^[0-9]' | while read -r worker; do
            echo "   • $worker"
        done
    else
        check_warning "Workers Configured" "false" "workers.txt empty"
    fi
else
    check_item "Workers Configured" "false" "workers.txt not found"
fi

# Check deployment scripts
echo ""
echo -e "${BOLD}4. Deployment Scripts${NC}"
echo "----------------------"

DEPLOY_DIR="$PROJECT_ROOT/cloud/deploy"
for script in deploy_workers.sh start_all_workers.sh stop_all_workers.sh check_workers.sh; do
    check_item "$script" "[ -x $DEPLOY_DIR/$script ]"
done

# Check worker health (if configured)
if [ "$WORKER_COUNT" -gt 0 ] 2>/dev/null; then
    echo ""
    echo -e "${BOLD}5. Worker Health${NC}"
    echo "----------------"

    ONLINE_COUNT=0
    grep -v '^#' "$WORKERS_FILE" | grep '^[0-9]' | while read -r worker; do
        if curl -s --connect-timeout 2 "http://$worker:8000/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅${NC} $worker - Online"
            ((ONLINE_COUNT++))
        else
            echo -e "${RED}❌${NC} $worker - Offline"
        fi
    done

    echo ""
    echo "Summary: $ONLINE_COUNT/$WORKER_COUNT workers online"
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Determine overall status
if [ -f ~/.oci/config ] && [ -f "$WORKERS_FILE" ] && [ "$WORKER_COUNT" -gt 0 ] 2>/dev/null; then
    echo -e "${GREEN}${BOLD}Status: READY${NC}"
    echo ""
    echo "Commands:"
    echo "  Monitor:  python3 cloud/monitor/worker_dashboard.py"
    echo "  Health:   cd cloud/deploy && ./check_workers.sh"
    echo "  Restart:  cd cloud/deploy && ./stop_all_workers.sh && ./start_all_workers.sh"
elif [ -f ~/.oci/config ]; then
    echo -e "${YELLOW}${BOLD}Status: PARTIALLY CONFIGURED${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Provision VMs: cd cloud/setup && python3 provision_oracle_vms.py"
    echo "  2. Or create VMs manually in Oracle Console"
    echo "  3. Add IPs to cloud/deploy/workers.txt"
else
    echo -e "${RED}${BOLD}Status: NOT CONFIGURED${NC}"
    echo ""
    echo "To get started:"
    echo "  cd cloud/setup && ./setup_oracle_cloud.sh"
fi

echo ""