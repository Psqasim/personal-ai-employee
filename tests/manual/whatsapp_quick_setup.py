#!/usr/bin/env python3
"""Quick WhatsApp session saver - waits for user confirmation"""
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

session_path = os.getenv("WHATSAPP_SESSION_PATH", str(Path.home() / ".whatsapp_session"))

print("=" * 70)
print("  WHATSAPP SESSION SAVER")
print("=" * 70)
print()
print(f"Session will be saved to: {session_path}")
print()

with sync_playwright() as p:
    print("Opening browser...")
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    print("Loading WhatsApp Web...")
    page.goto('https://web.whatsapp.com')
    
    print()
    print("=" * 70)
    print("  INSTRUCTIONS:")
    print("=" * 70)
    print()
    print("1. If you see a QR code → Scan it with your phone")
    print("2. Wait for WhatsApp to load completely")
    print("3. You should see your chats/conversations")
    print("4. When fully loaded, type 'done' in terminal and press Enter")
    print()
    print("=" * 70)
    print()
    
    # Wait for user confirmation
    input("Press Enter when WhatsApp is fully loaded and you see your chats...")
    
    print()
    print("Saving session...")
    context.storage_state(path=session_path)
    
    print(f"✅ Session saved to: {session_path}")
    print()
    
    browser.close()
    
    print("=" * 70)
    print("  ✅ SETUP COMPLETE!")
    print("=" * 70)
    print()
    print("You can now use WhatsApp automation!")
