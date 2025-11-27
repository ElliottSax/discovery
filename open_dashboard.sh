#!/bin/bash
# Open the Politician Trading Analytics Dashboard

echo "🚀 Politician Trading Analytics Dashboard"
echo "=========================================="
echo ""

# Check if API is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ API Server: Running on http://localhost:8000"
else
    echo "✗ API Server: Not running"
    echo ""
    echo "Starting API server..."
    cd /mnt/e/projects/discovery
    python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/discovery_api.log 2>&1 &
    sleep 3
    echo "✓ API Server started"
fi

echo ""
echo "📊 Opening dashboard in browser..."
echo ""

# Get full path to HTML file
DASHBOARD_PATH="/mnt/e/projects/discovery/api_demo.html"

# Try different browsers
if command -v google-chrome &> /dev/null; then
    google-chrome "$DASHBOARD_PATH" 2>/dev/null &
elif command -v firefox &> /dev/null; then
    firefox "$DASHBOARD_PATH" 2>/dev/null &
elif command -v chromium &> /dev/null; then
    chromium "$DASHBOARD_PATH" 2>/dev/null &
else
    echo "⚠ No browser found. Please open this file manually:"
    echo "   file://$DASHBOARD_PATH"
fi

echo ""
echo "Dashboard Features:"
echo "  • Live data from API (auto-refresh every 60s)"
echo "  • 5 Politicians with FFT cycle analysis"
echo "  • HMM regime detection (High/Medium/Low activity)"
echo "  • 564 trades analyzed over 2-year period"
echo "  • Top 10 most traded stocks"
echo "  • Interactive Chart.js visualizations"
echo ""
echo "Press Ctrl+C to stop the API server when done."
echo ""
