#!/bin/bash
# Quick script to save worker IPs

echo "Enter your 4 worker public IP addresses:"
echo ""
read -p "Worker 1 IP: " WORKER1
read -p "Worker 2 IP: " WORKER2
read -p "Worker 3 IP: " WORKER3
read -p "Worker 4 IP: " WORKER4

cat > workers.txt << EOF
$WORKER1
$WORKER2
$WORKER3
$WORKER4
EOF

echo ""
echo "✅ Workers saved to workers.txt:"
cat workers.txt
echo ""
echo "Testing SSH connectivity..."
echo ""

for worker in $WORKER1 $WORKER2 $WORKER3 $WORKER4; do
    echo -n "Testing $worker... "
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$worker "echo connected" 2>/dev/null; then
        echo "✅ Connected"
    else
        echo "❌ Cannot connect (VM might still be starting)"
    fi
done

echo ""
echo "Next steps:"
echo "1. ./deploy_workers.sh"
echo "2. ./start_all_workers.sh"
echo "3. ./check_workers.sh"