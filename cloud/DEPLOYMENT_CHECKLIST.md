# Free Compute Deployment Checklist

Quick reference for deploying all free compute resources

## ✅ Completed

- [x] Oracle Cloud CLI configured
- [x] 2 Oracle workers deployed (163.192.110.147, 163.192.103.233)
- [x] HuggingFace Space app created (`cloud/huggingface/`)
- [x] Google Colab notebook created (`cloud/colab/`)
- [x] Workers configuration file updated

## 📋 To Deploy

### HuggingFace Spaces (10 min)

- [ ] Create HuggingFace account at https://huggingface.co/join
- [ ] Create new Space: https://huggingface.co/new-space
  - Name: `discovery-worker-1`
  - SDK: Gradio
  - Hardware: CPU basic (free)
- [ ] Upload files from `cloud/huggingface/`:
  - [ ] `app.py`
  - [ ] `requirements.txt`
  - [ ] `README.md`
- [ ] Wait for deployment (~2 min)
- [ ] Test: `curl https://YOUR_USERNAME-discovery-worker-1.hf.space/health`
- [ ] Add to `.env`: `HUGGINGFACE_WORKER_1=https://YOUR_USERNAME-discovery-worker-1.hf.space`

**Optional: Create 2-4 more spaces for scaling**

### Google Colab (5 min)

- [ ] Sign in to Google account
- [ ] Upload `cloud/colab/discovery_worker.ipynb` to Google Drive
- [ ] Open with Google Colaboratory
- [ ] Runtime > Change runtime type > GPU
- [ ] Sign up for ngrok: https://dashboard.ngrok.com/signup
- [ ] Copy ngrok auth token
- [ ] Run all cells in notebook
- [ ] Paste ngrok token when prompted
- [ ] Copy the public URL
- [ ] Add to `.env`: `COLAB_GPU_WORKER=https://xxxx.ngrok.io`

**Note: Needs to be restarted daily (12h limit)**

### Oracle Cloud (Ongoing)

- [ ] Keep trying to provision A1.Flex instances
- [ ] Best times: Early morning/late night Chicago time
- [ ] Run: `./cloud/setup/retry_create_instance.sh`
- [ ] Target: 4 total A1 instances (24GB RAM, 4 cores)

### Optional: Additional Platforms

#### Kaggle Kernels
- [ ] Sign up: https://kaggle.com
- [ ] Create new notebook
- [ ] Settings > Accelerator: GPU
- [ ] Settings > Internet: On
- [ ] Upload similar code to Colab notebook
- [ ] Run and get URL

#### Railway (for Redis/Queue)
- [ ] Sign up: https://railway.app
- [ ] New Project > Deploy Redis
- [ ] Copy connection string
- [ ] Add to `.env`: `REDIS_URL=...`

#### Render (for API endpoint)
- [ ] Sign up: https://render.com
- [ ] New Web Service > Connect GitHub
- [ ] Select repository
- [ ] Configure build/start commands
- [ ] Get URL

## 🧪 Testing

### Test Oracle Workers
```bash
./cloud/oracle_status.sh

curl http://163.192.110.147:8000/health
curl http://163.192.103.233:8000/health
```

### Test HuggingFace Worker
```bash
curl https://YOUR_USERNAME-discovery-worker-1.hf.space/health

# Full test
curl -X POST https://YOUR_USERNAME-discovery-worker-1.hf.space/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "trades": [{"price": 100, "volume": 1000, "price_change": 2.5}],
    "analysis_types": ["sentiment", "volume_analysis"]
  }'
```

### Test Colab Worker
```bash
curl https://xxxx.ngrok.io/health

# Check GPU
curl https://xxxx.ngrok.io/ | grep gpu
```

## 📊 Resource Inventory

After deployment, you should have:

| Platform | Workers | Cores | RAM | GPU | Status |
|----------|---------|-------|-----|-----|--------|
| Oracle | 2 | 2+ | 12+ GB | No | ✅ Active |
| HuggingFace | 1-5 | 2-10 | 16-80 GB | No | ⏳ Deploy |
| Colab | 1 | 2 | 13 GB | T4 | ⏳ Deploy |
| Kaggle | 0-1 | 4 | 13 GB | P100 | 📝 Optional |
| **TOTAL** | **4-9** | **8-18** | **41-118 GB** | **1-2** | |

## 🔧 Configuration

