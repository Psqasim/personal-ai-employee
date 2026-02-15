#!/usr/bin/env python3
"""
WhatsApp QR Setup - One-time authentication

Launches Playwright browser in headed mode, displays WhatsApp Web QR code,
waits for scan, and saves session for future use.

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
Tasks: T035 (WhatsApp QR setup script)
"""

import os
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("[ERROR] Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


def authenticate_whatsapp_qr():
    """
    Authenticate WhatsApp Web via QR code scan.

    Returns:
        True if successful, False otherwise
    """
    session_path = os.getenv("WHATSAPP_SESSION_PATH", str(Path.home() / ".whatsapp_session"))

    print(f"[WhatsApp Setup] Starting authentication...")
    print(f"[WhatsApp Setup] Session will be saved to: {session_path}")

    try:
        with sync_playwright() as p:
            print("[WhatsApp Setup] Launching Chromium browser...")
            browser = p.chromium.launch(headless=False)  # Headed mode for QR scan
            context = browser.new_context()
            page = context.new_page()

            print("[WhatsApp Setup] Opening WhatsApp Web...")
            page.goto('https://web.whatsapp.com')

            # Wait for QR code
            print("[WhatsApp Setup] Waiting for QR code...")
            qr_selector = 'canvas[aria-label="Scan this QR code to link a device!"]'

            try:
                qr_canvas = page.wait_for_selector(qr_selector, timeout=10000)
                print("\n" + "="*60)
                print("  QR CODE DISPLAYED IN BROWSER")
                print("="*60)
                print("\nScan QR code with your WhatsApp mobile app:")
                print("  1. Open WhatsApp on your phone")
                print("  2. Tap Settings (⚙️) → Linked Devices")
                print("  3. Tap 'Link a Device'")
                print("  4. Scan the QR code shown in the browser")
                print("\nWaiting for authentication (timeout: 60 seconds)...")
                print("="*60 + "\n")

            except PlaywrightTimeout:
                # QR code didn't appear - might already be authenticated
                print("[WhatsApp Setup] No QR code detected - checking if already authenticated...")

            # Wait for authentication (QR code disappears, conversation panel appears)
            conversation_panel_selector = 'div[data-testid="conversation-panel-wrapper"]'

            try:
                page.wait_for_selector(conversation_panel_selector, timeout=60000)
                print("\n[WhatsApp Setup] ✓ Authenticated successfully!")

            except PlaywrightTimeout:
                print("\n[WhatsApp Setup] ✗ Authentication timeout (60s)")
                print("[WhatsApp Setup] QR code was not scanned in time")
                browser.close()
                return False

            # Save session
            print(f"[WhatsApp Setup] Saving session to {session_path}...")
            context.storage_state(path=session_path)

            print("[WhatsApp Setup] ✓ Session saved successfully!")
            print(f"[WhatsApp Setup] Session file: {session_path}")

            # Close browser
            browser.close()

            print("\n" + "="*60)
            print("  WHATSAPP AUTHENTICATION COMPLETE")
            print("="*60)
            print("\nYour WhatsApp session has been saved.")
            print("You can now run the WhatsApp watcher:")
            print("  python scripts/whatsapp_watcher.py")
            print("\nSession persistence:")
            print("  - Session typically lasts several weeks")
            print("  - Re-run this script if session expires")
            print("  - Session file location:", session_path)
            print("="*60 + "\n")

            return True

    except Exception as e:
        print(f"\n[WhatsApp Setup] ✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure Playwright is installed: pip install playwright")
        print("  2. Ensure Chromium browser is installed: playwright install chromium")
        print("  3. Check system requirements (Linux/macOS/Windows 10+)")
        print("  4. On WSL2, install dependencies: sudo apt-get install -y libgbm1 libasound2")
        return False


if __name__ == "__main__":
    success = authenticate_whatsapp_qr()
    sys.exit(0 if success else 1)
