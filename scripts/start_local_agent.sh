#!/bin/bash
# Start Local Agent on LOCAL MACHINE (laptop/PC)
#
# The Local Agent:
#   - Polls vault/Approved/ every 30s
#   - Sends approved emails via Gmail SMTP
#   - Moves sent files to vault/Done/
#   - Logs actions to vault/Logs/Local/
#
# Run this script on your LOCAL machine (not Oracle VM).
# The Oracle VM runs only the Cloud Agent (drafts, no sending).
#
# Usage:
#   ./scripts/start_local_agent.sh
#   ./scripts/start_local_agent.sh --once   # run a single approval cycle and exit

set -e

# Resolve project root (directory this script lives in, parent)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "=== Personal AI Employee — Local Agent ==="
echo "Project root: $PROJECT_ROOT"

# ---- Activate virtual environment ----
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
    echo "✓ venv activated: $PROJECT_ROOT/venv"
elif [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "✓ .venv activated"
else
    echo "⚠ No venv found — using system Python"
fi

# ---- Load environment variables ----
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
    echo "✓ .env loaded"
else
    echo "✗ ERROR: .env not found at $PROJECT_ROOT/.env"
    echo "  Create it with: VAULT_PATH, SMTP_USER, SMTP_PASSWORD, CLAUDE_API_KEY"
    exit 1
fi

# ---- Validate required env vars ----
missing=()
[ -z "$VAULT_PATH" ]    && missing+=("VAULT_PATH")
[ -z "$SMTP_USER" ]     && missing+=("SMTP_USER")
[ -z "$SMTP_PASSWORD" ] && missing+=("SMTP_PASSWORD")

if [ ${#missing[@]} -gt 0 ]; then
    echo "✗ ERROR: Missing required env vars: ${missing[*]}"
    echo "  Set them in .env and retry."
    exit 1
fi

echo "✓ VAULT_PATH=$VAULT_PATH"
echo "✓ SMTP_USER=$SMTP_USER"

# ---- Ensure vault dirs exist ----
for dir in \
    "$VAULT_PATH/Approved/Email" \
    "$VAULT_PATH/Approved/WhatsApp" \
    "$VAULT_PATH/Approved/LinkedIn" \
    "$VAULT_PATH/Done" \
    "$VAULT_PATH/Failed" \
    "$VAULT_PATH/Logs/Local" \
    "$VAULT_PATH/Logs/MCP_Actions"; do
    mkdir -p "$dir"
done
echo "✓ Vault directories ready"

# ---- Run ----
if [ "$1" == "--once" ]; then
    echo ""
    echo "Running single approval cycle..."
    python -c "
import os, sys
sys.path.insert(0, '.')
from local_agent.src.orchestrator import LocalOrchestrator
orch = LocalOrchestrator()
orch.process_approvals()
print('Done.')
"
else
    echo ""
    echo "Starting Local Orchestrator (Ctrl+C to stop)..."
    python local_agent/src/orchestrator.py
fi
