# 🚀 Deployment Guide: 24/7 Autonomous Pattern Discovery

## Quick Start (5 minutes)

### 1. Setup Environment
```bash
# Clone and navigate
cd /mnt/e/projects/discovery

# Run setup script
./scripts/setup_environment.sh

# Activate virtual environment
source venv/bin/activate
```

### 2. Configure API Keys

Get cheap LLM API keys (pick at least one):

| Provider | Cost | Get API Key |
|----------|------|-------------|
| **DeepSeek** | $0.14/M tokens | https://platform.deepseek.com/ |
| Together AI | $0.20/M tokens | https://api.together.xyz/ |
| OpenRouter | $0.20/M tokens | https://openrouter.ai/ |
| Groq | FREE (limited) | https://console.groq.com/ |

Create `.env` file:
```bash
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

Minimum required in `.env`:
```bash
# At least ONE of these LLM API keys
DEEPSEEK_API_KEY=sk-xxxxx

# Database credentials
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quant_db
DB_USER=quant_user
DB_PASSWORD=your_password
```

### 3. Start the System
```bash
# Load environment
source .env

# Start 24/7 system
./scripts/start_autonomous_system.sh
```

You'll see:
```
================================================
Starting 24/7 Autonomous Pattern Discovery System
================================================
✅ Database connection successful
Starting orchestrator...
Logs will be written to: logs/orchestrator.log

=== Starting Analysis Cycle #1 ===
```

### 4. Monitor in Real-Time

Option A: View Logs
```bash
tail -f logs/orchestrator.log
```

Option B: Web Dashboard
```bash
# In another terminal, serve the dashboard
python3 -m http.server 8080 --directory monitoring

# Open browser to: http://localhost:8080/dashboard.html
```

## Understanding the Output

### Analysis Cycle Output
```
CYCLE #1 - 2025-11-27T10:30:00
================================================================================
Loaded 564 trades from database
ML detected 12 novel patterns
LLM analysis complete
Generated 5 hypotheses
Found 8 novel findings

✅ Cycle #1 SUCCESSFUL
   - Trades analyzed: 564
   - Novel findings: 8
   - Total discoveries: 8

Sleeping for 30.0 minutes...
```

### Discoveries File
All discoveries are saved to `data/patterns/discoveries.jsonl`:

```bash
# View latest discoveries
tail -10 data/patterns/discoveries.jsonl | jq
```

Example discovery:
```json
{
  "type": "llm_insight",
  "finding": {
    "insight": "Nancy Pelosi trades NVDA 48 hours before earnings 73% of the time",
    "significance": "high",
    "evidence": "8 out of 11 NVDA trades occurred within 48h of earnings announcements"
  },
  "timestamp": "2025-11-27T10:31:45"
}
```

### Status File
Check current status:
```bash
cat logs/status.json | jq
```

Output:
```json
{
  "running": true,
  "uptime_hours": 24.5,
  "total_cycles": 49,
  "successful_cycles": 48,
  "success_rate": 0.98,
  "analyst_stats": {
    "total_discoveries": 127,
    "llm_stats": {
      "total_cost": 0.0234,
      "total_requests": 98,
      "average_cost_per_request": 0.0002
    }
  }
}
```

## Production Deployment

### Option 1: Systemd Service (Recommended)

Create service file `/etc/systemd/system/discovery-autonomous.service`:

```ini
[Unit]
Description=24/7 Autonomous Pattern Discovery System
After=network.target postgresql.service

[Service]
Type=simple
User=your_user
WorkingDirectory=/mnt/e/projects/discovery
Environment="PATH=/mnt/e/projects/discovery/venv/bin"
EnvironmentFile=/mnt/e/projects/discovery/.env
ExecStart=/mnt/e/projects/discovery/venv/bin/python3 -m ai_agents.orchestrator_24x7
Restart=always
RestartSec=10
StandardOutput=append:/var/log/discovery/orchestrator.log
StandardError=append:/var/log/discovery/orchestrator.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable discovery-autonomous
sudo systemctl start discovery-autonomous
sudo systemctl status discovery-autonomous
```

View logs:
```bash
sudo journalctl -u discovery-autonomous -f
```

### Option 2: Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements_autonomous.txt .
RUN pip install --no-cache-dir -r requirements_autonomous.txt

# Copy source code
COPY ai_agents/ ai_agents/
COPY ml_models/ ml_models/
COPY data_pipeline/ data_pipeline/

# Create directories
RUN mkdir -p logs data/pipeline data/patterns

# Run orchestrator
CMD ["python3", "-m", "ai_agents.orchestrator_24x7"]
```

