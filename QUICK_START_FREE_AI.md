# 🚀 QUICK START: FREE AI

## Get Full AI Power in 10 Minutes (FREE!)

### Option 1: Groq (Fastest - 2 minutes) ⚡

**Speed:** 500+ tokens/second (10x faster than GPT-4)
**Cost:** $0 (FREE tier)
**Quality:** Llama 3 70B (rivals GPT-4)

```bash
# 1. Get API key (2 minutes)
# Visit: https://console.groq.com
# Sign up with GitHub/Google
# Copy API key

# 2. Set environment variable
export GROQ_API_KEY="gsk_..."

# 3. Restart ULTRATHINK
kill $(cat logs/orchestrator.pid)
export DB_HOST=localhost \
&& export DB_PORT=5432 \
&& export DB_NAME=quant_db \
&& export DB_USER=quant_user \
&& export DB_PASSWORD='YOUR_DB_PASSWORD' \
&& export GROQ_API_KEY="gsk_..." \
&& nohup python3 -m ai_agents.orchestrator_24x7 > logs/orchestrator.log 2>&1 & echo $!

# 4. Verify
tail -f logs/orchestrator.log | grep -i "groq\|hypothesis"
```

**Result:** 10 hypotheses per cycle, AI pattern discovery, deep analysis - ALL FREE! 🎉

---

### Option 2: Ollama (Unlimited - 10 minutes) 🖥️

**Speed:** 20-50 tokens/second
**Cost:** $0 (runs on your machine)
**Quality:** Llama 3 8B (rivals GPT-3.5)
**Privacy:** 100% local, no data leaves machine

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Download model
ollama pull llama3:8b  # 4.7GB download

# 3. Test
ollama run llama3:8b "What is 2+2?"

# 4. Restart ULTRATHINK (auto-detects Ollama)
kill $(cat logs/orchestrator.pid)
export DB_HOST=localhost \
&& export DB_PORT=5432 \
&& export DB_NAME=quant_db \
&& export DB_USER=quant_user \
&& export DB_PASSWORD='YOUR_DB_PASSWORD' \
&& nohup python3 -m ai_agents.orchestrator_24x7 > logs/orchestrator.log 2>&1 & echo $!

# 5. Verify
tail -f logs/orchestrator.log | grep -i "ollama\|hypothesis"
```

**Result:** Unlimited queries, complete privacy, zero API costs! 🎉

---

### Option 3: Both (Best - 12 minutes) 🔥

Combine Groq (fast) + Ollama (unlimited) for maximum power:

```bash
# 1. Get Groq API key
export GROQ_API_KEY="gsk_..."

# 2. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3:8b

# 3. Restart ULTRATHINK with both
kill $(cat logs/orchestrator.pid)
export DB_HOST=localhost \
&& export DB_PORT=5432 \
&& export DB_NAME=quant_db \
&& export DB_USER=quant_user \
&& export DB_PASSWORD='YOUR_DB_PASSWORD' \
&& export GROQ_API_KEY="gsk_..." \
&& nohup python3 -m ai_agents.orchestrator_24x7 > logs/orchestrator.log 2>&1 & echo $!
```

**Result:** Groq for primary (fast), Ollama as unlimited fallback - BEST setup! 🚀

---

## What You Get (FREE)

### Before (No AI):
```
✅ ML detected 24 novel patterns
⚠️  DeepSeek generated 0 hypotheses
⚠️  AI discovered 0 novel patterns
✅ Found 24 novel findings
```

### After (With Groq/Ollama):
```
✅ ML detected 24 novel patterns
✅ DeepSeek generated 10 hypotheses ⭐
✅ AI discovered 5 novel patterns ⭐
✅ Deep analysis of 3 high-priority patterns ⭐
✅ Found 35+ novel findings
```

---

## Verification

Check if AI is working:

```bash
# Check logs
tail -50 logs/orchestrator.log | grep -i "generated\|hypothesis\|groq\|ollama"

