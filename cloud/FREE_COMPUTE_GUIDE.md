# Free Compute Resources Guide

Complete guide to setting up free computing resources for the Discovery platform

## Summary - Total Free Resources Available

| Platform | CPU | RAM | GPU | Storage | Runtime | Setup Time |
|----------|-----|-----|-----|---------|---------|------------|
| **Oracle Cloud** | 4 ARM cores | 24 GB | None | 200 GB | 24/7 | 30-60 min |
| **HuggingFace Spaces** | 2 cores × N | 16 GB × N | Optional | 50 GB | 24/7* | 10 min |
| **Google Colab** | 2 cores | 13 GB | T4 (16GB) | 78 GB | 12 hours | 5 min |
| **Kaggle Kernels** | 4 cores | 13 GB | P100/T4 | 73 GB | 9h GPU/week | 10 min |
| **Railway** | 0.5 vCPU | 512 MB | None | 1 GB | 24/7 | 5 min |
| **Render** | Shared | 512 MB | None | Shared | 24/7* | 5 min |
| **Fly.io** | 1 shared | 256 MB | None | 3 GB | 24/7 | 10 min |
| **Replit** | 0.5 vCPU | 512 MB | None | 1 GB | 24/7* | 5 min |

\* May sleep after inactivity

## 1. Oracle Cloud (★★★★★)

**Best for:** Primary worker nodes, 24/7 compute

### Resources (Always Free)
- **4 ARM cores** (Ampere A1)
- **24 GB RAM** (configurable across instances)
- **200 GB storage**
- **10 TB/month bandwidth**
- **2 AMD x86 instances** (1/8 OCPU, 1GB RAM each)

### Setup
```bash
cd /mnt/e/projects/discovery/cloud/setup
./setup_oracle_cloud.sh
```

See `ORACLE_QUICKSTART.md` for detailed instructions.

### Status
```bash
./cloud/oracle_status.sh
```

### Current Setup
- ✅ 2 workers active: `163.192.110.147`, `163.192.103.233`
- 📊 Running on A2.Flex and E5.Flex shapes
- 🎯 Can add 2-4 more A1.Flex instances (Always Free tier)

### Pros
- Truly free forever
- High performance ARM processors
- 24/7 uptime
- Generous resource limits

### Cons
- Setup complexity
- Capacity constraints (ARM instances often unavailable)
- Geographic restrictions

---

## 2. HuggingFace Spaces (★★★★☆)

**Best for:** Multiple persistent workers, API endpoints

### Resources (Free)
- **2 vCPU cores**
- **16 GB RAM**
- **50 GB storage**
- Can create **unlimited spaces**

### Setup

1. **Sign up**: https://huggingface.co/join

2. **Create Space**:
   - Go to: https://huggingface.co/new-space
   - Name: `discovery-worker-1`
   - SDK: Gradio
   - Hardware: CPU basic (free)

3. **Upload files** from `cloud/huggingface/`:
   - `app.py`
   - `requirements.txt`
   - `README.md`

4. **Get URL**:
   ```bash
   # Add to .env
   HUGGINGFACE_WORKER_1=https://YOUR_USERNAME-discovery-worker-1.hf.space
   ```

5. **Test**:
   ```bash
   curl https://YOUR_USERNAME-discovery-worker-1.hf.space/health
   ```

### Scaling Strategy
Create multiple spaces:
- `discovery-worker-1` (sentiment analysis)
- `discovery-worker-2` (volume analysis)
- `discovery-worker-3` (pattern detection)

**Each space = 2 cores, so 5 spaces = 10 cores free!**

### Pros
- Easy setup
- Multiple instances
- Good for microservices
- Persistent uptime

### Cons
- Sleeps after 48h inactivity
- 2 cores per space limit
- No GPU on free tier

---

## 3. Google Colab (★★★★☆)

**Best for:** GPU-accelerated batch jobs, ML inference

### Resources (Free)
- **NVIDIA T4 GPU** (16GB VRAM)
- **2 CPU cores**
- **13 GB RAM**
- **78 GB disk**

### Setup

1. **Upload notebook**: `cloud/colab/discovery_worker.ipynb` to Google Drive

2. **Open in Colab**: Right-click > Open with > Google Colaboratory

3. **Enable GPU**:
   - Runtime > Change runtime type
   - Hardware accelerator: GPU

4. **Get ngrok token**: https://dashboard.ngrok.com/signup

5. **Run all cells** and copy the public URL

6. **Add to .env**:
   ```bash
   COLAB_GPU_WORKER=https://xxxx.ngrok.io
   ```

