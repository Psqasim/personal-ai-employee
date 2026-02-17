#!/bin/bash
# PM2 wrapper: safely loads .env then runs local agent orchestrator
# PM2 calls this script directly — do NOT invoke manually.
#
# Uses Python-style .env parsing (handles comments, spaces, inline comments)
# instead of `source .env` which breaks on dashes in comments.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Export each non-comment, non-blank line from .env
# Strips inline comments and handles values with spaces safely
if [ -f "$PROJECT_ROOT/.env" ]; then
  while IFS= read -r line; do
    # Skip blank lines and comment lines
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    # Must contain = sign
    [[ "$line" != *=* ]] && continue
    # Extract key (everything before first =)
    key="${line%%=*}"
    key="${key// /}"   # trim spaces from key
    # Extract value (everything after first =), strip inline comments
    value="${line#*=}"
    value="${value%%#*}"  # remove inline comment
    value="${value%"${value##*[![:space:]]}"}"  # rtrim whitespace
    # Skip if key is empty or has spaces (not a valid var name)
    [[ -z "$key" || "$key" =~ [[:space:]] ]] && continue
    export "$key=$value"
  done < "$PROJECT_ROOT/.env"
fi

export PYTHONPATH="$PROJECT_ROOT"

exec "$PROJECT_ROOT/venv/bin/python3" -u "$PROJECT_ROOT/local_agent/src/orchestrator.py"
