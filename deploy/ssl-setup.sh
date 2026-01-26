#!/bin/bash
# SSL Certificate Setup Script
# Run this after DNS propagation is complete

set -e

echo "=========================================="
echo "  SSL Certificate Setup"
echo "=========================================="

# Create temporary nginx config without SSL for certbot
cat > /etc/nginx/sites-available/gamersarena.network << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name gamersarena.network www.gamersarena.network api.gamersarena.network administrator.gamersarena.network;
    
    root /opt/gan/frontend;
    index index.html;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
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
EOF

# Ensure nginx config is linked
ln -sf /etc/nginx/sites-available/gamersarena.network /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Create certbot webroot directory
mkdir -p /var/www/certbot

# Test and reload nginx
nginx -t
systemctl reload nginx

echo "📋 Testing domain resolution..."
echo ""

# Check if domain resolves to this server
EXPECTED_IP="178.128.61.13"
DOMAIN_IP=$(dig +short gamersarena.network | head -1)

if [ "$DOMAIN_IP" != "$EXPECTED_IP" ]; then
    echo "⚠️ Warning: Domain not yet pointing to this server!"
    echo "   Expected: $EXPECTED_IP"
    echo "   Got: $DOMAIN_IP"
    echo ""
    echo "Please update your Namecheap DNS settings and wait for propagation."
    echo "You can check status at: https://dnschecker.org/#A/gamersarena.network"
    exit 1
fi

echo "✅ Domain is pointing to this server!"
echo ""

# Get SSL certificate
echo "🔒 Obtaining SSL certificate..."
certbot --nginx \
    -d gamersarena.network \
    -d www.gamersarena.network \
    -d api.gamersarena.network \
    -d administrator.gamersarena.network \
    --non-interactive \
    --agree-tos \
    --email admin@gamersarena.network \
    --redirect

echo ""
echo "✅ SSL certificate installed!"
echo ""

# Now apply the full production nginx config
cp /opt/gan/deploy/nginx-production.conf /etc/nginx/sites-available/gamersarena.network
nginx -t
systemctl reload nginx

echo "=========================================="
echo "  ✅ SSL Setup Complete!"
echo "=========================================="
echo ""
echo "Your site is now accessible at:"
echo "  - https://gamersarena.network"
echo "  - https://www.gamersarena.network"
echo "  - https://api.gamersarena.network"
echo "  - https://administrator.gamersarena.network"
