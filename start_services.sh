#!/bin/bash

# Start all services for the Politician Trading Analysis System

echo "🚀 Starting Politician Trading Analysis Services..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  Port $1 is already in use${NC}"
        return 1
    fi
    return 0
}

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p data/pipeline
mkdir -p data/cache
mkdir -p logs

# Check environment variables
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Using defaults.${NC}"
    cp .env.example .env 2>/dev/null || echo "DB_PASSWORD=development" > .env
fi

# Source environment variables
export $(cat .env | grep -v '#' | xargs)

# Start monitoring system (Docker)
echo -e "\n${GREEN}1. Starting Monitoring System (Docker)...${NC}"
docker-compose -f docker-compose.production.yml up -d
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Monitoring system started${NC}"
else
    echo -e "${RED}❌ Failed to start monitoring system${NC}"
fi

# Check if API port is available
echo -e "\n${GREEN}2. Checking API port...${NC}"
if check_port 8000; then
    echo "✅ Port 8000 is available for API"
else
    echo -e "${YELLOW}Stopping existing service on port 8000...${NC}"
    kill $(lsof -t -i:8000) 2>/dev/null
fi

# Start FastAPI server
echo -e "\n${GREEN}3. Starting FastAPI Server...${NC}"
if [ -f "api/main.py" ]; then
    # Start in background
    python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > logs/api.log 2>&1 &
    API_PID=$!
    echo "API Server PID: $API_PID"
    echo $API_PID > .api.pid
    
    # Wait for API to start
    sleep 3
    
    # Check if API is running
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ API server started at http://localhost:8000${NC}"
        echo "   📖 API Docs: http://localhost:8000/api/docs"
    else
        echo -e "${RED}❌ API server failed to start. Check logs/api.log${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  API not found. Skipping...${NC}"
fi

# Run initial ETL pipeline
echo -e "\n${GREEN}4. Running Initial ETL Pipeline...${NC}"
if [ -f "data_pipeline/etl_orchestrator.py" ]; then
    python3 -c "
import asyncio
from data_pipeline.etl_orchestrator import ETLOrchestrator

async def run():
    orchestrator = ETLOrchestrator()
    result = await orchestrator.run_full_pipeline()
    print(f'Pipeline completed: {result.get(\"status\")}')

try:
    asyncio.run(run())
except Exception as e:
    print(f'Pipeline error: {e}')
" &
    ETL_PID=$!
    echo "ETL Pipeline PID: $ETL_PID"
else
    echo -e "${YELLOW}⚠️  ETL pipeline not found. Skipping...${NC}"
fi

# Display status
echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}🎉 Services Started Successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "📊 Monitoring Dashboard: Check Docker logs"
echo "   docker-compose -f docker-compose.production.yml logs -f"
echo ""
echo "🔌 API Endpoints:"
echo "   - Health: http://localhost:8000/health"
echo "   - Docs: http://localhost:8000/api/docs"
echo "   - Politicians: http://localhost:8000/api/v1/politicians"
echo "   - Trades: http://localhost:8000/api/v1/trades"
echo "   - Analysis: http://localhost:8000/api/v1/analysis/patterns"
echo ""
echo "🔑 Default API Credentials:"
echo "   Username: demo"
echo "   Password: demo123"
echo ""
echo "📝 Logs:"
echo "   - API: logs/api.log"
echo "   - Docker: docker-compose -f docker-compose.production.yml logs"
echo ""
echo "🛑 To stop all services, run: ./stop_services.sh"
echo ""