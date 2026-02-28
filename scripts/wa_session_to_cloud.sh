#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# WhatsApp Session Transfer: Local → Oracle Cloud VM
# ──────────────────────────────────────────────────────────────────────────────
#
# Why this exists:
#   WhatsApp rejects pairing from cloud/data-center IPs (Oracle, AWS, etc).
#   Local auth works fine on your residential IP. This script:
#     1. Authenticates WhatsApp locally (wa_local_setup.py)
#     2. Copies the session directory to the Oracle Cloud VM via SCP
#     3. Restarts whatsapp_watcher on the cloud VM via SSH
#
# Usage:
#   cd /tmp
#   bash "/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee/scripts/wa_session_to_cloud.sh"
#
# Requirements:
#   - SSH key at ~/.ssh/ssh-key-2026-02-17.key
#   - Oracle VM accessible at 129.151.151.212
#   - Python venv with Playwright installed
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ROOT="/mnt/d/gov ai code/QUATER 4 part 2/hacakthon/personal-ai-employee"
SSH_KEY="$HOME/.ssh/ssh-key-2026-02-17.key"
CLOUD_USER="ubuntu"
CLOUD_HOST="129.151.151.212"
LOCAL_SESSION="$HOME/.whatsapp_session_dir"
CLOUD_SESSION="/home/ubuntu/.whatsapp_session_dir"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"

# ── Colors ────────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  WhatsApp Session Transfer: Local → Oracle Cloud            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Pre-flight checks ────────────────────────────────────────────────────────
echo -e "${YELLOW}[1/5] Pre-flight checks...${NC}"

if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}ERROR: SSH key not found at $SSH_KEY${NC}"
    exit 1
fi
echo "  SSH key: OK"

if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}ERROR: Python venv not found at $VENV_PYTHON${NC}"
    echo "  Run: cd \"$PROJECT_ROOT\" && python -m venv venv && venv/bin/pip install playwright"
    exit 1
fi
echo "  Python venv: OK"

# Test SSH connectivity (5s timeout)
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o StrictHostKeyChecking=no "$CLOUD_USER@$CLOUD_HOST" "echo ok" >/dev/null 2>&1; then
    echo -e "${RED}ERROR: Cannot SSH to $CLOUD_HOST${NC}"
    echo "  Check: ssh -i $SSH_KEY $CLOUD_USER@$CLOUD_HOST"
    exit 1
fi
echo "  SSH to cloud: OK"
echo ""

# ── Step 1: Check if already authenticated locally ───────────────────────────
echo -e "${YELLOW}[2/5] Checking local WhatsApp session...${NC}"

# We must be in /tmp for WSL2 Playwright compatibility
cd /tmp

if [ -d "$LOCAL_SESSION" ]; then
    echo "  Found existing session at $LOCAL_SESSION"
    echo "  Testing if session is still valid..."

    # Quick check: run a test script that just opens WA and checks login state
    AUTH_CHECK=$("$VENV_PYTHON" -c "
import os, sys
os.chdir('/tmp')
from playwright.sync_api import sync_playwright
session = '$LOCAL_SESSION'
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=session, headless=True,
        args=['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--disable-gpu'],
        viewport={'width':1920,'height':1080},
    )
    page = ctx.new_page()
    page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=40000)
    import time; time.sleep(20)
    logged_in = page.locator('div[aria-label=\"Chat list\"],#pane-side').count() > 0
    ctx.close()
    print('LOGGED_IN' if logged_in else 'NOT_LOGGED_IN')
" 2>/dev/null || echo "ERROR")

    if [ "$AUTH_CHECK" = "LOGGED_IN" ]; then
        echo -e "  ${GREEN}Session is VALID! Skipping re-auth.${NC}"
    else
        echo "  Session expired or invalid. Will re-authenticate."
        rm -rf "$LOCAL_SESSION"
    fi
else
    echo "  No existing session. Will authenticate fresh."
fi

