# Oracle A1.Flex Auto-Provisioning

Automated system to continuously retry provisioning Oracle Cloud A1.Flex instances until successful.

## The Problem

Oracle's free tier A1 (ARM) instances are **always at capacity**. Manual attempts fail with "Out of capacity" errors. You need to retry constantly during off-peak hours.

## The Solution

Automated retry system that:
- ✅ Tries all 3 availability domains
- ✅ Retries with exponential backoff (5-30 min intervals)
- ✅ Runs 24/7 in background
- ✅ Auto-adds instances to workers.txt when successful
- ✅ Stops automatically when target reached
- ✅ Logs all attempts

## Quick Start

### 1. Start Auto-Provisioning (Background)

```bash
cd /mnt/e/projects/discovery/cloud/setup
./auto_provision.sh --background
```

This will:
- Run continuously in background
- Try to provision 4 A1.Flex instances
- Retry every 5-30 minutes
- Stop when all 4 are created

### 2. Watch Progress

```bash
./watch_provision.sh
```

Live dashboard showing:
- Current instance count
- Recent attempts
- Real-time log streaming

### 3. Check Status Anytime

```bash
./auto_provision.sh --status
```

### 4. Stop When Done

```bash
./auto_provision.sh --stop
```

## Options

```bash
# Foreground (see output directly)
./auto_provision.sh

# Background (recommended)
./auto_provision.sh --background

# Watch live progress
./watch_provision.sh

# Check status
./auto_provision.sh --status

# Stop background process
./auto_provision.sh --stop

# Help
./auto_provision.sh --help
```

## How It Works

### Retry Strategy

1. **Try all 3 availability domains** in sequence
2. **If all fail**: Wait 5 minutes, try again
3. **Still failing**: Increase wait time (5min → 7.5min → 11min → 16min → 24min → 30min max)
4. **Success**: Reset wait time to 5 minutes, continue provisioning next instance
5. **All 4 created**: Stop automatically

### Best Times to Provision

Oracle's A1 capacity varies by time:

**Best** (higher success rate):
- 2-8 AM Chicago time (weekdays)
- Late night/early morning
- Weekends

**Worst** (always at capacity):
- Business hours (9 AM - 5 PM)
- Evening (6-10 PM)

**The auto-provisioning system runs 24/7, so just let it run!**

## What Gets Created

Each successful provision creates:

**Instance:**
- Shape: VM.Standard.A1.Flex
- CPU: 1 OCPU (ARM)
- RAM: 6 GB
- Name: discovery-worker-1, discovery-worker-2, etc.
- SSH: Your current key (~/.ssh/id_rsa.pub)
- Network: Auto-assigned public IP

**Files Updated:**
- `cloud/deploy/workers.txt` - Worker IP list
- `~/.oracle_auto_provision/success.txt` - Successful IPs
- `~/.oracle_auto_provision/provision.log` - Full log

## Logs

All activity logged to:
```
~/.oracle_auto_provision/provision.log
```

View logs:
```bash
# Live tail
tail -f ~/.oracle_auto_provision/provision.log

# Last 50 lines
tail -50 ~/.oracle_auto_provision/provision.log

# Search for successes
grep "SUCCESS" ~/.oracle_auto_provision/provision.log
```

## After Successful Provisioning

Once instances are created:

### 1. Verify Instances
```bash
~/.local/bin/oci compute instance list \
  --compartment-id ocid1.tenancy.oc1..aaaaaaaa2ktu74gnhxcctwnk65ntpj6gfb53ofanbz2ram3jkm62ke5ekpsa \
  --lifecycle-state RUNNING
```

### 2. Check Workers File
```bash
cat cloud/deploy/workers.txt
```

Should contain 4 IPs:
```
XXX.XXX.XXX.XXX:8000
XXX.XXX.XXX.XXX:8000
XXX.XXX.XXX.XXX:8000
XXX.XXX.XXX.XXX:8000
```

### 3. Deploy Worker Software
```bash
cd cloud/deploy
./deploy_workers.sh
```

This will:
- SSH to each instance
- Upload code
- Install dependencies
- Create start/stop scripts

### 4. Start Workers
```bash
./start_all_workers.sh
```

### 5. Verify Health
```bash
python3 ../monitor/check_all_workers.py
```

Should show 4 healthy workers!

## Troubleshooting

### No instances after 24 hours

Oracle capacity is VERY tight. Some tips:
- Let it run for several days
- Capacity opens up randomly
- Higher success rate late night/early morning
- Consider different regions (but free tier region-locked)

### Script keeps failing

