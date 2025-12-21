#!/bin/bash
# Comprehensive system validation script

set -e

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║          ULTRATHINK SYSTEM VALIDATION & TESTING                  ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

PASS=0
FAIL=0
WARN=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

pass() {
    echo -e "   ${GREEN}✓${NC} $1"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "   ${RED}✗${NC} $1"
    FAIL=$((FAIL + 1))
}

warn() {
    echo -e "   ${YELLOW}⚠${NC} $1"
    WARN=$((WARN + 1))
}

# Test 1: Database Connection
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: Database Connection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python3 -c "
import psycopg2
import os
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 5432)),
    database=os.getenv('DB_NAME', 'quant_db'),
    user=os.getenv('DB_USER', 'quant_user'),
    password=os.getenv('DB_PASSWORD')
)
conn.close()
" 2>/dev/null; then
    pass "PostgreSQL connection successful"
else
    fail "PostgreSQL connection failed"
fi

# Test 2: Trade Data
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: Database Trade Data"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TRADE_COUNT=$(python3 -c "
import psycopg2, os
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 5432)),
    database=os.getenv('DB_NAME', 'quant_db'),
    user=os.getenv('DB_USER', 'quant_user'),
    password=os.getenv('DB_PASSWORD')
)
with conn.cursor() as cur:
    cur.execute('SELECT COUNT(*) FROM trades')
    print(cur.fetchone()[0])
conn.close()
" 2>/dev/null)

if [ "$TRADE_COUNT" -gt 0 ]; then
    pass "Found $TRADE_COUNT trades in database"
else
    fail "No trades found in database"
fi

POL_COUNT=$(python3 -c "
import psycopg2, os
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 5432)),
    database=os.getenv('DB_NAME', 'quant_db'),
    user=os.getenv('DB_USER', 'quant_user'),
    password=os.getenv('DB_PASSWORD')
)
with conn.cursor() as cur:
    cur.execute('SELECT COUNT(*) FROM politicians')
    print(cur.fetchone()[0])
conn.close()
" 2>/dev/null)

if [ "$POL_COUNT" -gt 0 ]; then
    pass "Found $POL_COUNT politicians in database"
else
    fail "No politicians found in database"
fi

# Test 3: Orchestrator Process
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: Orchestrator Process"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if pgrep -f "orchestrator_24x7" > /dev/null; then
    PID=$(pgrep -f "orchestrator_24x7" | tail -1)
    pass "Orchestrator running (PID: $PID)"
else
    warn "Orchestrator not running (start with ./scripts/start_autonomous_system.sh)"
fi

# Test 4: File Generation
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: Output Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "data/patterns/discoveries.jsonl" ]; then
    DISC_COUNT=$(wc -l < data/patterns/discoveries.jsonl)
    if [ "$DISC_COUNT" -gt 0 ]; then
        pass "Discoveries file exists ($DISC_COUNT discoveries)"
    else
        warn "Discoveries file empty"
    fi
else
    fail "Discoveries file not found"
fi

if [ -d "data/pipeline" ]; then
    TRADE_FILES=$(ls -1 data/pipeline/trades_*.json 2>/dev/null | wc -l)
    if [ "$TRADE_FILES" -gt 0 ]; then
        pass "Pipeline trade files exist ($TRADE_FILES files)"
    else
        warn "No pipeline trade files"
    fi
else
    fail "Pipeline directory not found"
fi

if [ -f "logs/orchestrator.log" ]; then
    pass "Orchestrator log exists"
else
    warn "Orchestrator log not found"
fi

if [ -f "logs/status.json" ]; then
    pass "Status file exists"
else
    warn "Status file not found"
fi

# Test 5: Pattern Detection
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 5: Pattern Detection Components"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test ML models can import
if python3 -c "from ml_models.advanced_models import EnsemblePatternDetector" 2>/dev/null; then
    pass "ML models import successfully"
else
    fail "ML models import failed"
fi

# Test LLM router
if python3 -c "from ai_agents.llm_router import get_llm_router; router = get_llm_router(); assert len(router.get_available_providers()) > 0" 2>/dev/null; then
    pass "LLM router functional"
