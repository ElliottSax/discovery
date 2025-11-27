#!/bin/bash
# Load environment variables and run analysis

set -a
source /mnt/e/projects/discovery/.env
set +a

python3 /mnt/e/projects/discovery/scripts/run_quick_analysis.py "$@"
