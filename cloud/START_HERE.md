# 🚀 Free Compute - START HERE

**Get 4-20 cores + GPU for $0/month**

---

## ⚡ Quick Start (Pick One)

### Option 1: HuggingFace (Easiest) - 10 minutes

**Manual Way** (no script needed):

1. Go to: **https://huggingface.co/new-space**
2. Fill in:
   - Name: `discovery-worker-1`
   - SDK: `Gradio`
   - Hardware: `CPU basic` (free)
3. Click "Create Space"
4. Upload these files from `cloud/huggingface/`:
   - `app.py`
   - `requirements.txt`
5. Wait 2 min for build
6. Your worker: `https://YOUR-USERNAME-discovery-worker-1.hf.space`

**Result**: ✅ 2 cores + 16GB RAM

---

### Option 2: Google Colab (GPU!) - 15 minutes

1. Upload `cloud/colab/discovery_worker.ipynb` to Google Drive
2. Open with Google Colaboratory
3. Runtime > Change runtime type > **GPU**
4. Get ngrok token: https://dashboard.ngrok.com/signup (free)
5. Runtime > Run all
6. Paste ngrok token when asked
7. Copy the public URL

**Result**: ✅ T4 GPU + 2 cores + 13GB RAM

---

### Option 3: Oracle Cloud (Best) - Automatic

**Already running!** ✅

- Auto-provisioning active (Attempt #19)
- Will get 4 cores + 24GB RAM when capacity available
- Runs 24/7, no action needed
- Check: `tail -f ~/.oracle_auto_provision/provision.log`

**ETA**: 1-7 days (capacity very tight)

---

## 📂 Everything You Need

### Files Ready to Deploy

```
cloud/
├── huggingface/
│   ├── app.py              ← Upload to HF Space
│   ├── requirements.txt    ← Upload to HF Space
│   └── README.md
│
├── colab/
│   └── discovery_worker.ipynb  ← Upload to Google Drive
│
└── setup/
    ├── deploy_huggingface.py   ← Automated deployment (needs token)
    ├── deploy_workers.py        ← Interactive menu
    └── auto_provision.sh        ← Oracle (running)
```

### Documentation

- **FREE_COMPUTE_GUIDE.md** - Complete guide (8+ platforms)
- **DEPLOYMENT_WALKTHROUGH.md** - Step-by-step
- **AUTO_DEPLOY_README.md** - Automated scripts
- **QUICK_REFERENCE.md** - Cheat sheet

---

## 🎯 What I Recommend

**Do This Right Now** (choose one):

1. **HuggingFace Manual** - Easiest, most reliable
   - 10 min setup
   - 24/7 uptime
   - Can create unlimited workers
   - Just upload files via web UI

2. **Google Colab** - If you need GPU
   - 15 min setup
   - Free T4 GPU!
   - Great for ML tasks
   - 12h sessions

**Oracle will provision automatically in background**

---

## 📊 What You'll Have

| Platform | CPU | RAM | GPU | Status |
|----------|-----|-----|-----|--------|
| HuggingFace | 2-10 | 16-80GB | - | ⏳ Ready to deploy |
| Colab | 2 | 13GB | T4 | ⏳ Ready to deploy |
| Oracle | 4 | 24GB | - | 🔄 Auto-provisioning |
| **TOTAL** | **8-16** | **53-117GB** | **1** | **$0/month** |

---

## 🚀 Deployment Commands

### HuggingFace (Automated)
```bash
cd cloud/setup
python3 deploy_huggingface.py
# Needs Write token from: https://huggingface.co/settings/tokens
```

### Check All Workers
```bash
python3 cloud/monitor/check_all_workers.py
```

### Oracle Status
```bash
tail -f ~/.oracle_auto_provision/provision.log
```

---

## ✅ After Deployment

Once you have workers running:

```python
import requests
import os

# Test worker
worker = os.getenv('HUGGINGFACE_WORKER_1')  # or COLAB_GPU_WORKER
response = requests.get(f"{worker}/health")
print(response.json())

# Run analysis
data = {
    "trades": [{"price": 100, "volume": 1000, "price_change": 2.5}],
    "analysis_types": ["sentiment", "volume_analysis"]
}
result = requests.post(f"{worker}/analyze", json=data)
print(result.json())
```

---

## 🆘 Need Help?

**Token Issues?**
- Must be "Write" token (not "Read")
- Get new one: https://huggingface.co/settings/tokens

**HuggingFace Manual Deployment**
1. https://huggingface.co/new-space
2. Upload app.py + requirements.txt
3. Done!

**Google Colab**
1. Upload notebook to Drive
2. Open in Colab
3. Enable GPU
4. Run cells

**Oracle**
- Just wait, it's automatic
- Check: `tail -f ~/.oracle_auto_provision/provision.log`

---

## 📚 Full Documentation

- **Complete Platform Guide**: `cloud/FREE_COMPUTE_GUIDE.md`
- **Step-by-Step Walkthrough**: `cloud/DEPLOYMENT_WALKTHROUGH.md`
- **Automated Scripts**: `cloud/AUTO_DEPLOY_README.md`
- **Quick Reference**: `cloud/QUICK_REFERENCE.md`

---

## 💡 Summary

**Fastest Path to Free Compute:**

1. **Manual HuggingFace** (10 min) → 2 cores + 16GB
2. **Google Colab** (15 min) → T4 GPU + 2 cores
3. **Oracle** (auto) → 4 cores + 24GB (1-7 days)

**Total: 8-16 cores, 53-117GB RAM, 1 GPU, $0/month**

**Start with HuggingFace manual deployment - it's the easiest!**

---

Ready? Pick a platform above and let's get your free compute running! 🎉
