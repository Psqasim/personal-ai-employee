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

# Use launch_persistent_context — preserves IndexedDB, ServiceWorkers, cookies.
# storage_state JSON only saves cookies/localStorage, which is not enough for
# WhatsApp's end-to-end encryption keys stored in IndexedDB.
print(f"Session directory: {session_path}")

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=session_path,
        headless=False,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
        slow_mo=300,
        viewport={"width": 1280, "height": 800},
    )
    page = context.new_page()

    print("Loading WhatsApp Web...")
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded")

    print("Waiting for QR code... (scan it now with your phone)")
    print("You have 120 seconds.\n")

    try:
        logged_in = False
        selectors_to_try = [
            'div[aria-label="Chat list"]',
            'div[data-testid="chat-list"]',
            '#pane-side',
        ]
        for sel in selectors_to_try:
            try:
                page.wait_for_selector(sel, timeout=120000)
                logged_in = True
                print(f"\n✅ Logged in detected via: {sel}")
                break
            except Exception:
                print(f"   selector {sel!r} not found, trying next...")

        if logged_in:
            import time
            time.sleep(2)  # Let page settle so all data is written to user_data_dir
            print(f"✅ Session saved to directory: {session_path}")
            print("\nYou can now send WhatsApp messages via the dashboard.")
            print("Run: pm2 restart local_approval_handler")
        else:
            print("\n❌ Could not detect logged-in state. Try again.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Try again.")

    context.close()
