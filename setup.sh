#!/bin/bash
# GAN - Gamers Arena Network
# One-Click Setup Script
# Run with: bash <(curl -s https://raw.githubusercontent.com/hamzaiqbai/gamersarena-network/main/setup.sh)

set -e
echo "==========================================="
echo "  GAN Gaming Platform - Auto Setup"
echo "==========================================="

# Clone repo
echo "[1/7] Cloning repository..."
cd /opt/gan
rm -rf /opt/gan/* /opt/gan/.* 2>/dev/null || true
git clone https://github.com/hamzaiqbai/gamersarena-network.git .

# Setup Python environment
echo "[2/7] Setting up Python..."
cd /opt/gan/backend
python3 -m venv venv
source venv/bin/activate
pip install --quiet -r requirements.txt

# Create .env file
echo "[3/7] Creating environment file..."
cat > /opt/gan/backend/.env << 'ENVFILE'
DATABASE_URL=postgresql://doadmin:AVNS_dsDs5ivMEc-3JhJ-87y@gan-db-do-user-30768850-0.m.db.ondigitalocean.com:25060/defaultdb?sslmode=require
SECRET_KEY=GAN-Production-Secret-Key-2026-Super-Secure
GOOGLE_CLIENT_ID=288371731066-rep26filnaba8kedlfbsrp7hh7e7d7ta.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
GOOGLE_REDIRECT_URI=https://gamersarena.network/api/auth/google/callback
WHATSAPP_PHONE_NUMBER_ID=952770604587145
WHATSAPP_BUSINESS_ACCOUNT_ID=1416105946683694
WHATSAPP_ACCESS_TOKEN=placeholder
ENVIRONMENT=production
DEBUG=false
ENVFILE

# Create systemd service
echo "[4/7] Creating backend service..."
cat > /etc/systemd/system/gan-backend.service << 'SERVICEFILE'
[Unit]
Description=GAN Backend API
After=network.target

[Service]
User=root
WorkingDirectory=/opt/gan/backend
Environment="PATH=/opt/gan/backend/venv/bin"
ExecStart=/opt/gan/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
SERVICEFILE

systemctl daemon-reload
systemctl enable gan-backend
systemctl start gan-backend

# Configure Nginx
echo "[5/7] Configuring Nginx..."
cat > /etc/nginx/sites-available/gamersarena.network << 'NGINXFILE'
server {
    listen 80;
    server_name gamersarena.network www.gamersarena.network;
    
    root /opt/gan/frontend;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINXFILE

ln -sf /etc/nginx/sites-available/gamersarena.network /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# Test backend
echo "[6/7] Testing backend..."
sleep 3
if curl -s http://127.0.0.1:8000/api/health | grep -q "healthy"; then
    echo "Backend is running!"
else
    echo "Backend may still be starting..."
fi

echo "[7/7] Getting SSL certificate..."
certbot --nginx -d gamersarena.network -d www.gamersarena.network --non-interactive --agree-tos --email admin@gamersarena.network --redirect || echo "SSL setup needs manual completion"

echo ""
echo "==========================================="
echo "  SETUP COMPLETE!"
echo "==========================================="
echo ""
echo "Your site: https://gamersarena.network"
echo ""
echo "To check status:"
echo "  systemctl status gan-backend"
echo "  curl http://127.0.0.1:8000/api/health"