# Should see:
# "DeepSeek generated 10 hypotheses" (not 0)
# "AI discovered X novel patterns" (not 0)
# "Generated response using groq" (not "local fallback")
```

---

## Expected Output (With Free AI)

```json
{
  "hypotheses": [
    {
      "id": "H001",
      "hypothesis": "Nancy Pelosi trades NVDA 2-5 days before earnings",
      "evidence": "87% of NVDA trades in this window",
      "likelihood": 0.82,
      "statistical_significance": 0.95
    },
    {
      "id": "H002",
      "hypothesis": "Synchronized trading between senators on tech committee",
      "evidence": "8 senators traded MSFT within 48 hours",
      "likelihood": 0.91,
      "statistical_significance": 0.98
    }
    // ... 8 more hypotheses
  ],
  "ai_novel_patterns": [
    {
      "pattern_name": "End-of-month portfolio rebalancing",
      "description": "Consistent sell pattern last 3 days of month",
      "significance": "high",
      "profit_potential": "Tax optimization strategy"
    }
    // ... more AI-discovered patterns
  ]
}
```

---

## Troubleshooting

### Groq Not Working

```bash
# Check API key
echo $GROQ_API_KEY  # Should show gsk_...

# Test directly
curl https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama-3.1-70b-versatile", "messages": [{"role": "user", "content": "test"}]}'
```

### Ollama Not Working

```bash
# Check if running
ollama list

# If not running, start it
ollama serve

# Test
ollama run llama3:8b "test"

# Check port
curl http://localhost:11434/api/tags
```

---

## Cost Comparison

| Setup | Monthly Cost | Hypotheses/Cycle | Quality |
|-------|-------------|------------------|---------|
| None (current) | $0 | 0 | N/A |
| Groq only | **$0** | 10-50 | Excellent |
| Ollama only | **$0** | Unlimited | Good |
| Both | **$0** | Unlimited | Excellent |
| DeepSeek | $1-2 | 10-100 | World-class |
| All combined | $5-10 | 100+ | Best possible |

**Recommendation:** Start with Groq (FREE, 2 min setup) ✨

---

## Next Steps After AI Activation

1. **Monitor discoveries:** `tail -f logs/orchestrator.log`
2. **Check knowledge base:** `cat data/patterns/knowledge_base.json`
3. **View hypotheses:** `cat data/patterns/discoveries.jsonl | grep hypothesis`
4. **Add more models:** `ollama pull mixtral:8x7b` (better reasoning)
5. **Increase frequency:** Change `ANALYSIS_INTERVAL_MINUTES=5` (currently 30)

---

## Advanced: Multiple Ollama Models

Run different models for different tasks:

```bash
# Fast model for simple tasks
ollama pull llama3:8b  # 4.7GB

# Best quality for complex reasoning
ollama pull llama3:70b  # 40GB (requires 48GB RAM)

# Best for code/technical analysis
ollama pull deepseek-coder:6.7b  # 3.8GB

# Best reasoning
ollama pull mixtral:8x7b  # 26GB

# Use in ULTRATHINK (auto-selects best available)
```

---

## FAQ

**Q: Is Groq really free?**
A: Yes! Free tier allows 30 requests/minute (enough for ULTRATHINK).

**Q: Will Ollama slow down my computer?**
A: Uses ~4-8GB RAM during inference. Set lower priority if needed:
```bash
ollama serve &  # Runs in background
renice -n 10 $(pgrep ollama)  # Lower priority
```

**Q: Can I use both Groq and paid APIs?**
A: Yes! LLM router uses Groq first (free), then falls back to DeepSeek if rate-limited.

**Q: How do I know which provider is being used?**
A: Check logs: `grep "Generated response using" logs/orchestrator.log`

**Q: What if Groq rate-limits me?**
A: Router automatically falls back to Ollama (unlimited).

---

## Support

- **Groq:** https://console.groq.com
- **Ollama:** https://ollama.com
- **ULTRATHINK Issues:** Check logs at `logs/orchestrator.log`

---

*Generated with [Claude Code](https://claude.com/claude-code)*
