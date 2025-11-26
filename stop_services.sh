#!/bin/bash

# Stop all services for the Politician Trading Analysis System

echo "🛑 Stopping Politician Trading Analysis Services..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stop API server
echo -e "\n${YELLOW}Stopping API Server...${NC}"
if [ -f .api.pid ]; then
    API_PID=$(cat .api.pid)
    if kill $API_PID 2>/dev/null; then
        echo -e "${GREEN}✅ API server stopped${NC}"
    else
        echo -e "${YELLOW}API server was not running${NC}"
    fi
    rm .api.pid
else
    # Try to find and kill by port
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        kill $(lsof -t -i:8000) 2>/dev/null
        echo -e "${GREEN}✅ API server stopped${NC}"
    else
        echo -e "${YELLOW}No API server found on port 8000${NC}"
    fi
fi

# Stop Docker services
echo -e "\n${YELLOW}Stopping Docker services...${NC}"
docker-compose -f docker-compose.production.yml down
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker services stopped${NC}"
else
    echo -e "${RED}❌ Failed to stop Docker services${NC}"
fi

echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}All services stopped successfully!${NC}"
echo -e "${GREEN}================================================${NC}"