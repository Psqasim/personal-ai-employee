#!/usr/bin/env python3
"""
Manual CEO Briefing trigger.
Run: python scripts/generate_ceo_briefing.py

Generates briefing immediately, updates Dashboard.md, sends WhatsApp.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ceo_briefing import generate_briefing

vault_path = os.path.abspath(
    os.getenv("VAULT_PATH", str(Path(__file__).parent.parent / "vault"))
)

print(f"[generate_ceo_briefing] Generating briefing for vault: {vault_path}")
path = generate_briefing(vault_path, send_wa=True)
print(f"[generate_ceo_briefing] ✅ Report: {path}")
