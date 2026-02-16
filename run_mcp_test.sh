#!/bin/bash
# Quick script to run MCP server tests

cd "$(dirname "$0")"
source venv/bin/activate
export PYTHONPATH="$PWD:$PYTHONPATH"
python3 tests/live/test_mcp_servers.py
