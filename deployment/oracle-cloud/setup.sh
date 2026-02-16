#!/bin/bash
#
# Oracle Cloud VM Initial Setup Script
# Run this script after provisioning a fresh Ubuntu 22.04 VM
#
# Usage: sudo bash setup.sh
#

set -e  # Exit on error

echo "========================================="
echo "Oracle Cloud VM Setup - Personal AI Employee"
echo "========================================="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
  echo "❌ Please run as root or with sudo"
  exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt update
apt upgrade -y

# Install base dependencies
echo "🔧 Installing base dependencies..."
apt install -y \
  software-properties-common \
  build-essential \
  curl \
  wget \
  git \
  vim \
  htop \
  ufw

# Install Python 3.11
echo "🐍 Installing Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa
apt update
apt install -y \
  python3.11 \
  python3.11-venv \
  python3.11-dev \
  python3-pip

# Set Python 3.11 as default
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

echo "✓ Python version: $(python3 --version)"

# Install Node.js 20 (for PM2)
echo "📦 Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

echo "✓ Node.js version: $(node --version)"
echo "✓ npm version: $(npm --version)"

# Install PM2 globally
echo "⚙️ Installing PM2..."
npm install -g pm2

echo "✓ PM2 version: $(pm2 --version)"

# Configure firewall (UFW)
echo "🔒 Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   # SSH
ufw allow 443/tcp  # HTTPS (for Odoo later)
ufw allow 8069/tcp # Odoo (temporary)

echo "✓ Firewall configured"
ufw status

# Create project directory
echo "📁 Creating project directory..."
mkdir -p /opt/personal-ai-employee
chown ubuntu:ubuntu /opt/personal-ai-employee

echo ""
echo "========================================="
echo "✅ VM setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Exit sudo and run as ubuntu user"
echo "2. Generate SSH key: ssh-keygen -t ed25519 -C 'cloud-agent@oracle-vm'"
echo "3. Add SSH key to GitHub"
echo "4. Clone repo: git clone git@github.com:user/personal-ai-employee.git /opt/personal-ai-employee"
echo "5. Run deploy.sh to install Python dependencies"
echo ""
