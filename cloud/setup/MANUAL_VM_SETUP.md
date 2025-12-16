# Oracle Cloud VM Manual Setup Guide

## ✅ Your Configuration is Ready!

Your Oracle Cloud credentials are configured:
- **User OCID**: ✅ Configured
- **Tenancy OCID**: ✅ Configured
- **Fingerprint**: ✅ `f0:02:61:70:fd:35:eb:67:a6:20:3a:08:ab:f4:4f:6f`
- **Region**: ✅ us-chicago-1 (ORD)
- **API Keys**: ✅ Uploaded to Oracle Cloud

## 🚀 Create 4 ARM VMs in Oracle Console

### Step 1: Open Oracle Cloud Console
Go to: https://cloud.oracle.com

### Step 2: Create Virtual Cloud Network (VCN)
1. Navigate to **Networking** → **Virtual Cloud Networks**
2. Click **Start VCN Wizard**
3. Select **Create VCN with Internet Connectivity**
4. Configuration:
   - **VCN Name**: `ultrathink-vcn`
   - **CIDR Block**: Keep default (10.0.0.0/16)
5. Click **Next** → **Create**

### Step 3: Configure Security Rules
1. In VCN details, click **Security Lists** → **Default Security List**
2. Click **Add Ingress Rules** and add:

**Rule 1 - SSH:**
- Source Type: CIDR
- Source CIDR: `0.0.0.0/0`
- IP Protocol: TCP
- Destination Port Range: `22`

**Rule 2 - Worker API:**
- Source Type: CIDR
- Source CIDR: `0.0.0.0/0`
- IP Protocol: TCP
- Destination Port Range: `8000`

### Step 4: Create 4 Compute Instances

⚠️ **IMPORTANT**: Oracle's free ARM instances are popular and may show "Out of Capacity". If this happens:
- Try different Availability Domain (AD-1, AD-2, or AD-3)
- Try early morning (6-8 AM) or late night (11 PM - 2 AM)
- Create 2 instances with 2 OCPUs each instead of 4x1

For **EACH** VM (repeat 4 times):

1. Go to **Compute** → **Instances**
2. Click **Create Instance**

**Configuration for each VM:**

**Name**:
- `ultrathink-worker-1` (then 2, 3, 4)

**Placement:**
- Keep defaults (try different AD if out of capacity)

**Image and shape:**
1. Click **Change image**
   - Select **Ubuntu** → **Canonical Ubuntu 22.04**
2. Click **Change shape**
   - Instance type: **Virtual machine**
   - Shape series: **Ampere** (ARM processor)
   - Shape name: **VM.Standard.A1.Flex**
   - Number of OCPUs: **1**
   - Amount of memory (GB): **6**

**Networking:**
- VCN: `ultrathink-vcn`
- Subnet: Public subnet (default)
- **Assign a public IPv4 address**: ✅ Yes (IMPORTANT!)

**Add SSH keys:**
- Generate SSH key pair (if you don't have one)
- Or paste your public key

**Boot volume:**
- Keep defaults (50 GB)

3. Click **Create**

4. **IMPORTANT**: Copy the public IP address once the instance is running

### Step 5: Save Worker IPs

After all 4 VMs are created and running, create the workers.txt file:

```bash
cd /mnt/e/projects/discovery/cloud/deploy
cat > workers.txt << EOF
[REPLACE WITH YOUR ACTUAL IPs]
129.153.XXX.XXX
129.153.YYY.YYY
129.153.ZZZ.ZZZ
129.153.WWW.WWW
EOF
```

## 📋 Checklist

- [ ] VCN created: `ultrathink-vcn`
- [ ] Security rules added (ports 22, 8000)
- [ ] Worker 1 created - IP: ________________
- [ ] Worker 2 created - IP: ________________
- [ ] Worker 3 created - IP: ________________
- [ ] Worker 4 created - IP: ________________
- [ ] workers.txt file created with IPs

## 🎯 Next Steps

Once all VMs are created:

```bash
# 1. Deploy code to workers
cd /mnt/e/projects/discovery/cloud/deploy
./deploy_workers.sh

# 2. Start worker services
./start_all_workers.sh

# 3. Verify health
./check_workers.sh
```

## 🆘 Troubleshooting

### "Out of Capacity" Error
This is common with free ARM instances. Solutions:
1. **Try different Availability Domain** (AD-1, AD-2, AD-3)
2. **Try different times** (early morning/late night)
3. **Alternative config**: Create 2 VMs with 2 OCPUs each
4. **Keep trying** - capacity opens up frequently

### Can't SSH to VM
```bash
# Test with verbose output
ssh -v ubuntu@[IP-ADDRESS]

# Common fixes:
# 1. Check Security List has port 22 open
# 2. Use correct username: ubuntu (not opc or ec2-user)
# 3. Check VM is in RUNNING state
```

### Instance Won't Start
- Check your tenancy limits (Compute → Limits)
- Ensure you're in the Always Free eligible region
- Try a different shape if A1.Flex unavailable

## 📞 Success Verification

After creating all VMs, verify with:

```bash
cd /mnt/e/projects/discovery/cloud
./oracle_status.sh
```

You should see:
- ✅ 4 Workers Configured
- ✅ All deployment scripts ready

---

**Need help?** The "Out of Capacity" error is normal - just keep trying at different times!