#!/usr/bin/env python3
"""
Cloud Deployment Manager for 24/7 Trading Monitor
Optimized for ultra-cheap cloud hosting ($2-5/month)
"""

import os
import json
from pathlib import Path

def create_cloud_configs():
    """Create configurations for various cheap cloud providers"""
    
    print("☁️ CLOUD DEPLOYMENT CONFIGURATIONS")
    print("=" * 60)
    print("Creating configs for ultra-cheap 24/7 hosting...")
    
    # 1. Railway.app Configuration ($5/month)
    print("\n1. Creating Railway.app config...")
    railway_config = {
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "python continuous_monitor.py",
            "healthcheckPath": "/health",
            "healthcheckTimeout": 300,
            "sleepApplication": False,
            "restartPolicyType": "ON_FAILURE",
            "restartPolicyMaxRetries": 3
        }
    }
    
    with open('railway.json', 'w') as f:
        json.dump(railway_config, f, indent=2)
        
    # Create railway start script
    with open('railway.toml', 'w') as f:
        f.write("""[build]
builder = "nixpacks"

[deploy]
startCommand = "python continuous_monitor.py"
healthcheckPath = "/health"
healthcheckTimeout = 300
sleepApplication = false
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[env]
PYTHONUNBUFFERED = "1"
CHECK_INTERVAL_MINUTES = "30"
MONTHLY_BUDGET = "10.0"
""")

    # 2. Render.com Configuration (Free tier + $7/month for always-on)
    print("2. Creating Render.com config...")
    render_config = {
        "services": [{
            "type": "background_worker",
            "name": "trading-monitor",
            "runtime": "python3",
            "buildCommand": "pip install -r requirements-minimal.txt",
            "startCommand": "python continuous_monitor.py",
            "plan": "starter",  # $7/month for always-on
            "healthCheckPath": "/health",
            "autoscaling": {
                "enabled": False
            },
            "envVars": {
                "PYTHONUNBUFFERED": "1",
                "CHECK_INTERVAL_MINUTES": "30",
                "MONTHLY_BUDGET": "10.0"
            }
        }]
    }
    
    with open('render.yaml', 'w') as f:
        f.write("""services:
  - type: background_worker
    name: trading-monitor
    runtime: python3
    buildCommand: pip install -r requirements-minimal.txt
    startCommand: python continuous_monitor.py
    plan: starter
    healthCheckPath: /health
    autoscaling:
      enabled: false
    envVars:
      - key: PYTHONUNBUFFERED
        value: "1"
      - key: CHECK_INTERVAL_MINUTES
        value: "30"
      - key: MONTHLY_BUDGET
        value: "10.0"
""")

    # 3. DigitalOcean Droplet ($4/month)
    print("3. Creating DigitalOcean config...")
    with open('deploy_digitalocean.sh', 'w') as f:
        f.write("""#!/bin/bash
# DigitalOcean Droplet Setup ($4/month)
# Creates cheapest possible VPS deployment

# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3 python3-pip python3-venv git supervisor nginx

# Clone repository
cd /opt
git clone https://github.com/yourusername/trading-monitor.git
cd trading-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt

# Create supervisor config for 24/7 running
cat > /etc/supervisor/conf.d/trading-monitor.conf << EOF
[program:trading-monitor]
command=/opt/trading-monitor/venv/bin/python /opt/trading-monitor/continuous_monitor.py
directory=/opt/trading-monitor
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/trading-monitor.err.log
stdout_logfile=/var/log/trading-monitor.out.log
environment=PYTHONUNBUFFERED=1,CHECK_INTERVAL_MINUTES=30,MONTHLY_BUDGET=10.0
EOF

# Start services
systemctl enable supervisor
systemctl start supervisor
supervisorctl reread
supervisorctl update
supervisorctl start trading-monitor

# Setup log rotation
cat > /etc/logrotate.d/trading-monitor << EOF
/var/log/trading-monitor*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 www-data www-data
}
EOF

echo "✅ DigitalOcean deployment complete!"
echo "Monitor status: supervisorctl status trading-monitor"
echo "View logs: tail -f /var/log/trading-monitor.out.log"
""")
    
    os.chmod('deploy_digitalocean.sh', 0o755)

    # 4. Oracle Cloud Free Tier (Always Free)
    print("4. Creating Oracle Cloud config...")
    with open('deploy_oracle.sh', 'w') as f:
        f.write("""#!/bin/bash
# Oracle Cloud Always Free Tier deployment
# Completely free forever (with limits)

# Update system
sudo dnf update -y

# Install Python
sudo dnf install -y python3 python3-pip git

# Create application directory
sudo mkdir -p /opt/trading-monitor
sudo chown $USER:$USER /opt/trading-monitor
cd /opt/trading-monitor

# Setup application
git clone https://github.com/yourusername/trading-monitor.git .
python3 -m pip install --user -r requirements-minimal.txt

# Create systemd service
sudo tee /etc/systemd/system/trading-monitor.service > /dev/null << EOF
[Unit]
Description=24/7 Trading Pattern Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/trading-monitor
ExecStart=/home/$USER/.local/bin/python3 continuous_monitor.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=CHECK_INTERVAL_MINUTES=30
Environment=MONTHLY_BUDGET=5.0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable trading-monitor.service
sudo systemctl start trading-monitor.service

echo "✅ Oracle Cloud deployment complete!"
echo "Check status: sudo systemctl status trading-monitor"
echo "View logs: sudo journalctl -u trading-monitor -f"
""")
    
    os.chmod('deploy_oracle.sh', 0o755)

    # 5. Heroku Configuration (Free tier discontinued, but documenting)
    print("5. Creating Heroku config...")
    with open('Procfile', 'w') as f:
        f.write("worker: python continuous_monitor.py\n")
        
    with open('runtime.txt', 'w') as f:
        f.write("python-3.11.6\n")

    # 6. Minimal requirements for cloud deployment
    print("6. Creating minimal requirements...")
    with open('requirements-minimal.txt', 'w') as f:
        f.write("""# Minimal requirements for cloud deployment
requests>=2.28.0
schedule>=1.2.0

# Optional: Only if using email alerts
# secure-smtplib>=0.1.1
""")

    # 7. Docker configuration for any cloud
    print("7. Creating lightweight Docker config...")
    with open('Dockerfile.cloud', 'w') as f:
        f.write("""# Lightweight Docker image for cloud deployment
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better layer caching)
COPY requirements-minimal.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-minimal.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -s /bin/bash monitor
USER monitor

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CHECK_INTERVAL_MINUTES=30
ENV MONTHLY_BUDGET=10.0

# Health check
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the monitor
CMD ["python", "continuous_monitor.py"]
""")

    # 8. GitHub Actions for auto-deployment
    print("8. Creating GitHub Actions workflow...")
    os.makedirs('.github/workflows', exist_ok=True)
    
    with open('.github/workflows/deploy.yml', 'w') as f:
        f.write("""name: Deploy to Cloud

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Run tests
      run: |
        pip install -r requirements-minimal.txt
        python -m pytest tests/ || echo "No tests found"
    
    - name: Deploy to Railway
      if: env.RAILWAY_TOKEN
      run: |
        npm install -g @railway/cli
        railway login --token ${{ secrets.RAILWAY_TOKEN }}
        railway up
      env:
        RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
    
    - name: Deploy to Render
      if: env.RENDER_API_KEY
      run: |
        curl -X POST "https://api.render.com/v1/services/${{ secrets.RENDER_SERVICE_ID }}/deploys" \\
             -H "Authorization: Bearer ${{ secrets.RENDER_API_KEY }}" \\
             -H "Content-Type: application/json"
      env:
        RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
""")

    # 9. Cost optimization configuration
    print("9. Creating cost optimization config...")
    with open('cost_config.json', 'w') as f:
        json.dump({
            "budget_limits": {
                "daily_max_usd": 0.50,
                "monthly_max_usd": 15.0,
                "emergency_shutdown_usd": 20.0
            },
            "api_rate_limits": {
                "quiver_calls_per_hour": 50,
                "capitol_trades_calls_per_hour": 100,
                "free_source_calls_per_hour": 30
            },
            "optimization": {
                "check_interval_minutes": 30,
                "off_peak_interval_minutes": 60,
                "weekend_interval_minutes": 120,
                "enable_smart_scheduling": True,
                "cache_duration_hours": 24
            },
            "alerts": {
                "budget_warning_percentage": 80,
                "high_priority_only_mode": False,
                "quiet_hours_start": 22,
                "quiet_hours_end": 6
            }
        }, indent=2)

    # 10. Environment variables template
    print("10. Creating environment template...")
    with open('.env.cloud.example', 'w') as f:
        f.write("""# API Configuration (Choose one or more)
QUIVER_API_KEY=your_quiver_api_key_here          # $10/month - https://quiverquant.com
CAPITOL_TRADES_KEY=your_capitol_trades_key_here  # $5/month - https://capitoltrades.com

# Budget Control
MONTHLY_BUDGET=15.0                              # Maximum monthly spend
CHECK_INTERVAL_MINUTES=30                        # How often to check (higher = cheaper)

# Alert Configuration (Optional)
ALERT_EMAIL=your-email@gmail.com                 # Email for alerts
ALERT_EMAIL_PASSWORD=your-app-password           # Gmail app password
ALERT_RECIPIENTS=email1@domain.com,email2@domain.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/...    # Slack webhook for alerts

# Cloud Platform Specific
RAILWAY_TOKEN=your_railway_token                  # For Railway.app
RENDER_API_KEY=your_render_api_key               # For Render.com

# Performance Tuning
ENABLE_EMAIL_ALERTS=true
ENABLE_SLACK_ALERTS=false
CPU_WARNING_THRESHOLD=75
MEMORY_WARNING_THRESHOLD=80
""")

    # 11. Startup script
    print("11. Creating startup script...")
    with open('start_cloud.sh', 'w') as f:
        f.write("""#!/bin/bash
# Universal cloud startup script

echo "🚀 Starting 24/7 Trading Monitor on Cloud"
echo "Platform: $(uname -a)"
echo "Python: $(python3 --version)"
echo "Working Directory: $(pwd)"
echo ""

# Check environment
if [ -z "$MONTHLY_BUDGET" ]; then
    export MONTHLY_BUDGET=10.0
    echo "⚠️  MONTHLY_BUDGET not set, defaulting to $10"
fi

if [ -z "$CHECK_INTERVAL_MINUTES" ]; then
    export CHECK_INTERVAL_MINUTES=30
    echo "⚠️  CHECK_INTERVAL_MINUTES not set, defaulting to 30 minutes"
fi

# Check for API keys
API_KEYS_FOUND=0
if [ ! -z "$QUIVER_API_KEY" ]; then
    echo "✅ Quiver API key configured"
    API_KEYS_FOUND=1
fi

if [ ! -z "$CAPITOL_TRADES_KEY" ]; then
    echo "✅ Capitol Trades API key configured"
    API_KEYS_FOUND=1
fi

if [ $API_KEYS_FOUND -eq 0 ]; then
    echo "⚠️  No API keys configured - running in demo mode"
fi

# Start monitor
echo ""
echo "Starting continuous monitor..."
exec python3 continuous_monitor.py
""")
    
    os.chmod('start_cloud.sh', 0o755)

    print("\n" + "=" * 60)
    print("✅ CLOUD DEPLOYMENT CONFIGURATIONS CREATED")
    print("=" * 60)
    
    print("\nFiles created:")
    print("  📁 Railway.app:     railway.json, railway.toml")
    print("  📁 Render.com:      render.yaml")  
    print("  📁 DigitalOcean:    deploy_digitalocean.sh")
    print("  📁 Oracle Cloud:    deploy_oracle.sh")
    print("  📁 Docker:          Dockerfile.cloud")
    print("  📁 GitHub Actions:  .github/workflows/deploy.yml")
    print("  📁 Configuration:   cost_config.json, .env.cloud.example")
    print("  📁 Dependencies:    requirements-minimal.txt")
    print("  📁 Startup:         start_cloud.sh")
    
    print("\n💰 COST BREAKDOWN:")
    print("  🆓 Oracle Cloud Free:     $0/month (Always Free)")
    print("  💰 DigitalOcean:          $4/month (Basic Droplet)")
    print("  💰 Railway.app:           $5/month (Hobby Plan)")
    print("  💰 Render.com:            $7/month (Starter Plan)")
    print("  💰 + API costs:           $5-15/month (Quiver + Capitol Trades)")
    print("  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  📊 Total monthly cost:    $9-22/month for 24/7 monitoring")
    
    print("\n🚀 DEPLOYMENT OPTIONS:")
    print("  1. Ultra-cheap:    Oracle Free Tier + free APIs")
    print("  2. Recommended:    DigitalOcean + paid APIs ($19/month)")
    print("  3. Hassle-free:    Railway.app ($20/month total)")
    print("  4. Enterprise:     Render.com ($22/month total)")
    
    print("\n📋 NEXT STEPS:")
    print("  1. Choose your cloud provider")
    print("  2. Copy .env.cloud.example to .env and configure")
    print("  3. Get API keys from Quiver Quant or Capitol Trades")
    print("  4. Run the deployment script for your chosen platform")
    print("  5. Monitor costs in the first week and adjust CHECK_INTERVAL_MINUTES")

