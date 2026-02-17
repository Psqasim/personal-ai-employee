#!/usr/bin/env python3
"""
WhatsApp Session Setup - Scan QR code to authenticate WhatsApp Web.

Run this ONCE to create/refresh the session file.
After scanning, the session is saved and the local agent can send
WhatsApp messages headlessly.

Usage:
    python3 scripts/setup_whatsapp_session.py

Requirements:
    - Run with headed display (not in SSH without X11)
    - Scan QR code with your WhatsApp phone → Linked Devices → Link a Device
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env
env_file = project_root / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.split("#")[0].strip()
            if key:
                os.environ.setdefault(key, value)

session_path = os.getenv("WHATSAPP_SESSION_PATH", "/home/ps_qasim/.whatsapp_session")
print(f"\n{'='*50}")
print("  WhatsApp Session Setup")
print(f"{'='*50}")
print(f"Session will be saved to: {session_path}")
print()

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright not installed.")
    print("Run: pip install playwright && playwright install chromium")
    sys.exit(1)

print("Opening WhatsApp Web — a browser window will appear.")
print("Scan the QR code with your phone:")
print("  WhatsApp → Linked Devices → Link a Device\n")

with sync_playwright() as p:
    # Must be headed (visible) for QR scan
    browser = p.chromium.launch(headless=False, slow_mo=500)
    context = browser.new_context()
    page = context.new_page()

    print("Loading WhatsApp Web...")
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    print("Waiting for QR code... (scan it now with your phone)")
    print("You have 90 seconds.")

    try:
        # Wait for chat panel = logged in
        page.wait_for_selector(
            'div[data-testid="conversation-panel-wrapper"]',
            timeout=90000
        )
        print("\n✅ Authenticated! Saving session...")
        context.storage_state(path=session_path)
        print(f"✅ Session saved to: {session_path}")
        print("\nYou can now send WhatsApp messages via the dashboard.")
        print("Run: pm2 restart local_approval_handler")

    except Exception:
        print("\n❌ Timed out or authentication failed.")
        print("Try again and scan the QR code faster.")

    browser.close()