# ── Step 2: Authenticate locally if needed ────────────────────────────────────
if [ ! -d "$LOCAL_SESSION" ] || [ "$AUTH_CHECK" != "LOGGED_IN" ]; then
    echo ""
    echo -e "${YELLOW}[3/5] Authenticating WhatsApp locally...${NC}"
    echo "  Running wa_local_setup.py (will show pairing code)..."
    echo "  Enter the code on your phone when prompted."
    echo ""

    "$VENV_PYTHON" "$PROJECT_ROOT/scripts/wa_local_setup.py"

    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Local authentication failed.${NC}"
        echo "  Try running manually: cd /tmp && $VENV_PYTHON $PROJECT_ROOT/scripts/wa_local_setup.py"
        exit 1
    fi
    echo -e "  ${GREEN}Local authentication successful!${NC}"
else
    echo ""
    echo -e "${YELLOW}[3/5] Skipping auth (session already valid)${NC}"
fi

# ── Step 3: Stop whatsapp_watcher on cloud ────────────────────────────────────
echo ""
echo -e "${YELLOW}[4/5] Preparing cloud VM...${NC}"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$CLOUD_USER@$CLOUD_HOST" bash -s <<'REMOTE_STOP'
echo "  Stopping whatsapp_watcher..."
pm2 stop whatsapp_watcher 2>/dev/null || true
echo "  Cleaning old session..."
rm -rf /home/ubuntu/.whatsapp_session_dir
echo "  Cloud ready for session transfer."
REMOTE_STOP

# ── Step 4: Transfer session ──────────────────────────────────────────────────
echo ""
echo -e "${YELLOW}[5/5] Transferring session to cloud...${NC}"

# SCP the entire session directory
scp -r -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    "$LOCAL_SESSION" \
    "$CLOUD_USER@$CLOUD_HOST:$CLOUD_SESSION"

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: SCP transfer failed.${NC}"
    exit 1
fi
echo -e "  ${GREEN}Session transferred!${NC}"

# ── Step 5: Start whatsapp_watcher on cloud ───────────────────────────────────
echo ""
echo -e "${YELLOW}Starting whatsapp_watcher on cloud...${NC}"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$CLOUD_USER@$CLOUD_HOST" bash -s <<'REMOTE_START'
# Clean Chrome lock files (prevents "profile in use" errors)
rm -f /home/ubuntu/.whatsapp_session_dir/SingletonLock 2>/dev/null
rm -f /home/ubuntu/.whatsapp_session_dir/SingletonCookie 2>/dev/null
rm -f /home/ubuntu/.whatsapp_session_dir/SingletonSocket 2>/dev/null

# Remove architecture-specific caches (x86 → ARM mismatch is fine for data, not code)
rm -rf /home/ubuntu/.whatsapp_session_dir/ShaderCache 2>/dev/null
rm -rf /home/ubuntu/.whatsapp_session_dir/GrShaderCache 2>/dev/null
rm -rf /home/ubuntu/.whatsapp_session_dir/GPUCache 2>/dev/null
rm -rf /home/ubuntu/.whatsapp_session_dir/Code\ Cache 2>/dev/null

echo "  Session cleanup done (removed x86 caches, Chrome locks)."
echo "  Starting whatsapp_watcher..."
cd /opt/personal-ai-employee
pm2 start ecosystem.config.js --only whatsapp_watcher
sleep 3
pm2 list
echo ""
echo "  Checking logs (last 10 lines)..."
pm2 logs whatsapp_watcher --lines 10 --nostream
REMOTE_START

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗"
echo -e "║  ✅ WhatsApp session transferred to Oracle Cloud!            ║"
echo -e "║                                                              ║"
echo -e "║  The watcher should now be running with your local session.  ║"
echo -e "║  Check: ssh -i $SSH_KEY $CLOUD_USER@$CLOUD_HOST 'pm2 logs'  ║"
echo -e "╚══════════════════════════════════════════════════════════════╝${NC}"
