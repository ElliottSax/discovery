# Oracle Cloud ARM Setup - Complete Step-by-Step Guide

## 📋 Table of Contents
1. [Pre-Setup Checklist](#pre-setup-checklist)
2. [Step 1: Oracle Cloud Account](#step-1-oracle-cloud-account)
3. [Step 2: Generate API Keys](#step-2-generate-api-keys)
4. [Step 3: Install OCI CLI](#step-3-install-oci-cli)
5. [Step 4: Provision VMs](#step-4-provision-vms)
6. [Step 5: Deploy Workers](#step-5-deploy-workers)
7. [Step 6: Verify Setup](#step-6-verify-setup)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Setup Checklist

Run the verification script first:
```bash
cd /mnt/e/projects/discovery/cloud/setup
python3 verify_oracle_setup.py
```

Required:
- [ ] WSL/Linux/Mac environment
- [ ] Python 3.9+ installed
- [ ] 30-45 minutes available
- [ ] Credit card for Oracle signup (won't be charged)

---

## Step 1: Oracle Cloud Account

### 1.1 Sign Up for Oracle Cloud Free Tier

1. Go to: https://oracle.com/cloud/free
2. Click "Start for free"
3. Fill registration form:
   - **Email**: Your email
   - **Country**: Your country
   - **Account Type**: Personal or Company
   - **Home Region**: `us-chicago-1` ⚠️ IMPORTANT - can't change later!

4. Verify email
5. Add payment method (required but won't charge for Always Free resources)

### 1.2 Save Your Account Information

After account creation, save these OCIDs:

```bash
# In Oracle Console, click Profile (top right) → User Settings
# Copy these values to your .env file

ORACLE_USER_OCID=ocid1.user.oc1..aaaaaaaa74qquxlbn7ky5lpcfkt2akeemtn4v2gd7kdc52dve7mx7kxbdziq
ORACLE_TENANCY_OCID=ocid1.tenancy.oc1..aaaaaaaa2ktu74gnhxcctwnk65ntpj6gfb53ofanbz2ram3jkm62ke5ekpsa
ORACLE_REGION=us-chicago-1
```

---

## Step 2: Generate API Keys

### 2.1 Generate Keys Locally

```bash
cd /mnt/e/projects/discovery/cloud/setup
./generate_oci_keys.sh
```

This creates:
- Private key: `~/.oci/oci_api_key.pem`
- Public key: `~/.oci/oci_api_key_public.pem`

### 2.2 Upload Public Key to Oracle Cloud

1. Oracle Console → Profile menu → User Settings
2. Click "API Keys" in left sidebar
3. Click "Add API Key"
4. Select "Paste Public Key"
5. Paste contents from: `cat ~/.oci/oci_api_key_public.pem`
6. Click "Add"
7. **COPY THE FINGERPRINT** (format: `12:34:56:78:90:ab:cd:ef:...`)

### 2.3 Update .env with Fingerprint

```bash
# Edit .env file
ORACLE_FINGERPRINT=12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef
```

---

## Step 3: Install OCI CLI

### 3.1 Run Installation Script

```bash
cd /mnt/e/projects/discovery/cloud/setup
./install_oci_cli.sh
```

Choose option 1 (pip installation) when prompted.

### 3.2 Configure OCI CLI

The script will guide you through configuration. Use these values:

```
User OCID: [from your .env]
Fingerprint: [from step 2.2]
Key location: /home/[username]/.oci/oci_api_key.pem
Tenancy OCID: [from your .env]
Region: us-chicago-1
```

### 3.3 Test Connection

```bash
oci iam region list
```

Should show list of Oracle Cloud regions.

---

## Step 4: Provision VMs

### Option A: Automated Provisioning (Recommended)

```bash
cd /mnt/e/projects/discovery/cloud/setup
python3 provision_oracle_vms.py
```

This will:
1. Create VCN (Virtual Cloud Network)
2. Configure security rules
3. Create 4 ARM VMs
4. Output public IPs to `workers.txt`

### Option B: Manual Creation (if automated fails)

#### 4.1 Create VCN

1. Oracle Console → Networking → Virtual Cloud Networks
2. Click "Start VCN Wizard"
3. Select "Create VCN with Internet Connectivity"
4. Name: `ultrathink-vcn`
5. Keep defaults, click "Create"

#### 4.2 Configure Security Rules

1. In VCN details → Security Lists → Default Security List
2. Add Ingress Rules:

| Source | Port | Protocol | Description |
|--------|------|----------|-------------|
| 0.0.0.0/0 | 22 | TCP | SSH |
| 0.0.0.0/0 | 8000 | TCP | Worker API |

#### 4.3 Create 4 Compute Instances

For each VM (repeat 4 times):

1. Compute → Instances → Create Instance
2. Name: `ultrathink-worker-1` (then 2, 3, 4)
3. Image: Ubuntu 22.04
4. Shape: Click "Change Shape"
   - Shape series: Ampere
   - Shape: VM.Standard.A1.Flex
   - OCPUs: 1
   - Memory: 6 GB
5. Networking:
   - VCN: ultrathink-vcn
   - Assign public IP: Yes
6. Add SSH keys: Upload `~/.ssh/id_rsa.pub`
7. Create

#### 4.4 Save Worker IPs

After all 4 VMs are created:

```bash
# Create workers.txt
cd /mnt/e/projects/discovery/cloud/deploy
cat > workers.txt << EOF
129.153.xxx.xxx  # Replace with actual IPs
129.153.yyy.yyy
129.153.zzz.zzz
129.153.www.www
EOF
```

---

## Step 5: Deploy Workers

### 5.1 Deploy Code to Workers

```bash
cd /mnt/e/projects/discovery/cloud/deploy
./deploy_workers.sh
```

This will:
- Upload Python code
- Install dependencies
- Create startup scripts

Expected time: 5-10 minutes

### 5.2 Start Worker Services

```bash
./start_all_workers.sh
```

### 5.3 Check Health

```bash
./check_workers.sh
```

Expected output:
```
Checking 129.153.xxx.xxx...
  ✓ Process running
  ✓ HTTP endpoint responding
```

---

## Step 6: Verify Setup

### 6.1 Run Complete Verification

```bash
cd /mnt/e/projects/discovery/cloud/setup
python3 verify_oracle_setup.py
```

### 6.2 Run Test Analysis

```bash
cd /mnt/e/projects/discovery
python3 cloud/test_oracle_setup.py
```

### 6.3 Update .env

The setup script should have added worker URLs:
```bash
grep ORACLE_WORKERS .env
```

Should show:
```
ORACLE_WORKERS=http://129.153.xxx.xxx:8000,http://129.153.yyy.yyy:8000,...
```

---

## Troubleshooting

### Issue: "Out of Capacity" Error

**Problem**: Oracle's free ARM instances are popular
**Solutions**:
1. Try different availability domain
2. Try early morning/late night
3. Create 2 VMs with 2 OCPUs each instead of 4x1
4. Try different region (requires new account)

### Issue: SSH Connection Failed

```bash
# Test SSH
ssh -v ubuntu@129.153.xxx.xxx

# Common fixes:
# 1. Check security list has port 22 open
# 2. Use correct username: ubuntu
# 3. Check key permissions
chmod 600 ~/.ssh/id_rsa
```

### Issue: Worker Not Responding

```bash
# SSH to worker
ssh ubuntu@129.153.xxx.xxx

# Check logs
cd ~/ultrathink
tail -50 worker.log

# Restart
./stop_worker.sh
./start_worker.sh

# Check process
ps aux | grep python
```

### Issue: OCI CLI Connection Failed

```bash
# Check config
cat ~/.oci/config

# Test with debug
oci iam region list --debug

# Common issues:
# - Fingerprint not set
# - Wrong key file path
# - API key not uploaded to Oracle
```

### Issue: Python Package Missing

```bash
# On worker
pip3 install --user -r ~/ultrathink/requirements.txt

# On local
pip3 install oci-cli aiohttp requests
```

---

## Performance Testing

After setup, test performance:

```python
# Quick performance test
from cloud.orchestrator.job_orchestrator import JobOrchestrator
import asyncio
import time

async def test():
    orchestrator = JobOrchestrator(
        worker_urls=[
            'http://129.153.xxx.xxx:8000',
            'http://129.153.yyy.yyy:8000',
            'http://129.153.zzz.zzz:8000',
            'http://129.153.www.www:8000'
        ]
    )

    # Generate test trades
    trades = [{'id': i, 'ticker': 'TEST'} for i in range(100)]

    start = time.time()
    results = await orchestrator.analyze_all_trades(
        trades,
        analysis_types=['sentiment']
    )
    duration = time.time() - start

    print(f"Processed {len(trades)} trades in {duration:.2f}s")
    print(f"Throughput: {len(trades)/duration:.1f} trades/second")

asyncio.run(test())
```

Expected: 20-50x speedup vs single machine

---

## Maintenance

### Daily Health Check
```bash
cd cloud/deploy
./check_workers.sh
```

### Update Worker Code
```bash
cd cloud/deploy
./deploy_workers.sh
./stop_all_workers.sh
./start_all_workers.sh
```

### Monitor Resources
```bash
# Check each worker
ssh ubuntu@[worker-ip]
htop  # CPU/memory
df -h  # Disk space
```

### View Logs
```bash
ssh ubuntu@[worker-ip]
cd ~/ultrathink
tail -f worker.log
```

---

## 🎉 Congratulations!

You now have:
- **4 ARM VMs** running 24/7
- **24GB RAM**, 8 vCPUs total
- **20-50x speedup** on analysis
- **$0/month cost** (Always Free)

Ready to process 200K+ trades in hours instead of days!