Build and run:
```bash
docker build -t discovery-autonomous .

docker run -d \
  --name discovery-24x7 \
  --restart unless-stopped \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  discovery-autonomous

# View logs
docker logs -f discovery-24x7
```

### Option 3: Docker Compose

Create `docker-compose.autonomous.yml`:
```yaml
version: '3.8'

services:
  discovery-autonomous:
    build: .
    container_name: discovery-24x7
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      - postgres
    networks:
      - discovery-net

  monitoring:
    image: nginx:alpine
    container_name: discovery-monitoring
    ports:
      - "8080:80"
    volumes:
      - ./monitoring:/usr/share/nginx/html:ro
    networks:
      - discovery-net

networks:
  discovery-net:
    driver: bridge
```

Run:
```bash
docker-compose -f docker-compose.autonomous.yml up -d
```

## Monitoring & Maintenance

### Daily Checks

```bash
# Check system status
cat logs/status.json | jq '.running, .success_rate, .total_discoveries'

# Check recent discoveries
tail -20 data/patterns/discoveries.jsonl | jq -r '.timestamp + " | " + .type'

# Check LLM costs
cat logs/status.json | jq '.analyst_stats.llm_stats'
```

### Weekly Tasks

```bash
# Review cost tracking
cat logs/status.json | jq '.analyst_stats.llm_stats'

# Cleanup old patterns (>30 days)
python3 -c "
from ai_agents.pattern_deduplicator import PatternDeduplicator
dedup = PatternDeduplicator()
dedup.cleanup_old_patterns(days_to_keep=30)
"

# Check log file size
du -h logs/orchestrator.log
```

### Monthly Tasks

```bash
# Rotate logs
mv logs/orchestrator.log logs/orchestrator.$(date +%Y%m).log
gzip logs/orchestrator.$(date +%Y%m).log

# Export discoveries for analysis
cat data/patterns/discoveries.jsonl | jq -s '.' > discoveries_$(date +%Y%m).json

# Review top patterns
cat data/patterns/discoveries.jsonl | jq -r '.type' | sort | uniq -c | sort -rn
```

## Troubleshooting

### System won't start

**Check database connection:**
```bash
python3 -c "
import psycopg2
import os
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    database=os.getenv('DB_NAME', 'quant_db'),
    user=os.getenv('DB_USER', 'quant_user'),
    password=os.getenv('DB_PASSWORD')
)
print('✅ Database OK')
conn.close()
"
```

**Check API keys:**
```bash
python3 -c "
import os
keys = ['DEEPSEEK_API_KEY', 'TOGETHER_API_KEY', 'OPENROUTER_API_KEY']
found = [k for k in keys if os.getenv(k)]
print(f'API keys found: {found}')
if not found:
    print('❌ No API keys set!')
else:
    print('✅ API keys OK')
"
```

### High failure rate

Check logs:
```bash
grep "ERROR\|FAILED" logs/orchestrator.log | tail -20
```

Common issues:
- **API rate limits**: Switch to different provider or reduce frequency
- **Database timeouts**: Check database performance
- **Memory issues**: Reduce `ANALYSIS_INTERVAL_MINUTES` or add more RAM

### High costs

Check provider usage:
```bash
cat logs/status.json | jq '.analyst_stats.llm_stats.provider_stats'
```

To reduce costs:
1. Set `DEEPSEEK_API_KEY` (cheapest at $0.14/M)
2. Increase `ANALYSIS_INTERVAL_MINUTES` (run less frequently)
3. Check if you're being rate-limited and falling back to expensive providers

### No discoveries

