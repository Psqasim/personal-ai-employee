#!/usr/bin/env python3
"""Direct test of WhatsApp MCP send_message function"""
from dotenv import load_dotenv
load_dotenv()

import os
import sys
from pathlib import Path

# Add mcp_servers to path
sys.path.insert(0, str(Path(__file__).parent / "mcp_servers" / "whatsapp_mcp"))

from server import send_message

print("=" * 80)
print("  WHATSAPP MCP DIRECT TEST")
print("=" * 80)
print()
print(f"Session: {os.getenv('WHATSAPP_SESSION_PATH')}")
print()
print("Testing send_message function directly (no MCP client wrapper)")
print("This will use NON-HEADLESS mode so we can see what's happening")
print()
print("=" * 80)
print()

# Modify the server.py temporarily to use headless=False
import mcp_servers.whatsapp_mcp.server as whatsapp_server

# Patch the send_message to use headless=False
original_code = '''browser = p.chromium.launch(headless=True)'''
patched_code = '''browser = p.chromium.launch(headless=False)'''

server_file = Path(__file__).parent / "mcp_servers" / "whatsapp_mcp" / "server.py"
server_content = server_file.read_text()

if original_code in server_content:
    print("⚠️  Temporarily patching server.py to use headless=False for debugging")
    patched_content = server_content.replace(original_code, patched_code)
    server_file.write_text(patched_content)
    print("✅ Patched - browser will be visible")
    print()

    # Reload module
    import importlib
    importlib.reload(sys.modules['server'])
    from server import send_message

try:
    print("Calling send_message...")
    print("Contact: john_smith_001")
    print("Message: Test message from AI - WhatsApp integration working!")
    print()

    result = send_message(
        chat_id="john_smith_001",
        message="Test message from AI - WhatsApp integration working!"
    )

    print()
    print("=" * 80)
    print("✅ SUCCESS!")
    print(f"Message ID: {result['message_id']}")
    print(f"Sent at: {result['sent_at']}")
    print("=" * 80)

except Exception as e:
    print()
    print("=" * 80)
    print(f"❌ ERROR: {e}")
    print("=" * 80)
    import traceback
    traceback.print_exc()

finally:
    # Restore original
    if patched_code in server_content.replace(original_code, patched_code):
        print()
        print("Restoring server.py to headless=True...")
        server_file.write_text(server_content)
        print("✅ Restored")
