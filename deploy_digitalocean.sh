#!/bin/bash
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
