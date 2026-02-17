#!/bin/bash
# Deploy latest code to Oracle Cloud VM
# Usage: bash deploy_to_oracle.sh

set -e

VM_IP="129.151.151.212"
SSH_KEY="$HOME/.ssh/ssh-key-2026-02-17.key"
VM_USER="ubuntu"
BRANCH="003-platinum-tier"

echo "🚀 Deploying to Oracle VM ($VM_IP)..."

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$VM_USER@$VM_IP" << 'ENDSSH'
set -e
cd /opt/personal-ai-employee

echo "=== Git Pull ==="
git fetch origin 003-platinum-tier
git reset --hard origin/003-platinum-tier
echo "✅ Code updated"

echo ""
echo "=== Install Dependencies ==="
source venv/bin/activate
pip install -r requirements.txt --quiet
echo "✅ Dependencies OK"

echo ""
echo "=== Reload Environment ==="
export $(cat .env.cloud | grep -v '^#' | xargs)
echo "TIER=$TIER"
echo "VAULT_PATH=$VAULT_PATH"

echo ""
echo "=== PM2 Restart ==="
pm2 restart all --update-env
sleep 3

echo ""
echo "=== PM2 Status ==="
pm2 list

echo ""
echo "=== Recent Logs (last 30 lines) ==="
pm2 logs --lines 30 --nostream

echo ""
echo "✅ Deployment complete!"
ENDSSH
