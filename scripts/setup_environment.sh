#!/bin/bash
# Setup environment for autonomous system

set -e

echo "================================================"
echo "Setting up Autonomous Pattern Discovery System"
echo "================================================"

# Change to project directory
cd "$(dirname "$0")/.."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements_autonomous.txt

echo ""
echo "================================================"
echo "Setup complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Set environment variables for LLM APIs:"
echo "   export DEEPSEEK_API_KEY='your-key'"
echo "   export TOGETHER_API_KEY='your-key'"
echo "   export OPENROUTER_API_KEY='your-key'"
echo ""
echo "2. Set database credentials (if different from defaults):"
echo "   export DB_HOST='localhost'"
echo "   export DB_PORT='5432'"
echo "   export DB_NAME='quant_db'"
echo "   export DB_USER='quant_user'"
echo "   export DB_PASSWORD='your-password'"
echo ""
echo "3. Start the autonomous system:"
echo "   ./scripts/start_autonomous_system.sh"
echo ""