Check:
```bash
# Verify OCI CLI works
~/.local/bin/oci iam region list

# Check quota
~/.local/bin/oci limits resource-availability get \
  --service-name compute \
  --limit-name vm-standard-a1-flex-core-count \
  --compartment-id ocid1.tenancy.oc1..aaaaaaaa2ktu74gnhxcctwnk65ntpj6gfb53ofanbz2ram3jkm62ke5ekpsa
```

### Process died

Restart:
```bash
./auto_provision.sh --background
```

It will resume from current count (won't recreate existing instances).

### Want to run on system startup

Use systemd service:
```bash
# Install service
sudo cp oracle-auto-provision.service /etc/systemd/system/

# Enable (starts on boot)
sudo systemctl enable oracle-auto-provision

# Start now
sudo systemctl start oracle-auto-provision

# Check status
sudo systemctl status oracle-auto-provision

# View logs
sudo journalctl -u oracle-auto-provision -f
```

## Advanced Configuration

Edit `/mnt/e/projects/discovery/cloud/setup/auto_provision.sh`:

```bash
# Number of instances (default: 4)
TARGET_INSTANCES=4

# Min wait between retries (default: 5 min)
MIN_WAIT=300

# Max wait between retries (default: 30 min)
MAX_WAIT=1800

# Instance specs (default: 1 OCPU, 6GB RAM)
--shape-config '{"ocpus":1,"memory-in-gbs":6}'

# Or use 2 instances with 2 OCPUs each:
--shape-config '{"ocpus":2,"memory-in-gbs":12}'
```

## Success Metrics

Typical results:
- **1-3 days**: Usually get 1-2 instances
- **3-7 days**: Get 3-4 instances (full quota)
- **7+ days**: If still nothing, check account/region

Your free tier quota:
- **4 OCPUs total** (can be 4×1 or 2×2 or 1×4)
- **24 GB RAM total**
- **200 GB storage total**

## Cost

**$0** - This uses Oracle's Always Free tier. Never charged.

## What If I Get Impatient?

Options:
1. **Wait it out** - Free is free, patience pays off
2. **Try different region** - Create new account in different region
3. **Use other free compute** - HuggingFace, Colab (see FREE_COMPUTE_GUIDE.md)
4. **Paid instances** - A1.Flex is ~$0.01/hour if you can't wait

## Example Session

```bash
$ ./auto_provision.sh --background
Starting auto-provisioning in background...
Started with PID: 12345

Monitor progress:
  tail -f /home/elliott/.oracle_auto_provision/provision.log

Stop process:
  ./auto_provision.sh --stop

$ ./watch_provision.sh
╔════════════════════════════════════════════════════════════════════╗
║        Oracle A1 Auto-Provisioning - Live Monitor                 ║
╚════════════════════════════════════════════════════════════════════╝

✓ Auto-provisioning is RUNNING (PID: 12345)
Current instances: 0/4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Live Log (Ctrl+C to exit):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[2025-12-13 12:00:00] Attempt #1 - Current instances: 0/4
[2025-12-13 12:00:01] Attempting to create instance 1 in TEQo:US-CHICAGO-1-AD-1...
[2025-12-13 12:00:05] ❌ Out of capacity in TEQo:US-CHICAGO-1-AD-1
[2025-12-13 12:00:06] Attempting to create instance 1 in TEQo:US-CHICAGO-1-AD-2...
[2025-12-13 12:00:10] ❌ Out of capacity in TEQo:US-CHICAGO-1-AD-2
[2025-12-13 12:00:11] Attempting to create instance 1 in TEQo:US-CHICAGO-1-AD-3...
[2025-12-13 12:00:15] ❌ Out of capacity in TEQo:US-CHICAGO-1-AD-3
[2025-12-13 12:00:16] ⏳ All ADs at capacity. Waiting 300 seconds...
[2025-12-13 12:00:16]    (Next try: 12:05:16)

... [5 minutes later] ...

[2025-12-13 12:05:16] Attempt #2 - Current instances: 0/4
[2025-12-13 12:05:17] Attempting to create instance 1 in TEQo:US-CHICAGO-1-AD-1...
[2025-12-13 12:05:25] ✅ SUCCESS! Instance created in TEQo:US-CHICAGO-1-AD-1
[2025-12-13 12:05:35] 🌐 Public IP: 152.67.123.45
[2025-12-13 12:05:36] 📝 Added to workers.txt

... [continues until 4 instances created] ...

[2025-12-13 14:23:45] 🎉 SUCCESS! All 4 instances provisioned!
```

## Summary

**Just run this and forget about it:**
```bash
cd /mnt/e/projects/discovery/cloud/setup
./auto_provision.sh --background
```

Check back in a few days - you'll have free compute!
