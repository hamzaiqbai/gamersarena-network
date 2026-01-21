#!/bin/bash
# Deployment Script for GAN Gaming Platform
# Run this after uploading files to /opt/gan

set -e

echo "=========================================="
echo "  GAN Gaming Platform - Deployment"
echo "=========================================="

cd /opt/gan

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create /opt/gan/.env with your environment variables"
    exit 1
fi

# Build and start containers
echo "🐳 Building and starting Docker containers..."
docker compose -f docker-compose.prod.yml up -d --build

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
sleep 10

# Check backend health
echo "🔍 Checking backend health..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️ Backend health check failed, checking logs..."
    docker logs gan-backend --tail 50
fi

# Setup Nginx if not already configured
if [ ! -f "/etc/nginx/sites-enabled/gamersarena.network" ]; then
    echo "🔧 Configuring Nginx..."
    cp /opt/gan/deploy/nginx-production.conf /etc/nginx/sites-available/gamersarena.network
    ln -sf /etc/nginx/sites-available/gamersarena.network /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx config
    nginx -t
    
    echo "✅ Nginx configured!"
fi

# Reload Nginx
echo "🔄 Reloading Nginx..."
systemctl reload nginx

echo ""
echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Your site should be accessible at:"
echo "  - http://gamersarena.network (will redirect to HTTPS after SSL)"
echo ""
echo "Next: Run SSL setup with:"
echo "  certbot --nginx -d gamersarena.network -d www.gamersarena.network -d api.gamersarena.network"
