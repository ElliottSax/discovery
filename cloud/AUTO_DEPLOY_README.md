# Automated Worker Deployment

**Deploy free compute workers automatically with one command!**

## Quick Start (HuggingFace - Recommended)

```bash
cd /mnt/e/projects/discovery/cloud/setup
python3 deploy_huggingface.py
```

This will:
1. Ask for your HuggingFace token
2. Create worker spaces automatically
3. Upload all necessary files
4. Wait for deployment
5. Add workers to your `.env` file
6. Test the workers

**Time**: ~5 minutes for 2-3 workers

---

## What You Need

### HuggingFace Token (One-time setup - 2 min)

1. Go to: **https://huggingface.co/settings/tokens**
   - Log in or create account (free, no credit card)

2. Click "New token"
   - Name: `discovery-workers`
   - Type: **Write**
   - Click "Generate"

3. Copy the token (looks like: `hf_xxxxxxxxxxxxx`)

4. Keep it handy for the script!

---

## Automated Deployment

### Option 1: Interactive Menu

```bash
cd /mnt/e/projects/discovery/cloud/setup
python3 deploy_workers.py
```

Shows menu with all platforms:
```
🚀 Free Compute Worker Deployment

Available platforms:

  1. HuggingFace Spaces  (⭐ Recommended)
     • 2 cores, 16GB RAM per worker
     • Unlimited workers
     • 24/7 uptime
     • Automated deployment ✅

  2. Google Colab (GPU)
     • T4 GPU, 2 cores, 13GB RAM
     • Manual setup (15 min)
     • 12h sessions

  3. Railway
     ...

Select platform [1-5, 0 to exit]:
```

### Option 2: Direct Deployment

```bash
# Deploy to HuggingFace automatically
python3 deploy_workers.py --auto

# Or specify platform
python3 deploy_workers.py --platform hf
```

---

## Full Walkthrough

### Step 1: Run the Script

```bash
cd /mnt/e/projects/discovery/cloud/setup
python3 deploy_huggingface.py
```

### Step 2: Authenticate

```
═══════════════════════════════════════════════════════════════════════
HuggingFace Authentication
═══════════════════════════════════════════════════════════════════════

To deploy workers, you need a HuggingFace token.

Steps:
1. Go to: https://huggingface.co/settings/tokens
2. Create a new token with 'write' permissions
3. Copy and paste it below

Enter your HuggingFace token: hf_xxxxxxxxxxxxx
ℹ️  Verifying token...
✅ Authenticated as: your_username
```

### Step 3: Choose Number of Workers

```
How many workers do you want to deploy?
  • Each worker: 2 cores, 16GB RAM
  • You can deploy unlimited workers
  • Recommended: Start with 2-3

Number of workers [1-10]: 2
```

### Step 4: Watch Deployment

```
═══════════════════════════════════════════════════════════════════════
Deploying Worker #1
═══════════════════════════════════════════════════════════════════════

ℹ️  Creating space: discovery-worker-1...
✅ Space created: your_username/discovery-worker-1
ℹ️  Uploading files to your_username/discovery-worker-1...
✅ Uploaded: app.py
✅ Uploaded: requirements.txt
✅ Uploaded: README.md
✅ Worker URL: https://your_username-discovery-worker-1.hf.space
ℹ️  Waiting for space to build (max 300s)...
  Building... 45s / 300s
✅ Space is live!
✅ Added to .env: HUGGINGFACE_WORKER_1
✅ Worker #1 deployed successfully!

Test with: curl https://your_username-discovery-worker-1.hf.space/health

[... repeats for worker #2 ...]
```

### Step 5: Deployment Complete!

```
═══════════════════════════════════════════════════════════════════════
Deployment Complete
═══════════════════════════════════════════════════════════════════════

Successfully deployed: 2/2 workers

Your workers are now available!

Next steps:
  1. Test workers: python3 cloud/monitor/check_all_workers.py
  2. View .env file to see worker URLs

Total compute added: 4 cores, 32 GB RAM
```

---

## What Gets Created

For each worker, the script:

1. **Creates HuggingFace Space**
   - Name: `discovery-worker-1`, `discovery-worker-2`, etc.
   - SDK: Gradio
   - Hardware: CPU basic (free)

2. **Uploads Files**
   - `app.py` - Worker application
   - `requirements.txt` - Dependencies
   - `README.md` - Documentation

3. **Waits for Build**
   - HuggingFace builds the space (~2 min)
   - Script waits until worker is live

4. **Updates .env**
   ```bash
   HUGGINGFACE_WORKER_1=https://username-discovery-worker-1.hf.space
   HUGGINGFACE_WORKER_2=https://username-discovery-worker-2.hf.space
   ```

