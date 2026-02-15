#!/usr/bin/env python3
"""
WhatsApp QR Setup - Terminal Version (WSL2 Compatible)

Shows QR code in terminal for scanning.

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-15
"""

import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import time

# Try to import qrcode for terminal display
try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False
    print("⚠️  Installing qrcode library...")
    os.system("pip install qrcode[pil] --quiet")
    import qrcode
    HAS_QRCODE = True

session_path = os.getenv("WHATSAPP_SESSION_PATH", str(Path.home() / ".whatsapp_session"))

print("=" * 80)
print("  WHATSAPP QR SETUP - TERMINAL VERSION")
print("=" * 80)
print()
print(f"Session will be saved to: {session_path}")
print()

print("Starting browser (headless mode)...")
print()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    print("Loading WhatsApp Web...")
    page.goto('https://web.whatsapp.com', wait_until='networkidle')

    print("Waiting for QR code...")
    time.sleep(3)

    # Try to extract QR code data
    try:
        # Wait for QR code canvas
        qr_selector = 'canvas[aria-label="Scan this QR code to link a device!"]'
        page.wait_for_selector(qr_selector, timeout=10000)

        # Get QR code data URL
        qr_data = page.evaluate('''() => {
            const canvas = document.querySelector('canvas[aria-label="Scan this QR code to link a device!"]');
            return canvas ? canvas.toDataURL() : null;
        }''')

        if qr_data:
            print("=" * 80)
            print("  QR CODE DETECTED!")
            print("=" * 80)
            print()

            # Save QR code as image
            import base64
            qr_image_path = Path("/tmp/whatsapp_qr.png")

            # Extract base64 data
            base64_data = qr_data.split(',')[1]
            qr_image_path.write_bytes(base64.b64decode(base64_data))

            print(f"✅ QR code saved to: {qr_image_path}")
            print()
            print("📱 SCAN INSTRUCTIONS:")
            print("   1. Open WhatsApp on your phone")
            print("   2. Go to: Menu (⋮) → Linked Devices → Link a Device")
            print("   3. Scan the QR code image at: /tmp/whatsapp_qr.png")
            print()
            print("   OR if you have Windows access:")
            print(f"   Open: {qr_image_path}")
            print()

            # Try to display in terminal (if qrcode installed)
            if HAS_QRCODE:
                print("🔲 QR CODE IN TERMINAL:")
                print("=" * 80)

                # Generate ASCII QR code
                # Note: We can't easily convert the canvas QR to ASCII
                # But we can show the image path
                print(f"   Image saved at: {qr_image_path}")
                print(f"   View with: eog {qr_image_path} (on Linux)")
                print(f"   Or transfer to Windows and open with image viewer")
                print()

            print("=" * 80)
            print()

            # Wait for authentication
            print("⏳ Waiting for you to scan the QR code...")
            print("   (This will timeout in 60 seconds if not scanned)")
            print()

            # Wait for WhatsApp to load (indicating successful scan)
            try:
                page.wait_for_selector('div[data-testid="chat-list"]', timeout=60000)
                print("✅ WhatsApp authenticated!")
                print()

                # Save session
                print("Saving session...")
                context.storage_state(path=session_path)

                print(f"✅ Session saved to: {session_path}")
                print()
                print("🎉 WhatsApp setup complete!")
                print()

            except Exception as e:
                print(f"⏱️  Timeout waiting for scan: {e}")
                print()
                print("Please try again and scan the QR code faster.")
                print()
        else:
            print("❌ Could not extract QR code")
            print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("Alternative: Run this script on Windows directly (not WSL)")
        print("   python tests/manual/whatsapp_quick_setup.py")
        print()

    browser.close()

print("=" * 80)
print("Setup script finished")
print("=" * 80)
