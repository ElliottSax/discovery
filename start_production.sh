#!/bin/bash
# Quick start script for production

# Navigate to project directory
cd /mnt/e/projects/discovery

# Check if environment variables are set
if [ -z "$DB_PASSWORD" ]; then
    echo 'ERROR: Please set DB_PASSWORD environment variable'
    echo 'Example: export DB_PASSWORD="your_secure_password"'
    exit 1
fi

# Run production system
echo 'Starting production system...'
python3 run_production.py
