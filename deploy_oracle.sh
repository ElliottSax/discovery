#!/bin/bash
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
