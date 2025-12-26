#!/bin/bash
# Sync generated code from all training instances

OUTPUT_DIR="/mnt/e/projects/discovery/training-output"

for i in 1 2 3 4; do
    case $i in
        1) ip="163.192.101.0" ;;
        2) ip="64.181.194.101" ;;
        3) ip="147.224.209.57" ;;
        4) ip="147.224.136.175" ;;
    esac
    
    rsync -avz -e "ssh -i ~/.ssh/oci_key" \
        ubuntu@$ip:~/autocoder-training/workspace/*.py \
        $OUTPUT_DIR/instance-$i/ 2>/dev/null
done

echo "Synced $(find $OUTPUT_DIR -name '*.py' | wc -l) files at $(date)"
