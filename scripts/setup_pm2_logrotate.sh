#!/bin/bash
# FR-P047: PM2 Log Rotation Setup
# Run on both local PC and Oracle Cloud VM
#
# Usage:
#   bash scripts/setup_pm2_logrotate.sh
#
# Configures:
#   - Max log size: 10 MB
#   - Retain: 7 rotated files
#   - Compress: gzip old logs
#   - Date format in filenames

set -euo pipefail

echo "[pm2-logrotate] Installing pm2-logrotate module..."
pm2 install pm2-logrotate

echo "[pm2-logrotate] Configuring..."
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 7
pm2 set pm2-logrotate:compress true
pm2 set pm2-logrotate:dateFormat YYYY-MM-DD_HH-mm-ss
pm2 set pm2-logrotate:rotateModule true
pm2 set pm2-logrotate:workerInterval 3600   # check every hour
pm2 set pm2-logrotate:rotateInterval 0 0 * * 0  # Sunday midnight

echo "[pm2-logrotate] Saving PM2 config..."
pm2 save

echo "[pm2-logrotate] ✅ Done. Current settings:"
pm2 conf pm2-logrotate 2>/dev/null || true

echo ""
echo "Run this script on BOTH:"
echo "  1. Local PC  (WSL2): bash scripts/setup_pm2_logrotate.sh"
echo "  2. Oracle VM (SSH):  bash scripts/setup_pm2_logrotate.sh"
