#!/bin/bash
# Server Setup Script for Ubuntu 24.04
# Run this on your DigitalOcean droplet

set -e

echo "=========================================="
echo "  GAN Gaming Platform - Server Setup"
echo "=========================================="

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install required packages
echo "📦 Installing required packages..."
apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
apt install -y docker-compose-plugin

# Enable Docker service
systemctl enable docker
systemctl start docker

# Setup firewall
echo "🔥 Configuring firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw --force enable

# Create app directory
echo "📁 Creating application directory..."
mkdir -p /opt/gan
mkdir -p /opt/gan/frontend
mkdir -p /opt/gan/backend

echo "✅ Server setup complete!"
echo ""
echo "Next steps:"
echo "1. Upload your application files to /opt/gan"
echo "2. Run the deploy script"
