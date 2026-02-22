#!/bin/bash
# Deploy Next.js Dashboard to Oracle Cloud VM
# Usage: bash deployment/oracle/deploy_dashboard.sh
# Strategy: Build locally (fast) → rsync .next/ → restart PM2

set -e

ORACLE_USER="ubuntu"
ORACLE_IP="129.151.151.212"
ORACLE_KEY="$HOME/.ssh/ssh-key-2026-02-17.key"
DASHBOARD_DIR="/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee/nextjs_dashboard"
REMOTE_DIR="/opt/personal-ai-employee"

echo "========================================"
echo "  Deploying Next.js Dashboard"
echo "  Target: $ORACLE_USER@$ORACLE_IP"
echo "========================================"

echo ""
echo ">>> Step 1: Pull latest code on Oracle VM..."
ssh -i "$ORACLE_KEY" "$ORACLE_USER@$ORACLE_IP" "cd $REMOTE_DIR && git fetch origin && git reset --hard origin/main"
echo "✅ Code updated on VM"

echo ""
echo ">>> Step 2: Install dependencies locally (if needed)..."
cd "$DASHBOARD_DIR"
npm install --silent
echo "✅ Dependencies ready"

echo ""
echo ">>> Step 3: Build locally..."
npm run build
echo "✅ Build complete"

echo ""
echo ">>> Step 4: Rsync .next/ to Oracle VM..."
rsync -az --delete \
  -e "ssh -i $ORACLE_KEY" \
  "$DASHBOARD_DIR/.next/" \
  "$ORACLE_USER@$ORACLE_IP:$REMOTE_DIR/nextjs_dashboard/.next/"
echo "✅ Build files synced"

echo ""
echo ">>> Step 5: Restart PM2 on Oracle VM..."
ssh -i "$ORACLE_KEY" "$ORACLE_USER@$ORACLE_IP" "pm2 restart nextjs_dashboard && pm2 save"
echo "✅ PM2 restarted"

echo ""
echo ">>> Verifying..."
sleep 3
HTTP=$(ssh -i "$ORACLE_KEY" "$ORACLE_USER@$ORACLE_IP" "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/login")
echo "Internal HTTP: $HTTP"

echo ""
echo "========================================"
echo "  ✅ Dashboard deployed!"
echo "  Access: http://129.151.151.212:3000"
echo "========================================"
