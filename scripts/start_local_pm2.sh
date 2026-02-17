#!/bin/bash
# Start Local Agent as PM2 background service
#
# Run this once from the project root to launch the local approval handler.
# PM2 will keep it running and auto-restart on crash.
#
# Usage:
#   bash scripts/start_local_pm2.sh
#
# After first run, agent starts automatically on every PC boot
# (once you also run scripts/setup_local_startup.sh).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo ""
echo "======================================"
echo "  Personal AI Employee — Local Agent  "
echo "======================================"
echo "Project: $PROJECT_ROOT"
echo ""

# ---- Check prerequisites ----
if ! command -v pm2 &>/dev/null; then
  echo "⚠  PM2 not found. Installing globally..."
  npm install -g pm2
fi

if [ ! -f "$PROJECT_ROOT/.env" ]; then
  echo "✗ ERROR: .env not found at $PROJECT_ROOT/.env"
  echo "  Create it with VAULT_PATH, SMTP_USER, SMTP_PASSWORD, CLAUDE_API_KEY"
  exit 1
fi

if [ ! -f "$PROJECT_ROOT/venv/bin/python3" ]; then
  echo "✗ ERROR: Python venv not found at $PROJECT_ROOT/venv/"
  echo "  Create it with: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# ---- Create vault log dirs (PM2 writes logs here) ----
mkdir -p "$PROJECT_ROOT/vault/Logs/Local"
mkdir -p "$PROJECT_ROOT/vault/Logs/MCP_Actions"
mkdir -p "$PROJECT_ROOT/vault/Approved/Email"
mkdir -p "$PROJECT_ROOT/vault/Done"
mkdir -p "$PROJECT_ROOT/vault/Failed"
echo "✓ Vault directories ready"

# ---- Stop existing instance if running ----
if pm2 list 2>/dev/null | grep -q "local_approval_handler"; then
  echo "↻ Stopping existing local_approval_handler..."
  pm2 delete local_approval_handler 2>/dev/null || true
fi

# ---- Start via PM2 ----
echo ""
echo "Starting PM2 process..."
pm2 start scripts/run_local_agent.sh \
  --name local_approval_handler \
  --interpreter bash \
  --max-restarts 10 \
  --restart-delay 5000

# ---- Save process list (so pm2 resurrect restores it) ----
pm2 save
echo ""
echo "✅ Local Agent is running!"
echo ""

# ---- Show status ----
pm2 list

echo ""
echo "Useful commands:"
echo "  pm2 logs local_approval_handler   — live logs"
echo "  pm2 stop local_approval_handler   — stop"
echo "  pm2 restart local_approval_handler — restart"
echo ""
echo "Open dashboard:"
echo "  cd nextjs_dashboard && npm run dev"
echo "  → http://localhost:3000"
echo ""
echo "To auto-start on boot, run once:"
echo "  bash scripts/setup_local_startup.sh"
