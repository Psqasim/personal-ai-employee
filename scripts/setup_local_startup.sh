#!/bin/bash
# Configure Local Agent to start automatically on PC boot
#
# Run this ONCE after bash scripts/start_local_pm2.sh
#
# What it does:
#   1. Saves current PM2 process list
#   2. Generates a systemd startup hook (Linux/WSL) or launchd (macOS)
#   3. After reboot, PM2 auto-starts and restores all saved processes
#
# Usage:
#   bash scripts/setup_local_startup.sh

set -e

echo ""
echo "======================================"
echo "  Setup Local Agent Boot Auto-Start   "
echo "======================================"
echo ""

if ! command -v pm2 &>/dev/null; then
  echo "✗ PM2 not found. Run scripts/start_local_pm2.sh first."
  exit 1
fi

# Verify local_approval_handler is running
if ! pm2 list 2>/dev/null | grep -q "local_approval_handler"; then
  echo "✗ local_approval_handler is not running."
  echo "  Start it first: bash scripts/start_local_pm2.sh"
  exit 1
fi

echo "Current PM2 processes:"
pm2 list
echo ""

# Save current process list
pm2 save
echo "✓ Process list saved"

# Generate startup script
echo ""
echo "Generating startup hook..."
echo "(You may be prompted for sudo password)"
pm2 startup

echo ""
echo "✅ Done! Local Agent will auto-start on boot."
echo ""
echo "To verify after reboot:"
echo "  pm2 list   ← should show local_approval_handler online"
echo ""
echo "To undo auto-start:"
echo "  pm2 unstartup"
