#!/bin/bash
# Claude Code Training Cluster Monitor

echo "=============================================="
echo "  CLAUDE CODE TRAINING CLUSTER STATUS"
echo "  $(date)"
echo "=============================================="
echo ""

total_iter=0
total_success=0
total_files=0

for i in 1 2 3 4; do
    case $i in
        1) ip="163.192.101.0"; focus="Algorithms" ;;
        2) ip="64.181.194.101"; focus="Trees/DS" ;;
        3) ip="147.224.209.57"; focus="Graphs/DP" ;;
        4) ip="147.224.136.175"; focus="Strings/Math" ;;
    esac
    
    stats=$(ssh -i ~/.ssh/oci_key -o ConnectTimeout=5 ubuntu@$ip "
        iter=\$(grep -c 'Iteration' ~/autocoder-training/training.log 2>/dev/null || echo 0)
        succ=\$(grep -c 'Success' ~/autocoder-training/training.log 2>/dev/null || echo 0)
        files=\$(ls ~/autocoder-training/workspace/*.py 2>/dev/null | wc -l)
        mem=\$(free -h | grep Mem | awk '{print \$3}')
        echo \"\$iter|\$succ|\$files|\$mem\"
    " 2>/dev/null)
    
    IFS='|' read -r iter succ files mem <<< "$stats"
    
    total_iter=$((total_iter + iter))
    total_success=$((total_success + succ))
    total_files=$((total_files + files))
    
    rate=0
    [ "$iter" -gt 0 ] && rate=$((succ * 100 / iter))
    
    printf "Instance %d %-12s | %6d iter | %3d%% success | %3d files | %s RAM\n" \
        $i "$focus" "$iter" "$rate" "$files" "$mem"
done

echo ""
echo "----------------------------------------------"
printf "TOTAL                   | %6d iter | %3d files\n" "$total_iter" "$total_files"
echo "=============================================="
