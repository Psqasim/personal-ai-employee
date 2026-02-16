#!/bin/bash
#
# Start Cloud Agent with PM2
# Run this after configuring .env.cloud and vault
#
# Usage: bash start.sh
#

set -e  # Exit on error

echo "========================================="
echo "Starting Cloud Agent with PM2"
echo "========================================="
echo ""

# Check if running from project root
if [ ! -f "ecosystem.config.js" ]; then
  echo "❌ Error: ecosystem.config.js not found"
  echo "Please run this script from the project root directory"
  exit 1
fi

# Check if .env.cloud exists
if [ ! -f ".env.cloud" ]; then
  echo "❌ Error: .env.cloud not found"
  echo "Please create .env.cloud from .env.cloud.example and configure it"
  exit 1
fi

# Check if vault exists
if [ ! -d "vault" ]; then
  echo "❌ Error: vault/ directory not found"
  echo "Please clone or create vault directory"
  exit 1
fi

# Load .env.cloud to verify configuration
source .env.cloud

if [ -z "$VAULT_PATH" ]; then
  echo "❌ Error: VAULT_PATH not set in .env.cloud"
  exit 1
fi

if [ -z "$CLAUDE_API_KEY" ]; then
  echo "❌ Error: CLAUDE_API_KEY not set in .env.cloud"
  exit 1
fi

echo "✓ Configuration validated"
echo ""

# Check PM2 installed
if ! command -v pm2 &> /dev/null; then
  echo "❌ Error: PM2 not installed"
  echo "Run: sudo npm install -g pm2"
  exit 1
fi

echo "✓ PM2 version: $(pm2 --version)"
echo ""

# Stop any existing processes
echo "🛑 Stopping existing Cloud Agent processes..."
pm2 delete all 2>/dev/null || true

# Start Cloud Agent processes
echo "🚀 Starting Cloud Agent processes..."
pm2 start ecosystem.config.js

echo ""
echo "⏳ Waiting for processes to start..."
sleep 3

# Display process list
echo ""
pm2 list

# Display logs (last 10 lines)
echo ""
echo "📋 Recent logs:"
pm2 logs --lines 10 --nostream

echo ""
echo "========================================="
echo "✅ Cloud Agent started successfully!"
echo "========================================="
echo ""
echo "Monitor logs:"
echo "  pm2 logs                    # All logs (live)"
echo "  pm2 logs cloud_orchestrator # Specific process"
echo "  pm2 logs --lines 50         # Last 50 lines"
echo ""
echo "Manage processes:"
echo "  pm2 list                    # List all processes"
echo "  pm2 restart all             # Restart all"
echo "  pm2 stop all                # Stop all"
echo "  pm2 delete all              # Delete all"
echo ""
echo "Enable startup on boot:"
echo "  pm2 startup systemd         # Generate startup script"
echo "  pm2 save                    # Save current process list"
echo ""