This is normal if:
- All patterns have been seen before (deduplication working)
- No significant changes in trading patterns
- System needs more time to observe new patterns

Check pattern count:
```bash
wc -l data/patterns/discoveries.jsonl
```

Force new analysis:
```bash
# Temporarily disable deduplication
export ENABLE_PATTERN_DEDUPLICATION=false
./scripts/start_autonomous_system.sh
```

## Performance Tuning

### Optimize for Cost
```bash
# .env settings for minimal cost
ANALYSIS_INTERVAL_MINUTES=60  # Run hourly instead of every 30min
DEEPSEEK_API_KEY=sk-xxx       # Use cheapest provider
```

Expected: **~$0.50/week**

### Optimize for Speed
```bash
# .env settings for maximum discoveries
ANALYSIS_INTERVAL_MINUTES=15  # Run every 15 minutes
GROQ_API_KEY=xxx              # Use fast (free) provider first
```

Expected: **~$2-3/week**

### Optimize for Quality
```bash
# .env settings for best analysis
ANALYSIS_INTERVAL_MINUTES=30
OPENROUTER_API_KEY=xxx        # Use Qwen-2.5-72B for quality
PATTERN_SIMILARITY_THRESHOLD=0.95  # Higher threshold = more unique patterns
```

Expected: **~$1-2/week**

## API Integration

The autonomous system automatically generates pipeline data for the API:

```bash
# Pipeline data is automatically created in:
data/pipeline/trades_YYYYMMDD_HHMMSS.json
data/pipeline/analytics_YYYYMMDD_HHMMSS.json
```

API endpoints use this data:
- `GET /api/v1/politicians`
- `GET /api/v1/trades`
- `GET /api/v1/stats`

## Security Considerations

1. **Never commit .env** - Already in .gitignore
2. **Rotate API keys monthly** - Set calendar reminder
3. **Monitor costs daily** - Set up alerts
4. **Restrict API access** - Use firewall rules
5. **Encrypt discoveries** - Consider encrypting sensitive findings

## Scaling

### Horizontal Scaling

Run multiple instances analyzing different aspects:

```bash
# Instance 1: Recent patterns (last 30 days)
ANALYSIS_FOCUS=recent ./scripts/start_autonomous_system.sh

# Instance 2: Historical patterns (all time)
ANALYSIS_FOCUS=historical ./scripts/start_autonomous_system.sh

# Instance 3: Real-time (last 24 hours)
ANALYSIS_FOCUS=realtime ./scripts/start_autonomous_system.sh
```

### Vertical Scaling

For larger datasets:

```bash
# Increase analysis interval
ANALYSIS_INTERVAL_MINUTES=60

# Or add more resources
docker run --memory=4g --cpus=2 discovery-autonomous
```

## Backup & Recovery

### Backup Discoveries

```bash
# Daily backup
cp data/patterns/discoveries.jsonl \
   backups/discoveries_$(date +%Y%m%d).jsonl

# Compress old backups
find backups/ -name "*.jsonl" -mtime +7 -exec gzip {} \;
```

### Restore from Backup

```bash
# Stop system
sudo systemctl stop discovery-autonomous

# Restore discoveries
cp backups/discoveries_20251127.jsonl data/patterns/discoveries.jsonl

# Restart
sudo systemctl start discovery-autonomous
```

## Next Steps

1. ✅ Get LLM API keys
2. ✅ Configure .env
3. ✅ Start the system
4. ✅ Monitor for 24 hours
5. ⏳ Review first discoveries
6. ⏳ Tune parameters based on results
7. ⏳ Set up production deployment
8. ⏳ Configure alerts
9. ⏳ Schedule backups

## Support

- **Documentation**: See README_AUTONOMOUS.md
- **Logs**: Check logs/orchestrator.log
- **Status**: View logs/status.json
- **Issues**: Create GitHub issue

---

**System Ready**: The autonomous pattern discovery system is now configured and ready to run 24/7, continuously finding novel trading patterns at minimal cost.

**Estimated Weekly Cost**: $1-5 (depending on configuration)

**Expected Discoveries**: 50-200 per week (after deduplication)
