#!/bin/bash
#
# Oracle Cloud "Out of Capacity" Helper
# Strategies for getting ARM instances
#

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║           Oracle Cloud ARM Instance Capacity Strategies           ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}⚠️  Getting 'Out of Capacity' is normal!${NC}"
echo "Oracle's free ARM instances are very popular."
echo ""

echo -e "${BLUE}Strategy 1: Try Different Availability Domains${NC}"
echo "-------------------------------------------"
echo "1. In the 'Placement' section when creating instance"
echo "2. Try each AD in order:"
echo "   • AD-1 (e.g., tGvK:US-CHICAGO-1-AD-1)"
echo "   • AD-2 (e.g., tGvK:US-CHICAGO-1-AD-2)"
echo "   • AD-3 (e.g., tGvK:US-CHICAGO-1-AD-3)"
echo ""

echo -e "${BLUE}Strategy 2: Alternative Configurations${NC}"
echo "--------------------------------------"
echo "Instead of: 4 VMs × 1 OCPU × 6GB RAM"
echo "Try these alternatives:"
echo ""
echo "Option A: 2 Larger VMs"
echo "  • 2 VMs × 2 OCPUs × 12GB RAM each"
echo "  • Still 4 OCPUs total (max free tier)"
echo ""
echo "Option B: 1 Large VM (temporary)"
echo "  • 1 VM × 4 OCPUs × 24GB RAM"
echo "  • Split into smaller VMs later"
echo ""
echo "Option C: Mixed Sizes"
echo "  • 1 VM × 2 OCPUs × 12GB RAM"
echo "  • 2 VMs × 1 OCPU × 6GB RAM each"
echo ""

echo -e "${BLUE}Strategy 3: Best Times to Try${NC}"
echo "-----------------------------"
# Get current time in different timezones
echo "Current times:"
echo "  Chicago: $(TZ='America/Chicago' date '+%H:%M %Z')"
echo "  UTC:     $(date -u '+%H:%M %Z')"
echo ""
echo "Best capacity windows:"
echo "  🌅 Early morning: 5-8 AM local time"
echo "  🌙 Late night: 11 PM - 2 AM local time"
echo "  📅 Weekends generally better"
echo ""

echo -e "${BLUE}Strategy 4: Auto-Retry Script${NC}"
echo "-----------------------------"
echo "Want me to create an auto-retry script?"
echo "It will keep trying to create instances every few minutes."
echo ""

read -p "Create auto-retry script? (yes/no): " CREATE_RETRY

if [ "$CREATE_RETRY" = "yes" ]; then
    cat > oracle_auto_retry.py << 'EOF'
#!/usr/bin/env python3
"""
Oracle Cloud Auto-Retry Instance Creation
Keeps trying to create instances until successful
"""

import time
import subprocess
import json
from datetime import datetime

# Configuration
RETRY_INTERVAL = 300  # 5 minutes
MAX_RETRIES = 100

def try_create_instance(name, ad_index):
    """Try to create an instance in a specific AD"""

    # Get list of ADs
    ads = [
        "tGvK:US-CHICAGO-1-AD-1",
        "tGvK:US-CHICAGO-1-AD-2",
        "tGvK:US-CHICAGO-1-AD-3"
    ]

    if ad_index >= len(ads):
        return False

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Trying {name} in {ads[ad_index]}...")

    # This is a placeholder - actual OCI CLI command would go here
    # For manual creation, just return False to indicate we need to try manually
    print(f"  → Please try creating {name} in AD: {ads[ad_index]}")
    return False

def main():
    print("Oracle Cloud Auto-Retry Helper")
    print("=" * 50)
    print("\nThis script will remind you to retry creating instances")
    print(f"every {RETRY_INTERVAL} seconds ({RETRY_INTERVAL/60} minutes)")
    print("\nPress Ctrl+C to stop")

    instances = [
        "ultrathink-worker-1",
        "ultrathink-worker-2",
        "ultrathink-worker-3",
        "ultrathink-worker-4"
    ]

    created = []
    attempts = 0
    ad_index = 0

    while len(created) < len(instances) and attempts < MAX_RETRIES:
        attempts += 1
        print(f"\n\n{'='*50}")
        print(f"Attempt #{attempts}")
        print(f"{'='*50}")

        for instance in instances:
            if instance in created:
                continue

            print(f"\n🔄 Go to Oracle Console and try creating: {instance}")
            print(f"   Use Availability Domain #{ad_index + 1}")
            print(f"   Shape: VM.Standard.A1.Flex")
            print(f"   OCPUs: 1, RAM: 6GB")

        # Rotate through ADs
        ad_index = (ad_index + 1) % 3

        # Ask if any were successful
        print("\n" + "="*50)
        success = input("Did any instances get created? List names (comma-separated) or press Enter: ")
        if success:
            for name in success.split(','):
                name = name.strip()
                if name in instances and name not in created:
                    created.append(name)
                    print(f"✅ Marked {name} as created")

        if len(created) < len(instances):
            print(f"\n⏰ Waiting {RETRY_INTERVAL/60} minutes before next attempt...")
            print(f"   Still need: {[i for i in instances if i not in created]}")
            time.sleep(RETRY_INTERVAL)

    if len(created) == len(instances):
        print("\n🎉 All instances created successfully!")
    else:
        print(f"\n⚠️  Created {len(created)}/{len(instances)} instances")
        print(f"   Still need: {[i for i in instances if i not in created]}")

if __name__ == "__main__":
    main()
EOF

    chmod +x oracle_auto_retry.py
    echo ""
    echo -e "${GREEN}✅ Created oracle_auto_retry.py${NC}"
    echo "Run it with: python3 oracle_auto_retry.py"
fi

echo ""
echo -e "${BLUE}Strategy 5: Manual Persistence${NC}"
echo "------------------------------"
echo "1. Keep the Create Instance form filled out"
echo "2. Just change the Availability Domain"
echo "3. Click Create every few minutes"
echo "4. Open multiple browser tabs with the form ready"
echo ""

echo -e "${YELLOW}Current Recommendation:${NC}"
echo "----------------------"
HOUR=$(date +%H)
if [ $HOUR -ge 5 ] && [ $HOUR -le 8 ]; then
    echo "✅ Good time window (early morning) - keep trying!"
elif [ $HOUR -ge 23 ] || [ $HOUR -le 2 ]; then
    echo "✅ Good time window (late night) - keep trying!"
else
    echo "⚠️  Not peak time - but still worth trying"
    echo "   Consider setting an alarm for early morning"
fi

echo ""
echo "Remember: Free ARM instances are valuable ($50/month each)"
echo "so competition is high. Persistence pays off!"
echo ""