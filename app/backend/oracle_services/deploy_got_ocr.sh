#!/bin/bash
# Deploy GOT-OCR2 service to Oracle server
# Usage: ./deploy_got_ocr.sh

set -e

ORACLE_IP="129.153.97.27"
ORACLE_USER="opc"
SSH_KEY="$HOME/Oracle_data/ssh-key-2025-05-12.key"

echo "=== Deploying GOT-OCR2 Service to Oracle ==="

# Create service directory on Oracle
ssh -i "$SSH_KEY" "$ORACLE_USER@$ORACLE_IP" "sudo mkdir -p /opt/got-ocr && sudo chown opc:opc /opt/got-ocr"

# Copy the service file
scp -i "$SSH_KEY" got_ocr_service.py "$ORACLE_USER@$ORACLE_IP:/opt/got-ocr/"

# Create requirements file
cat << 'EOF' > /tmp/got_ocr_requirements.txt
fastapi>=0.104.0
uvicorn>=0.24.0
python-multipart>=0.0.6
torch>=2.0.0
transformers>=4.35.0
pillow>=10.0.0
requests>=2.31.0
tiktoken>=0.5.0
accelerate>=0.24.0
EOF

scp -i "$SSH_KEY" /tmp/got_ocr_requirements.txt "$ORACLE_USER@$ORACLE_IP:/opt/got-ocr/requirements.txt"

# Create systemd service file
cat << 'EOF' > /tmp/got-ocr.service
[Unit]
Description=GOT-OCR2 Document OCR Service
After=network.target ollama.service

[Service]
Type=simple
User=opc
WorkingDirectory=/opt/got-ocr
Environment="PATH=/usr/local/bin:/usr/bin"
ExecStart=/usr/bin/scl enable gcc-toolset-10 -- /usr/bin/python3.9 -m uvicorn got_ocr_service:app --host 0.0.0.0 --port 8082
Restart=on-failure
RestartSec=10

# Resource limits
MemoryMax=8G
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

scp -i "$SSH_KEY" /tmp/got-ocr.service "$ORACLE_USER@$ORACLE_IP:/tmp/got-ocr.service"

# Install dependencies and set up service
ssh -i "$SSH_KEY" "$ORACLE_USER@$ORACLE_IP" << 'REMOTE_SCRIPT'
set -e

echo "=== Installing Python dependencies ==="
cd /opt/got-ocr
scl enable gcc-toolset-10 -- python3.9 -m pip install -r requirements.txt

echo "=== Setting up systemd service ==="
sudo mv /tmp/got-ocr.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable got-ocr

echo "=== Starting GOT-OCR2 service ==="
sudo systemctl start got-ocr

sleep 5
echo "=== Service status ==="
systemctl is-active got-ocr || echo "Service may take time to start (model loading)"

echo "=== Checking port ==="
curl -s http://localhost:8082/health || echo "Service starting up..."
REMOTE_SCRIPT

echo ""
echo "=== Deployment complete ==="
echo "Service URL: http://$ORACLE_IP:8082"
echo ""
echo "Commands:"
echo "  Check status: ssh -i $SSH_KEY $ORACLE_USER@$ORACLE_IP 'systemctl status got-ocr'"
echo "  View logs:    ssh -i $SSH_KEY $ORACLE_USER@$ORACLE_IP 'journalctl -u got-ocr -f'"
echo "  Test OCR:     curl http://$ORACLE_IP:8082/health"
