# 24/7 Autonomous Pattern Discovery System

## 🚀 Overview

This is an **autonomous, 24/7 pattern discovery system** that continuously analyzes politician trading data to find novel, significant patterns and models in the stock market. It uses:

- **Cheap LLM APIs** (DeepSeek, OpenRouter, Alibaba Qwen, Together AI, Groq) to minimize costs
- **Advanced ML models** (LSTM, Transformers, Ensemble methods) for pattern detection
- **Autonomous agents** that run continuously without human intervention
- **Intelligent deduplication** to identify only truly novel patterns
- **Real-time monitoring** with cost tracking

## 💰 Cost Optimization

The system is designed to run 24/7 at **minimal cost**:

- **DeepSeek**: $0.14/M tokens (primary)
- **Together AI**: $0.20/M tokens (backup)
- **Qwen (via OpenRouter)**: $0.20/M tokens (backup)
- **Groq**: Free tier (backup)
- **Local**: Free fallback

Expected cost: **~$1-5 per week** depending on usage.

## 📁 Architecture

```
discovery/
├── ai_agents/
│   ├── llm_router.py              # Routes to cheapest LLM API
│   ├── autonomous_analyst.py       # Core analysis agent
│   ├── orchestrator_24x7.py        # 24/7 orchestrator
│   └── pattern_deduplicator.py     # Prevents duplicates
├── ml_models/
│   └── advanced_models.py          # LSTM, Transformers, Ensemble
├── data_pipeline/
│   └── db_to_pipeline.py           # Database to pipeline converter
├── monitoring/
│   └── dashboard.html              # Real-time monitoring dashboard
├── logs/
│   ├── orchestrator.log            # System logs
│   ├── status.json                 # Current status
│   └── alerts.jsonl                # Alert history
└── data/
    ├── pipeline/                   # Pipeline JSON files
    └── patterns/
        └── discoveries.jsonl        # All discoveries
```

## 🛠️ Setup

### 1. Install Dependencies

```bash
./scripts/setup_environment.sh
```

### 2. Configure Environment

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add at least one LLM API key:

```bash
# Get cheap API keys:
# DeepSeek: https://platform.deepseek.com/ ($0.14/M tokens!)
# Together: https://api.together.xyz/
# OpenRouter: https://openrouter.ai/
# Groq: https://console.groq.com/

DEEPSEEK_API_KEY=your_key_here
TOGETHER_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

### 3. Verify Database Connection

The system needs access to your PostgreSQL database:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=quant_db
export DB_USER=quant_user
export DB_PASSWORD=your_password
```

## 🚦 Usage

### Start the 24/7 System

```bash
./scripts/start_autonomous_system.sh
```

The system will:
1. ✅ Check database connection
2. ✅ Verify API keys
3. ✅ Start autonomous analysis cycles
4. ✅ Run every 30 minutes (configurable)
5. ✅ Log all activities
6. ✅ Store novel discoveries

### Monitor in Real-Time

Open the monitoring dashboard:

```bash
# Serve the dashboard
python3 -m http.server 8080 --directory monitoring

# Then open in browser:
# http://localhost:8080/dashboard.html
```

The dashboard shows:
- System status and uptime
- Total discoveries
- LLM cost tracking
- Recent discoveries
- Real-time logs

### Run Single Analysis (Testing)

```bash
# Test autonomous analyst
python3 -m ai_agents.autonomous_analyst

# Test LLM router
python3 -m ai_agents.llm_router

# Test pipeline generation
python3 -m data_pipeline.db_to_pipeline
```

## 🧠 How It Works

### Analysis Cycle (every 30 minutes)

1. **Load Data**: Fetch latest trades from database
2. **ML Analysis**: Run LSTM, Transformers, Ensemble models
3. **LLM Analysis**: Use cheap LLMs to interpret patterns
4. **Generate Hypotheses**: Create testable hypotheses
5. **Extract Novel Patterns**: Deduplicate and identify significant findings
6. **Store Discoveries**: Save to JSONL file
7. **Generate Pipeline Data**: Update API data files

### Pattern Detection Methods

