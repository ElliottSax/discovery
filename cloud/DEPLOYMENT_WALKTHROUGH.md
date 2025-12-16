# Free Compute Deployment - Interactive Walkthrough

**Goal**: Get 4-16 cores of free compute running in 15-30 minutes

**Status**: Oracle auto-provisioning running in background ✅

---

## Option 1: HuggingFace Spaces (⭐ Start Here - 10 min)

**What you get**: 2 cores, 16GB RAM per space, unlimited spaces

### Step 1: Create HuggingFace Account (2 min)

1. Open browser: **https://huggingface.co/join**
2. Fill out:
   - Email address
   - Username
   - Password
3. Click "Sign Up"
4. Check email and verify

✅ Done? Continue to Step 2

---

### Step 2: Create Your First Space (3 min)

1. Go to: **https://huggingface.co/new-space**

2. Fill in the form:
   ```
   Owner: [your username]
   Space name: discovery-worker-1
   License: MIT
   Select SDK: Gradio
   Space hardware: CPU basic - 2 vCPU • 16 GB • Free
   Repo type: Public (or Private)
   ```

3. Click "Create Space"

4. Wait ~10 seconds for space to initialize

✅ Space created! Continue to Step 3

---

### Step 3: Upload Worker Files (3 min)

You'll see the space repository interface. Click "Files" tab.

**Upload these 3 files** (from `/mnt/e/projects/discovery/cloud/huggingface/`):

1. Click "+ Add file" > "Upload files"

2. Upload:
   - `app.py` (main worker application)
   - `requirements.txt` (dependencies)
   - `README.md` (optional, documentation)

3. Commit message: "Initial worker deployment"

4. Click "Commit to main"

**Space will automatically build and deploy!** (~2 minutes)

✅ Files uploaded! Continue to Step 4

---

### Step 4: Get Your Worker URL (1 min)

1. Wait for build to complete (watch the build logs)

2. When you see "Running on local URL: http://0.0.0.0:7860"
   - Space is live! ✅

3. Your worker URL is:
   ```
   https://[your-username]-discovery-worker-1.hf.space
   ```

4. Test it - click the link or run:
   ```bash
   curl https://[your-username]-discovery-worker-1.hf.space/health
   ```

   Should return:
   ```json
   {
     "status": "healthy",
     "worker_type": "general",
     "compute_platform": "huggingface_spaces"
   }
   ```

✅ Worker is live! Continue to Step 5

---

### Step 5: Add to Your Configuration (1 min)

Add to `/mnt/e/projects/discovery/.env`:

```bash
# HuggingFace Workers
HUGGINGFACE_WORKER_1=https://[your-username]-discovery-worker-1.hf.space
```

Or run:
```bash
echo "HUGGINGFACE_WORKER_1=https://[your-username]-discovery-worker-1.hf.space" >> .env
```

✅ **HuggingFace worker complete!** You now have 2 cores + 16GB RAM

**Want more?** Repeat steps 2-5 to create:
- `discovery-worker-2` (another 2 cores)
- `discovery-worker-3` (another 2 cores)
- etc.

---

## Option 2: Google Colab (GPU! - 15 min)

**What you get**: T4 GPU (16GB VRAM), 2 CPU cores, 13GB RAM

### Step 1: Upload Notebook to Google Drive (2 min)

1. Open **Google Drive**: https://drive.google.com

2. Create folder: "Colab Notebooks" (or use existing)

3. Upload file:
   - Navigate to `/mnt/e/projects/discovery/cloud/colab/`
   - Upload `discovery_worker.ipynb` to your Drive folder

✅ Notebook uploaded! Continue to Step 2

---

### Step 2: Open in Colab (1 min)

1. In Google Drive, find `discovery_worker.ipynb`

2. Right-click > "Open with" > "Google Colaboratory"
   - If you don't see Colaboratory:
     - Click "Connect more apps"
     - Search "Colaboratory"
     - Install it

3. Notebook opens in Colab!

✅ Notebook open! Continue to Step 3

---

### Step 3: Enable GPU (1 min)

1. In Colab menu: **Runtime** > **Change runtime type**

2. Settings:
   ```
   Hardware accelerator: GPU
   GPU type: T4
   ```

3. Click **Save**

4. You'll see "🔌 T4" in the top-right corner

✅ GPU enabled! Continue to Step 4

---

### Step 4: Get ngrok Token (3 min)

Ngrok provides a public URL for your Colab worker.

1. Go to: **https://dashboard.ngrok.com/signup**

2. Sign up (free):
   - Email
   - Password
   - OR: Sign in with Google/GitHub

3. Verify email

4. Go to: **https://dashboard.ngrok.com/get-started/your-authtoken**

5. **Copy your authtoken** (looks like: `2abc123def456...`)
   - Keep this handy for next step!

✅ Token copied! Continue to Step 5

---

### Step 5: Run the Notebook (5 min)

1. In Colab, click **Runtime** > **Run all**
   - Or press `Ctrl+F9`

2. Cells will run in sequence:
   - Installing dependencies (~2 min)
   - Checking GPU
   - Setting up ngrok
   - Starting worker

3. When prompted: **"Enter your ngrok auth token:"**
   - Paste your token from Step 4
   - Press Enter

4. Wait ~1 minute for worker to start

5. You'll see output like:
   ```
   ═══════════════════════════════════════════
   🚀 WORKER IS LIVE!
   ═══════════════════════════════════════════

   📍 Public URL: https://xxxx-xx-xx-xx-xx.ngrok.io

   💡 Add this to your .env file:
      COLAB_GPU_WORKER=https://xxxx-xx-xx-xx-xx.ngrok.io
   ```