else
    fail "LLM router failed"
fi

# Test deduplicator
if python3 -c "from ai_agents.pattern_deduplicator import PatternDeduplicator; dedup = PatternDeduplicator(); assert dedup is not None" 2>/dev/null; then
    pass "Pattern deduplicator functional"
else
    fail "Pattern deduplicator failed"
fi

# Test 6: Discovery Quality
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 6: Discovery Quality Checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "data/patterns/discoveries.jsonl" ]; then
    # Check for different pattern types
    MIMICRY=$(grep -c '"type".*"mimicry"' data/patterns/discoveries.jsonl || echo "0")
    SYNCHRONIZED=$(grep -c '"type".*"synchronized"' data/patterns/discoveries.jsonl || echo "0")
    BURST=$(grep -c '"type".*"burst"' data/patterns/discoveries.jsonl || echo "0")

    if [ "$MIMICRY" -gt 0 ]; then
        pass "Mimicry patterns detected ($MIMICRY)"
    else
        warn "No mimicry patterns found"
    fi

    if [ "$SYNCHRONIZED" -gt 0 ]; then
        pass "Synchronized trading detected ($SYNCHRONIZED)"
    else
        warn "No synchronized trading found"
    fi

    if [ "$BURST" -gt 0 ]; then
        pass "Burst trading patterns detected ($BURST)"
    else
        warn "No burst trading found"
    fi

    # Check JSON validity
    if python3 -c "
import json
with open('data/patterns/discoveries.jsonl') as f:
    for line in f:
        json.loads(line.strip())
" 2>/dev/null; then
        pass "All discoveries are valid JSON"
    else
        fail "Invalid JSON in discoveries"
    fi
fi

# Test 7: System Health
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 7: System Health Metrics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "logs/status.json" ]; then
    SUCCESS_RATE=$(python3 -c "import json; print(json.load(open('logs/status.json'))['success_rate']*100)" 2>/dev/null || echo "0")

    if python3 -c "exit(0 if float('$SUCCESS_RATE') >= 90 else 1)" 2>/dev/null; then
        pass "Success rate: ${SUCCESS_RATE}%"
    elif python3 -c "exit(0 if float('$SUCCESS_RATE') >= 50 else 1)" 2>/dev/null; then
        warn "Success rate: ${SUCCESS_RATE}%"
    else
        fail "Success rate: ${SUCCESS_RATE}%"
    fi

    TOTAL_DISCOVERIES=$(python3 -c "import json; print(json.load(open('logs/status.json'))['analyst_stats']['total_discoveries'])" 2>/dev/null || echo "0")

    if [ "$TOTAL_DISCOVERIES" -gt 0 ]; then
        pass "Total discoveries: $TOTAL_DISCOVERIES"
    else
        warn "No discoveries yet"
    fi
fi

# Test 8: Error Checks
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 8: Error Monitoring"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "logs/orchestrator.log" ]; then
    ERROR_COUNT=$(grep -c "ERROR" logs/orchestrator.log || echo "0")
    WARNING_COUNT=$(grep -c "WARNING" logs/orchestrator.log || echo "0")

    if [ "$ERROR_COUNT" -eq 0 ]; then
        pass "No errors in logs"
    else
        warn "Found $ERROR_COUNT errors in logs"
    fi

    if [ "$WARNING_COUNT" -lt 10 ]; then
        pass "Minimal warnings ($WARNING_COUNT)"
    else
        warn "Many warnings in logs ($WARNING_COUNT)"
    fi
fi

# Summary
echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                      VALIDATION SUMMARY                           ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${YELLOW}Warnings: $WARN${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ "$FAIL" -eq 0 ]; then
    echo "✅ System is HEALTHY and operating normally"
    exit 0
elif [ "$FAIL" -lt 3 ]; then
    echo "⚠️  System is operational with minor issues"
    exit 0
else
    echo "❌ System has critical issues requiring attention"
    exit 1
fi
