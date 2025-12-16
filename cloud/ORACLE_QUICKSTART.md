# Oracle Cloud ARM Compute - Quick Start Guide

## 🚀 Setup in 3 Steps

### Step 1: Run Automated Setup
```bash
cd /mnt/e/projects/discovery/cloud/setup
./setup_oracle_cloud.sh
```

This interactive script will:
- Generate Oracle Cloud API keys
- Help provision 4 ARM VMs (Always Free)
- Deploy worker services
- Run verification tests

### Step 2: Manual Steps in Oracle Console

If the automated provisioning doesn't work (common with new accounts), follow these manual steps:

1. **Sign up for Oracle Cloud Free Tier**
   - Go to: https://oracle.com/cloud/free
   - Choose region: `us-chicago-1`
   - Complete payment verification (won't be charged)

2. **Add API Key** (if not done automatically)
   - Oracle Console → Profile → User Settings → API Keys
   - Add the public key from `~/.oci/oci_api_key_public.pem`
   - Copy the fingerprint to `.env` file

3. **Create VMs Manually** (if automated fails)
   - Navigate to Compute → Instances
   - Create 4 instances with these specs:
     - Shape: VM.Standard.A1.Flex
     - OCPUs: 1, Memory: 6GB
     - Image: Ubuntu 22.04
     - Add your SSH key
   - Copy public IPs to `cloud/deploy/workers.txt`

### Step 3: Deploy and Test

Once VMs are created (automatically or manually):

```bash
# Deploy to workers
cd /mnt/e/projects/discovery/cloud/deploy
./deploy_workers.sh

# Start services
./start_all_workers.sh

# Verify health
./check_workers.sh
```

---

## 📋 Pre-requisites Checklist

- [ ] Python 3.9+ installed
- [ ] SSH key pair (`~/.ssh/id_rsa.pub`)
- [ ] Oracle Cloud account (free tier)
- [ ] 30-45 minutes for initial setup

---

## 🔧 Troubleshooting

### "Out of Capacity" Error
Oracle's free ARM instances are popular. Try:
1. Different availability domain
2. Wait and retry (early morning/late night)
3. Try 2 VMs with 2 OCPUs each instead of 4x1

### SSH Connection Failed
1. Check security list has port 22 open
2. Verify public IP is correct
3. Use correct username: `ubuntu`
4. Check SSH key: `ssh -i ~/.ssh/id_rsa ubuntu@IP`

### Worker API Not Responding
1. Check security list has port 8000 open
2. SSH to VM and check logs: `tail ~/ultrathink/worker.log`
3. Restart worker: `cd ~/ultrathink && ./stop_worker.sh && ./start_worker.sh`

---

## 📊 What You Get

| Feature | Value |
|---------|-------|
| **VMs** | 4 ARM instances |
| **Specs** | 24GB RAM, 8 vCPUs total |
| **Storage** | 200GB |
| **Network** | 10TB/month transfer |
| **Cost** | $0/month (Always Free) |
| **Performance** | 20-50x speedup |

---

## 🎯 Next Steps

After successful setup:

1. **Run full analysis**:
   ```python
   from cloud.orchestrator.job_orchestrator import JobOrchestrator

   orchestrator = JobOrchestrator(
       worker_urls=os.getenv('ORACLE_WORKERS').split(',')
   )

   results = await orchestrator.analyze_all_trades(
       trades,
       analysis_types=['sentiment', 'market_impact', 'volume']
   )
   ```

2. **Monitor performance**:
   ```bash
   cd cloud/deploy
   ./check_workers.sh
   ```

3. **Scale as needed**:
   - Add more workers to `workers.txt`
   - Adjust batch sizes for optimization

---

## 📚 Resources

- [Full Setup Documentation](../ORACLE_CLOUD_SETUP.md)
- [Architecture Overview](../ORACLE_CLOUD_ASSESSMENT.md)
- [Worker API Documentation](worker/README.md)
- [Oracle Cloud Console](https://cloud.oracle.com)

---

**Questions?** Check the detailed guides or run `./setup_oracle_cloud.sh` for interactive help!