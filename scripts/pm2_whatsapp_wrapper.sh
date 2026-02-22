#!/bin/bash
# PM2 wrapper for WhatsApp watcher (Python)
# Runs the whatsapp_watcher.py using the project venv

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Load .env
if [ -f "$PROJECT_ROOT/.env" ]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" != *=* ]] && continue
    key="${line%%=*}"; key="${key// /}"
    value="${line#*=}"; value="${value%%#*}"
    value="${value%"${value##*[![:space:]]}"}"
    [[ -z "$key" || "$key" =~ [[:space:]] ]] && continue
    export "$key=$value"
  done < "$PROJECT_ROOT/.env"
fi

export PYTHONPATH="$PROJECT_ROOT"
export PYTHONUNBUFFERED=1

# Map CLAUDE_API_KEY → ANTHROPIC_API_KEY (SDK standard name)
if [ -n "$CLAUDE_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
  export ANTHROPIC_API_KEY="$CLAUDE_API_KEY"
fi

export WHATSAPP_SESSION_PATH="${HOME}/.whatsapp_session_dir"
export WHATSAPP_POLL_INTERVAL="${WHATSAPP_POLL_INTERVAL:-30}"
export CHATS_TO_CHECK="${CHATS_TO_CHECK:-5}"

# Use venv python (linux path for WSL2)
PYTHON="$PROJECT_ROOT/venv/bin/python3"
if [ ! -f "$PYTHON" ]; then
  PYTHON="$PROJECT_ROOT/venv/bin/python"
fi

exec "$PYTHON" -u "$PROJECT_ROOT/scripts/whatsapp_watcher.py"
