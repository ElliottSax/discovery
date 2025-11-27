#!/bin/bash
# Start the 24/7 Autonomous Pattern Discovery System

set -e

echo "================================================"
echo "Starting 24/7 Autonomous Pattern Discovery System"
echo "================================================"

# Change to project directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if required environment variables are set
if [ -z "$DEEPSEEK_API_KEY" ] && [ -z "$TOGETHER_API_KEY" ] && [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  WARNING: No LLM API keys found in environment"
    echo "Set at least one of: DEEPSEEK_API_KEY, TOGETHER_API_KEY, OPENROUTER_API_KEY"
    echo "System will use fallback mode (limited functionality)"
fi

# Create required directories
mkdir -p logs data/pipeline data/patterns

# Check database connection
echo "Checking database connection..."
python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'quant_db'),
        user=os.getenv('DB_USER', 'quant_user'),
        password=os.getenv('DB_PASSWORD', 'REDACTED_PASSWORD')
    )
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "Cannot start without database connection"
    exit 1
fi

# Start the orchestrator
echo ""
echo "Starting orchestrator..."
echo "Logs will be written to: logs/orchestrator.log"
echo "Press Ctrl+C to stop"
echo ""

python3 -m ai_agents.orchestrator_24x7