5. **Tests Worker**
   - Verifies `/health` endpoint responds
   - Confirms worker is operational

---

## Verify Deployment

### Test Individual Worker

```bash
curl https://your-username-discovery-worker-1.hf.space/health
```

Should return:
```json
{
  "status": "healthy",
  "worker_type": "general",
  "compute_platform": "huggingface_spaces",
  "available_analyses": [
    "sentiment",
    "volume_analysis",
    "price_patterns",
    "basic_stats"
  ]
}
```

### Test All Workers

```bash
python3 cloud/monitor/check_all_workers.py
```

Output:
```
╔════════════════════════════════════════════════════════════════════╗
║                     Worker Status Report                          ║
╚════════════════════════════════════════════════════════════════════╝

HUGGINGFACE_SPACES
──────────────────────────────────────────────────────────────────────
✅ https://username-discovery-worker-1.hf.space
   Type: general | Response: 0.234s
✅ https://username-discovery-worker-2.hf.space
   Type: general | Response: 0.189s

Summary
Total Workers: 2
Healthy: 2
Availability: 100%

Available Resources
CPU Cores: ~4
RAM: ~32 GB
GPUs: 0
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'huggingface_hub'"

The script will auto-install it, but you can also install manually:
```bash
pip install huggingface_hub
```

### "Invalid token"

1. Check token has **Write** permissions (not Read)
2. Get new token: https://huggingface.co/settings/tokens
3. Make sure you copied the entire token

### "Space already exists"

If you run the script multiple times, it will detect existing spaces and update them instead of failing.

### Space build fails

1. Check build logs in HuggingFace UI
2. Verify files are correct:
   ```bash
   ls cloud/huggingface/
   # Should show: app.py, requirements.txt, README.md
   ```
3. Try deleting the space and running script again

### Worker not responding after deployment

1. Wait 30 seconds - space may be sleeping
2. Make a request to wake it up:
   ```bash
   curl https://your-space.hf.space/
   ```
3. Check space logs in HuggingFace UI

---

## Advanced Usage

### Deploy Specific Number of Workers

```python
# In Python
from deploy_huggingface import deploy_worker, get_hf_token

token, username = get_hf_token()

# Deploy 5 workers
for i in range(1, 6):
    deploy_worker(token, username, i)
```

### Update Existing Workers

Just run the script again - it will update existing spaces with new code.

### Delete Workers

1. Go to: https://huggingface.co/spaces
2. Find your workers
3. Settings > Delete space

Or via CLI:
```bash
# Install huggingface-cli
pip install huggingface_hub[cli]

# Delete space
huggingface-cli delete your-username/discovery-worker-1 --type space
```

---

## Comparison: Manual vs Automated

| Method | Time | Difficulty | Workers |
|--------|------|------------|---------|
| **Manual** | 10 min/worker | Medium | 1 at a time |
| **Automated** | 5 min total | Easy | Unlimited |

**Automated wins!** 🎉

---

## Next Steps After Deployment

### 1. Test Workers

```bash
python3 cloud/monitor/check_all_workers.py
```

### 2. Run Analysis

```python
import requests
import os

worker = os.getenv('HUGGINGFACE_WORKER_1')

response = requests.post(f"{worker}/analyze", json={
    "trades": [
        {"price": 100, "volume": 1000, "price_change": 2.5},
        {"price": 102.5, "volume": 1500, "price_change": 1.2}
    ],
    "analysis_types": ["sentiment", "volume_analysis"]
})

print(response.json())
```

### 3. Scale Up

Need more compute? Run the script again to deploy more workers:
```bash
python3 deploy_huggingface.py
# Enter your token
# Enter number of additional workers
```

### 4. Monitor Usage

HuggingFace provides analytics:
- Go to your space
- Click "Analytics" tab
- See requests, uptime, etc.

---

## Summary

**Before**: Manual deployment, 10 min per worker, error-prone

**After**: Automated deployment, 5 min for unlimited workers, bulletproof

**Command**:
```bash
python3 cloud/setup/deploy_huggingface.py
```

**Result**: Free compute workers deployed automatically! 🚀

---

## Quick Reference

```bash
# Deploy HuggingFace workers (automated)
python3 cloud/setup/deploy_huggingface.py

# Deploy via menu (all platforms)
python3 cloud/setup/deploy_workers.py

# Deploy HuggingFace directly
python3 cloud/setup/deploy_workers.py --auto

# Test all workers
python3 cloud/monitor/check_all_workers.py

# Check Oracle auto-provisioning
tail -f ~/.oracle_auto_provision/provision.log
```

Get your HuggingFace token: https://huggingface.co/settings/tokens

Deploy workers in 5 minutes! 🎉