#### 1. LSTM Pattern Detector
- Detects temporal patterns in individual politician trading
- Identifies burst trading, Monday effects, directional bias
- Analyzes trade velocity and clustering

#### 2. Transformer Attention Analyzer
- Finds synchronized trading across politicians
- Detects mimicry patterns (politicians copying each other)
- Cross-correlation analysis

#### 3. LLM Deep Analysis
- Interprets statistical patterns
- Generates insights and hypotheses
- Identifies suspicious behaviors
- Suggests correlations

### Novel Discovery Criteria

A pattern is considered "novel" if:
- Not seen in previous 30 days
- Similarity score < 90% to existing patterns
- High significance score (>0.7)
- Unique combination of factors

## 📊 Output Files

### discoveries.jsonl
All novel patterns discovered:
```json
{
  "type": "llm_insight",
  "finding": {
    "insight": "Multiple senators trading NVDA before earnings",
    "significance": "high",
    "evidence": "..."
  },
  "timestamp": "2025-11-27T10:30:00"
}
```

### status.json
Current system status:
```json
{
  "running": true,
  "uptime_hours": 24.5,
  "total_cycles": 49,
  "success_rate": 0.98,
  "analyst_stats": {
    "total_discoveries": 127,
    "llm_stats": {
      "total_cost": 0.0234,
      "total_requests": 98
    }
  }
}
```

## 🔍 Example Discoveries

The system can discover patterns like:

1. **Temporal Patterns**
   - "Nancy Pelosi trades 80% on Mondays before 10am"
   - "Ted Cruz has burst trading with 3-day clusters"

2. **Synchronized Trading**
   - "5 senators bought NVDA within 48 hours before earnings"
   - "Cross-party coordination on tech stock purchases"

3. **Mimicry Patterns**
   - "Senator A copies Senator B's trades with 2-week lag"
   - "70% portfolio overlap between unlikely pairs"

4. **Anomalies**
   - "Unusual trade volume 1 week before FDA approval"
   - "Concentrated selling before market downturn"

## 🚨 Alerting

The system alerts on:
- **Critical failures**: 5+ consecutive analysis failures
- **Significant discoveries**: 5+ novel patterns in one cycle
- **Cost overruns**: If LLM costs exceed threshold
- **Database issues**: Connection failures

Alerts are logged to `logs/alerts.jsonl`.

## ⚙️ Configuration

Edit these in `.env`:

```bash
# How often to run analysis (minutes)
ANALYSIS_INTERVAL_MINUTES=30

# Max consecutive failures before alerting
MAX_CONSECUTIVE_FAILURES=5

# Logging level
LOG_LEVEL=INFO
```

## 🔧 Maintenance

### View Logs
```bash
tail -f logs/orchestrator.log
```

### View Status
```bash
cat logs/status.json | jq
```

### View Discoveries
```bash
tail -20 data/patterns/discoveries.jsonl | jq
```

### Cleanup Old Patterns (30+ days)
```bash
python3 -c "
from ai_agents.pattern_deduplicator import PatternDeduplicator
dedup = PatternDeduplicator()
dedup.cleanup_old_patterns(days_to_keep=30)
"
```

## 🐳 Deploy with Docker (Optional)

```bash
# Build image
docker build -t discovery-autonomous .

# Run with environment
docker run -d \
  --name discovery-24x7 \
  --env-file .env \
  --restart unless-stopped \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  discovery-autonomous
```

## 📈 Performance

Expected metrics:
- **Analysis time**: 2-5 minutes per cycle
- **Memory usage**: 100-500 MB
- **CPU usage**: <10% average
- **Storage**: ~1 MB per day of discoveries
- **Cost**: $1-5 per week in LLM API calls

## 🤝 Contributing

This autonomous system is extensible. Add your own:
- Detection algorithms in `ml_models/`
- LLM providers in `llm_router.py`
- Analysis methods in `autonomous_analyst.py`

## 📝 License

See main project LICENSE.

## 🙏 Credits

Built with:
- DeepSeek for ultra-cheap LLM inference
- PostgreSQL for data storage
- PyTorch for ML models
- FastAPI for monitoring

---

**Status**: 🟢 Production Ready

**Version**: 1.0.0

**Last Updated**: 2025-11-27