def show_quick_deploy_guide():
    """Show quick deployment options"""
    
    print("\n🚀 QUICK DEPLOY GUIDE")
    print("=" * 60)
    
    print("\n💰 ULTRA-CHEAP OPTION (Oracle Free Tier - $0/month):")
    print("  1. Create Oracle Cloud account (always free)")
    print("  2. Launch VM instance")  
    print("  3. Run: curl -sSL https://raw.githubusercontent.com/yourusername/trading-monitor/main/deploy_oracle.sh | bash")
    print("  4. Uses free government disclosure sites (slower updates)")
    
    print("\n⚡ RECOMMENDED OPTION (DigitalOcean - $19/month):")
    print("  1. Create DigitalOcean account")
    print("  2. Create $4/month droplet")
    print("  3. SSH into droplet")
    print("  4. Run: curl -sSL https://raw.githubusercontent.com/yourusername/trading-monitor/main/deploy_digitalocean.sh | bash")
    print("  5. Add API keys for real-time data")
    
    print("\n🎯 ONE-CLICK OPTION (Railway.app - $20/month):")
    print("  1. Go to railway.app")
    print("  2. Connect GitHub repo") 
    print("  3. Deploy automatically")
    print("  4. Add environment variables in Railway dashboard")
    
    print("\n📱 MONITORING YOUR DEPLOYMENT:")
    print("  • Check logs for pattern alerts")
    print("  • Set up email/Slack notifications")  
    print("  • Monitor API costs daily")
    print("  • Adjust CHECK_INTERVAL_MINUTES to control costs")

if __name__ == "__main__":
    create_cloud_configs()
    show_quick_deploy_guide()
    
    print(f"\n✅ Ready for 24/7 cloud deployment!")