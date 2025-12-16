#!/bin/bash
#
# Oracle Cloud Migration Tracker
# Tracks A2.Flex (paid) instances and monitors for A1.Flex (free) availability
#

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                 Oracle Cloud Instance Tracker                     ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
A2_INSTANCES_FILE="a2_instances.txt"
A1_INSTANCES_FILE="a1_instances.txt"
WORKERS_FILE="../deploy/workers.txt"

# Track current A2.Flex instances
echo "=== Current A2.Flex Instances (Using Credits) ==="
echo ""
echo "Enter your A2.Flex instance details:"
echo ""

# Collect A2 instance info
for i in 1 2 3 4; do
    read -p "Worker $i IP (or press Enter to skip): " IP
    if [ -n "$IP" ]; then
        read -p "Worker $i OCID (for termination later): " OCID
        echo "$IP|$OCID|A2.Flex|$(date)" >> "$A2_INSTANCES_FILE"
        echo "$IP" >> "$WORKERS_FILE.tmp"
    fi
done

# Create/update workers.txt
if [ -f "$WORKERS_FILE.tmp" ]; then
    mv "$WORKERS_FILE.tmp" "$WORKERS_FILE"
    echo ""
    echo "✅ Updated workers.txt with A2.Flex IPs"
fi

echo ""
echo "=== Cost Summary ==="
A2_COUNT=$(wc -l < "$A2_INSTANCES_FILE" 2>/dev/null || echo 0)
A2_MONTHLY_COST=$((A2_COUNT * 8))  # ~$8 per A2.Flex instance

echo "A2.Flex instances: $A2_COUNT"
echo "Estimated monthly cost: \$$A2_MONTHLY_COST"
echo "Credits remaining after 1 month: \$$(( 300 - A2_MONTHLY_COST ))"
echo "Months of runway: $(( 300 / A2_MONTHLY_COST )) months"

echo ""
echo "=== Migration Plan ==="
echo ""
echo "1. Your A2.Flex instances are running NOW ✅"
echo "2. We'll monitor for A1.Flex (free) availability"
echo "3. When A1.Flex becomes available:"
echo "   - Create new A1.Flex instance"
echo "   - Migrate worker to new instance"
echo "   - Terminate old A2.Flex instance"
echo "4. Gradually replace all A2 with A1 (free)"
echo ""

# Create monitoring script
cat > check_a1_availability.sh << 'EOF'
#!/bin/bash
# Check A1.Flex availability

echo "Checking A1.Flex availability..."
echo ""
echo "Try creating an A1.Flex instance in Oracle Console:"
echo "1. Compute → Instances → Create Instance"
echo "2. Shape: VM.Standard.A1.Flex (Ampere)"
echo "3. 1 OCPU, 6GB RAM"
echo "4. Try all 3 Availability Domains"
echo ""
echo "Best times to check:"
echo "  🌅 Early morning: 6-8 AM CST"
echo "  🌙 Late night: 11 PM - 2 AM CST"
echo ""
echo "Run this check daily until you get all 4 free instances!"
EOF

chmod +x check_a1_availability.sh

echo "=== Next Steps ==="
echo ""
echo "1. Finish creating all 4 A2.Flex instances"
echo "2. Run: cd ../deploy && ./save_workers.sh"
echo "3. Deploy code: ./deploy_workers.sh"
echo "4. Check daily for A1.Flex: ./check_a1_availability.sh"
echo ""

# Create cron job suggestion
echo "=== Optional: Auto-Check Setup ==="
echo "Add to crontab for daily checks:"
echo "  0 6,23 * * * cd $(pwd) && ./check_a1_availability.sh"
echo ""
echo "This will remind you to check at 6 AM and 11 PM daily"
echo ""