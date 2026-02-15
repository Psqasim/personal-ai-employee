#!/usr/bin/env python3
"""Test WhatsApp auto-send via approval_watcher"""
from dotenv import load_dotenv
load_dotenv()  # Load .env file first

import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_skills.approval_watcher import process_approval

# Set vault path
os.environ["VAULT_PATH"] = str(Path(__file__).parent / "vault")

# Process the approved draft
draft_file = "vault/Approved/WhatsApp/TEST_WHATSAPP_FINAL.md"
draft_path = Path(__file__).parent / draft_file

print("=" * 80)
print("  WHATSAPP AUTO-SEND TEST")
print("=" * 80)
print()
print(f"Processing: {draft_path.name}")
print(f"Session: {os.getenv('WHATSAPP_SESSION_PATH')}")
print()
print("This will:")
print("1. Parse the approved draft")
print("2. Launch WhatsApp Web (headless)")
print("3. Find contact: john_smith_001")
print("4. Send message")
print("5. Move draft to vault/Done/")
print()
print("=" * 80)
print()

try:
    success = process_approval(str(draft_path), approval_type="whatsapp")
    print()
    print("=" * 80)
    if success:
        print("✅ WhatsApp message sent successfully!")
        print()
        print("Check:")
        print("1. WhatsApp on phone 0301082227 for new message")
        print("2. vault/Done/ for processed draft")
        print("3. vault/Logs/MCP_Actions/ for action log")
    else:
        print("❌ WhatsApp send failed")
        print()
        print("Check:")
        print("1. vault/Needs_Action/ for error details")
        print("2. vault/Logs/Error_Recovery/ for error log")
    print("=" * 80)
except Exception as e:
    print()
    print("=" * 80)
    print(f"❌ ERROR: {e}")
    print("=" * 80)
    import traceback
    traceback.print_exc()
