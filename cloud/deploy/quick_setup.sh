#!/bin/bash
# Quick setup for Oracle Cloud workers

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    Quick Worker Setup                             ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Worker 1 is already known
WORKER1="163.192.103.233"

echo "Worker 1: $WORKER1 ✅"
echo ""
echo "Enter the IPs for workers 2-4 as they become available:"
echo ""

read -p "Worker 2 IP (press Enter to skip): " WORKER2
read -p "Worker 3 IP (press Enter to skip): " WORKER3
read -p "Worker 4 IP (press Enter to skip): " WORKER4

# Create workers.txt
cat > workers.txt << EOF
$WORKER1
$WORKER2
$WORKER3
$WORKER4
EOF

# Remove empty lines
sed -i '/^$/d' workers.txt

echo ""
echo "✅ Saved to workers.txt:"
cat workers.txt

echo ""
echo "Testing SSH connectivity..."
echo ""

for worker in $(cat workers.txt); do
    echo -n "Testing $worker... "
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -o PasswordAuthentication=no ubuntu@$worker "echo connected" 2>/dev/null; then
        echo "✅ Connected"
    else
        echo "⚠️  Not ready yet (VM might still be initializing)"
    fi
done

echo ""
echo "=== Next Steps ==="
echo "Once all VMs are ready:"
echo "1. ./deploy_workers.sh    # Deploy code"
echo "2. ./start_all_workers.sh # Start services"
echo "3. ./check_workers.sh     # Verify health"
echo ""

# Check if all 4 are present
WORKER_COUNT=$(wc -l < workers.txt)
if [ "$WORKER_COUNT" -eq 4 ]; then
    echo "All 4 workers configured! Ready to deploy."
else
    echo "You have $WORKER_COUNT workers configured. Add more IPs when ready."
fi