### Limitations
- 12 hour max runtime
- ~90 min idle disconnect
- Need to restart daily
- Not for 24/7 services

### When to Use
- Heavy ML model inference
- Large matrix operations
- Batch processing datasets
- GPU-specific workloads

### Upgrade Options
- **Colab Pro** ($10/mo): 24h runtime, better GPUs
- **Colab Pro+** ($50/mo): Priority access, longer runtimes

### Pros
- Free GPU!
- T4 is quite powerful
- Great for ML tasks
- No account limits

### Cons
- Time limits
- Not persistent
- Manual restarts needed
- Browser must stay open

---

## 4. Kaggle Kernels (★★★☆☆)

**Best for:** Alternative GPU compute, dataset processing

### Resources (Free)
- **NVIDIA P100 or T4 GPU**
- **4 CPU cores**
- **13 GB RAM**
- **73 GB disk**
- **30 hours/week GPU quota**

### Setup

1. **Sign up**: https://kaggle.com/account/login

2. **Create Notebook**:
   - New Notebook
   - Settings > Accelerator: GPU

3. **Enable Internet**:
   - Settings > Internet: On

4. **Install & Run**:
   ```python
   !pip install fastapi uvicorn
   # Similar setup to Colab
   ```

### Pros
- P100 GPU (better than Colab's T4 in some cases)
- Weekly quota system
- Good dataset integration
- Public kernels for sharing

### Cons
- Weekly quota limits
- Less flexible than Colab
- 9 hours max per session
- Internet access restrictions

---

## 5. Railway (★★★☆☆)

**Best for:** Lightweight API endpoints, Redis/DB

### Resources (Free)
- **$5/month credit**
- **0.5 vCPU**
- **512 MB RAM**
- **1 GB storage**

### Setup

1. **Sign up**: https://railway.app

2. **New Project** > Deploy from GitHub

3. **Environment variables** from `.env`

4. **Get URL** from deployment

### Best For
- Redis instances
- Small API services
- Webhook handlers
- Queue workers

### Cons
- Limited resources
- Credit-based (runs out after $5)

---

## 6. Render (★★★☆☆)

**Best for:** Web services, APIs

### Resources (Free)
- **Shared CPU**
- **512 MB RAM**
- **Spins down after 15 min idle**

### Setup

1. **Sign up**: https://render.com

2. **New Web Service** > Connect GitHub

3. **Configure**:
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

4. **Get URL**: `https://your-service.onrender.com`

### Pros
- Easy deployment
- Auto-deploys from Git
- Free SSL
- Good for APIs

### Cons
- Sleeps after inactivity
- Limited RAM
- Slow cold starts

---

## 7. Fly.io (★★★☆☆)

**Best for:** Global edge deployment

### Resources (Free)
- **3 shared CPUs** (total across all apps)
- **256 MB RAM** per VM
- **3 GB storage**
- **160 GB/month bandwidth**

### Setup

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Deploy
flyctl launch
flyctl deploy
```

### Pros
- Multiple regions
- Good for global distribution
- Docker-based

### Cons
- Limited RAM per instance
- Complex pricing
- Not great for heavy compute

---

## 8. Replit (★★☆☆☆)

**Best for:** Quick prototypes, small scripts

### Resources (Free)
- **0.5 vCPU**
- **512 MB RAM**
- **1 GB storage**

### Setup

1. **Sign up**: https://replit.com

2. **Create Repl** > Python

3. **Upload code** or import from GitHub

4. **Run** to get public URL

### Pros
- Very easy to use
- In-browser IDE
- Instant deployment

### Cons
- Very limited resources
- Unreliable for production
- Sleeps aggressively

---

## Recommended Setup Strategy

### Phase 1: Foundation (Free)
```
┌─────────────────────────────────────────┐
│ Oracle Cloud (Primary)                  │
│ • 2 A1 instances (2 cores, 12GB each)  │
│ • Main worker pool                      │
└─────────────────────────────────────────┘
            │
            ├── HuggingFace Space 1 (sentiment)
            ├── HuggingFace Space 2 (volume)
            └── HuggingFace Space 3 (patterns)
```

### Phase 2: GPU Addition
```
┌─────────────────────────────────────────┐
│ Google Colab (GPU tasks)                │
│ • Run during business hours             │
│ • Batch ML jobs                         │
└─────────────────────────────────────────┘
```

### Phase 3: Full Scale (Still Free!)
```
Oracle Cloud (4 ARM instances)     → 4 cores, 24GB
HuggingFace (5 spaces)            → 10 cores, 80GB
Google Colab (daily sessions)      → T4 GPU, 13GB
Kaggle (weekly quota)              → P100 GPU, 13GB
Railway (Redis/Queue)              → 512MB
─────────────────────────────────────────────────
TOTAL: 14+ cores, 100+ GB RAM, 2 GPUs, $0/month
```

## Current Status

✅ **Active:**
- Oracle Cloud: 2 workers deployed
- Worker IPs: `163.192.110.147:8000`, `163.192.103.233:8000`

📝 **Ready to Deploy:**
- HuggingFace: App created in `cloud/huggingface/`
- Colab: Notebook created in `cloud/colab/`

🎯 **Next Steps:**
1. Deploy HuggingFace Space (10 min)
2. Upload Colab notebook (5 min)
3. Try Oracle A1 instance again (capacity permitting)
4. Optional: Set up Railway for Redis

## Integration Code

```python
import os
import requests
from typing import List, Dict

class FreeComputeOrchestrator:
    def __init__(self):
        self.workers = {
            'oracle': [
                '163.192.110.147:8000',
                '163.192.103.233:8000'
            ],
            'huggingface': os.getenv('HUGGINGFACE_WORKERS', '').split(','),
            'colab': os.getenv('COLAB_GPU_WORKER'),
            'kaggle': os.getenv('KAGGLE_WORKER')
        }

    def get_available_workers(self, require_gpu=False):
        """Get list of healthy workers"""
        available = []

        for platform, workers in self.workers.items():
            if require_gpu and platform not in ['colab', 'kaggle']:
                continue

            for worker in workers:
                if worker and self.check_health(worker):
                    available.append({
                        'url': worker,
                        'platform': platform,
                        'gpu': platform in ['colab', 'kaggle']
                    })

        return available

    def check_health(self, worker_url):
        """Check if worker is healthy"""
        try:
            response = requests.get(f"http://{worker_url}/health", timeout=3)
            return response.ok
        except:
            return False

    def distribute_work(self, tasks, prefer_gpu=False):
        """Distribute tasks across available workers"""
        workers = self.get_available_workers(require_gpu=prefer_gpu)

        if not workers:
            raise Exception("No workers available")

        # Round-robin distribution
        results = []
        for i, task in enumerate(tasks):
            worker = workers[i % len(workers)]
            result = self.execute_task(worker['url'], task)
            results.append(result)

        return results
```

## Monitoring

```bash
# Check Oracle workers
./cloud/oracle_status.sh

# Test all workers
python3 -c "
import requests
workers = [
    'http://163.192.110.147:8000',
    'http://163.192.103.233:8000'
]
for w in workers:
    try:
        r = requests.get(f'{w}/health', timeout=3)
        print(f'✅ {w}: {r.json()}')
    except:
        print(f'❌ {w}: Offline')
"
```

## Cost Breakdown

| Platform | Monthly Cost | Annual Cost |
|----------|-------------|-------------|
| Oracle Cloud | $0 | $0 |
| HuggingFace (5 spaces) | $0 | $0 |
| Google Colab | $0 | $0 |
| Kaggle | $0 | $0 |
| Railway | $0 | $0 |
| Render | $0 | $0 |
| **TOTAL** | **$0** | **$0** |

## Upgrade Paths (If Needed Later)

When free tier isn't enough:

1. **Oracle Cloud**: Stays free forever
2. **HuggingFace Pro**: $9/mo per space for persistent GPU
3. **Google Colab Pro**: $10/mo for 24h runtimes
4. **Railway Pro**: $5/mo for more resources
5. **Digital Ocean**: $4/mo for basic droplet

But with proper utilization of free tiers, you can run substantial workloads at $0/month!

## Tips for Maximizing Free Resources

1. **Use right tool for job**: GPU tasks on Colab, CPU on Oracle
2. **Batch processing**: Queue work for Colab's 12-hour windows
3. **Fallback chains**: If Colab offline, use Oracle workers
4. **Health checks**: Monitor all workers, route around failures
5. **Caching**: Cache results to reduce recomputation
6. **Compression**: Minimize data transfer between workers
7. **Off-peak usage**: Oracle instances easier to provision at night
8. **Multiple accounts**: HuggingFace/Colab allow multiple free accounts

## Conclusion

With strategic use of free tiers, you can build a powerful distributed computing platform at $0/month:

- **14+ CPU cores** for parallel processing
- **100+ GB RAM** for large datasets
- **2 GPUs** for ML workloads
- **~400 GB storage** across platforms
- **24/7 uptime** on Oracle/HuggingFace
- **Geographic distribution** via multiple providers

This setup can handle significant workloads before needing any paid services!