6. **Copy that URL!**

✅ Worker running! Continue to Step 6

---

### Step 6: Add to Configuration (1 min)

Add to `/mnt/e/projects/discovery/.env`:

```bash
# GPU Worker (Colab)
COLAB_GPU_WORKER=https://xxxx-xx-xx-xx-xx.ngrok.io
```

Test it:
```bash
curl https://xxxx-xx-xx-xx-xx.ngrok.io/health
```

Should return:
```json
{
  "status": "healthy",
  "worker_type": "gpu",
  "gpu_available": true,
  "compute_platform": "colab"
}
```

✅ **Colab GPU worker complete!** You now have T4 GPU + 2 cores + 13GB RAM

**Important**:
- Keep the browser tab open
- Worker runs for 12 hours max
- Restart daily by running cells again

---

## Option 3: Kaggle Kernels (Alternative GPU - 15 min)

**What you get**: P100 GPU, 4 CPU cores, 13GB RAM, 30h/week GPU quota

Similar to Colab but with weekly quota instead of daily sessions.

### Quick Steps:

1. **Sign up**: https://kaggle.com/account/login

2. **Create Notebook**:
   - Click "Code" > "New Notebook"
   - Settings > Accelerator: **GPU P100**
   - Settings > Internet: **On**

3. **Install & Run**:
   ```python
   !pip install fastapi uvicorn pyngrok nest-asyncio

   # Copy code from Colab notebook
   # Or upload discovery_worker.ipynb
   ```

4. **Get ngrok token** (same as Colab step 4)

5. **Run and get URL**

6. **Add to .env**:
   ```bash
   KAGGLE_GPU_WORKER=https://xxxx.ngrok.io
   ```

---

## Verify All Workers

After deploying, check all workers:

```bash
cd /mnt/e/projects/discovery
python3 cloud/monitor/check_all_workers.py
```

Should show:
```
╔════════════════════════════════════════════════════════════════════╗
║                     Worker Status Report                          ║
╚════════════════════════════════════════════════════════════════════╝

HUGGINGFACE_SPACES
──────────────────────────────────────────────────────────────────────
✅ https://yourname-discovery-worker-1.hf.space
   Type: general | Response: 0.234s

COLAB
──────────────────────────────────────────────────────────────────────
✅ https://xxxx.ngrok.io
   Type: gpu 🎮 GPU | Response: 0.156s

Summary
Total Workers: 2
Healthy: 2
Availability: 100%

Available Resources
CPU Cores: ~4
RAM: ~29 GB
GPUs: 1
```

---

## What You've Achieved

**Active Compute** (right now):
- HuggingFace: 2-6 cores, 16-48GB RAM (depending on # of spaces)
- Colab: T4 GPU, 2 cores, 13GB RAM
- **Total: 4-8 cores, 29-61GB RAM, 1 GPU, $0/month**

**Background** (auto-provisioning):
- Oracle: Will add 4 cores, 24GB RAM when capacity available (1-7 days)

**Final Total** (when Oracle completes):
- **8-12 cores, 53-85GB RAM, 1 GPU, $0/month**

---

## Quick Reference Card

| Platform | Status | Setup Time | Resources |
|----------|--------|------------|-----------|
| Oracle | 🔄 Auto-provisioning | 1-7 days | 4 cores, 24GB |
| HuggingFace | ✅ Deploy now | 10 min | 2 cores, 16GB |
| Colab | ✅ Deploy now | 15 min | 2 cores, 13GB, T4 GPU |
| Kaggle | 📝 Optional | 15 min | 4 cores, 13GB, P100 GPU |

---

## Troubleshooting

### HuggingFace space build fails
- Check `requirements.txt` is valid
- View build logs in Space settings
- Common issue: FastAPI version conflict
  - Solution: Use exact versions in requirements.txt

### Colab disconnects immediately
- Don't close browser tab
- Check internet connection
- Try incognito mode
- Restart runtime and try again

### ngrok URL not working
- Check token is correct
- Token has usage limits on free tier (20 connections/min)
- Create new token if needed

### Worker health check fails
- Wait 30 seconds for space to wake up (if sleeping)
- Check URL is correct (no trailing slash)
- Verify space is running (check HuggingFace UI)

---

## Next Steps

Once you have workers running:

1. **Test workers**:
   ```bash
   python3 cloud/monitor/check_all_workers.py
   ```

2. **Run test analysis**:
   ```python
   import requests

   worker = "https://your-worker.hf.space"

   response = requests.post(f"{worker}/analyze", json={
       "trades": [
           {"price": 100, "volume": 1000, "price_change": 2.5},
           {"price": 102.5, "volume": 1500, "price_change": 1.2}
       ],
       "analysis_types": ["sentiment", "volume_analysis"]
   })

   print(response.json())
   ```

3. **Integrate with main app**:
   - Workers are now available via environment variables
   - Use orchestrator to distribute work
   - See `cloud/FREE_COMPUTE_GUIDE.md` for integration examples

---

## Summary

**Time investment**: 15-30 minutes today
**Result**: 4-8 cores + GPU running immediately
**Cost**: $0/month
**Value if paid**: ~$50-100/month

Plus Oracle will add 4 more cores automatically in background (1-7 days).

**Start with HuggingFace** - it's the easiest and most reliable for 24/7 compute!
