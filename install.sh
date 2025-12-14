#!/bin/bash
# Installation script for Linux

set -e

echo "Installing faneX-ID OnPrem Connector..."

# Create directories
sudo mkdir -p /etc/fanexid-connector
sudo mkdir -p /var/log/fanexid-connector
sudo mkdir -p /opt/fanexid-connector

# Copy files
sudo cp -r * /opt/fanexid-connector/
sudo cp config.ini.example /etc/fanexid-connector/config.ini

# Create systemd service
sudo tee /etc/systemd/system/fanexid-connector.service > /dev/null <<EOF
[Unit]
Description=faneX-ID OnPrem Connector
After=network.target

[Service]
Type=simple
User=fanexid
Group=fanexid
WorkingDirectory=/opt/fanexid-connector
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create user
sudo useradd -r -s /bin/false fanexid || true

# Set permissions
sudo chown -R fanexid:fanexid /opt/fanexid-connector
sudo chown -R fanexid:fanexid /var/log/fanexid-connector
sudo chmod 600 /etc/fanexid-connector/config.ini

# Install Python dependencies
sudo pip3 install -r /opt/fanexid-connector/requirements.txt

# Reload systemd
sudo systemctl daemon-reload

echo "Installation complete!"
echo "Configure /etc/fanexid-connector/config.ini and then run:"
echo "  sudo systemctl start fanexid-connector"
echo "  sudo systemctl enable fanexid-connector"