### Environment Variables

Add to `/mnt/e/projects/discovery/.env`:

```bash
# Oracle Cloud Workers
ORACLE_WORKER_1=http://163.192.110.147:8000
ORACLE_WORKER_2=http://163.192.103.233:8000
ORACLE_WORKERS=163.192.110.147:8000,163.192.103.233:8000

# HuggingFace Spaces
HUGGINGFACE_WORKER_1=https://YOUR_USERNAME-discovery-worker-1.hf.space
HUGGINGFACE_WORKER_2=https://YOUR_USERNAME-discovery-worker-2.hf.space
# Add more as needed

# GPU Workers
COLAB_GPU_WORKER=https://xxxx.ngrok.io
KAGGLE_GPU_WORKER=https://xxxx.ngrok.io  # if using

# Optional
REDIS_URL=redis://...  # if using Railway
```

### Worker List File

`cloud/deploy/workers.txt`:
```
# Oracle Cloud Workers
163.192.110.147:8000
163.192.103.233:8000

# HuggingFace Workers
YOUR_USERNAME-discovery-worker-1.hf.space:443

# GPU Workers (dynamic)
# Add Colab/Kaggle URLs as they come online
```

## 🚀 Usage

### Check All Workers
```bash
python3 cloud/monitor/check_all_workers.py
```

### Distribute Work
```python
from cloud.orchestrator import FreeComputeOrchestrator

orchestrator = FreeComputeOrchestrator()
workers = orchestrator.get_available_workers()
print(f"Available: {len(workers)} workers")

# GPU tasks
gpu_workers = orchestrator.get_available_workers(require_gpu=True)
print(f"GPU workers: {len(gpu_workers)}")
```

## 📈 Monitoring

### Health Dashboard
```bash
# Start monitoring dashboard
python3 cloud/monitor/worker_dashboard.py
```

### Automated Checks
```bash
# Add to cron for monitoring
*/5 * * * * cd /mnt/e/projects/discovery && python3 cloud/monitor/check_all_workers.py
```

## 💡 Tips

1. **Deploy incrementally**: Start with Oracle + 1 HuggingFace space, then add more
2. **Test thoroughly**: Verify each worker before adding to production
3. **Monitor usage**: Track which workers are used most
4. **Fallback logic**: Always have backup workers configured
5. **Document URLs**: Keep `.env` file updated with all worker URLs
6. **Restart Colab daily**: Set reminder to restart GPU worker
7. **Oracle capacity**: Keep retrying A1 instance creation during off-peak hours

## 🎯 Success Criteria

You'll know deployment is successful when:

- [ ] At least 2 Oracle workers responding to `/health`
- [ ] At least 1 HuggingFace space deployed and accessible
- [ ] Colab notebook runs and provides public URL
- [ ] All workers can process test analysis requests
- [ ] Environment variables configured in `.env`
- [ ] Total compute: 4+ cores, 25+ GB RAM available

## 📞 Troubleshooting

### Oracle worker not responding
```bash
# SSH into instance
ssh ubuntu@163.192.110.147

# Check logs
tail -f ~/ultrathink/worker.log

# Restart service
cd ~/ultrathink && ./stop_worker.sh && ./start_worker.sh
```

### HuggingFace space error
- Check Space logs in HuggingFace UI
- Verify `requirements.txt` has all dependencies
- Rebuild space if needed
- Check if space is sleeping (make request to wake)

### Colab disconnected
- Restart runtime
- Re-run all cells
- Keep browser tab open
- Check ngrok token is valid

### No workers available
```bash
# Check network connectivity
ping 163.192.110.147

# Verify environment variables
cat .env | grep WORKER

# Check firewall rules (Oracle)
# Ensure ports 8000, 443 are open
```

## 🎉 Next Steps After Deployment

1. **Baseline performance test**: Run analysis on all workers, measure speed
2. **Load balancing**: Implement round-robin or least-busy routing
3. **Auto-scaling**: Detect load and spin up Colab/Kaggle as needed
4. **Monitoring dashboard**: Real-time view of all worker status
5. **Cost tracking**: Track free tier usage limits
6. **Optimization**: Profile which workers handle which tasks best

---

**Estimated Total Setup Time: 30-60 minutes**

**Monthly Cost: $0**

**Total Compute Available: 8-18 cores, 41-118 GB RAM, 1-2 GPUs**
