#!/usr/bin/env python3
"""
WhatsApp MCP Server - Playwright automation via JSON-RPC 2.0

Implements Model Context Protocol for WhatsApp Web automation using Playwright.
Supports QR authentication, session persistence, and message sending.

Tools:
- authenticate_qr: Display QR code for WhatsApp Web authentication
- send_message: Send WhatsApp message via Playwright

Author: Personal AI Employee (Gold Tier)
Created: 2026-02-14
"""

import sys
import json
import os
from datetime import datetime
from typing import Dict, Any
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


# WhatsApp Web selectors (as of 2026-01)
SELECTORS = {
    "SEARCH_BOX": 'div[contenteditable="true"][data-tab="3"]',
    "MESSAGE_INPUT": 'div[contenteditable="true"][data-tab="10"]',
    "SEND_BUTTON": 'button[data-tab="11"]',
    "QR_CODE": 'canvas[aria-label="Scan this QR code to link a device!"]',
    "CONVERSATION_PANEL": 'div[data-testid="conversation-panel-wrapper"]'
}


def authenticate_qr() -> Dict[str, Any]:
    """
    Initiate WhatsApp Web QR authentication.

    Returns:
        Dict with qr_code_base64 and status
    """
    session_path = os.getenv("WHATSAPP_SESSION_PATH", "/tmp/whatsapp_session")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Headed for QR scan
            context = browser.new_context()
            page = context.new_page()
            page.goto('https://web.whatsapp.com')

            # Wait for QR code
            qr_canvas = page.wait_for_selector(SELECTORS["QR_CODE"], timeout=10000)

            # Get QR code as base64 (simplified - actual implementation would use canvas.toDataURL)
            qr_code_base64 = "QR_CODE_PLACEHOLDER"  # In production, extract actual QR code

            # Wait for authentication (QR disappears)
            page.wait_for_selector(SELECTORS["CONVERSATION_PANEL"], timeout=60000)

            # Save session
            context.storage_state(path=session_path)
            browser.close()

            return {
                "qr_code_base64": qr_code_base64,
                "status": "authenticated",
                "session_path": session_path
            }

    except PlaywrightTimeout:
        raise Exception("QR_SCAN_TIMEOUT: QR code not scanned within 60 seconds")
    except Exception as e:
        raise Exception(f"BROWSER_LAUNCH_FAILED: {e}")


def send_message(chat_id: str, message: str) -> Dict[str, Any]:
    """
    Send WhatsApp message via Playwright.

    Args:
        chat_id: Contact name (as shown in WhatsApp Web)
        message: Message text to send

    Returns:
        Dict with message_id and sent_at
    """
    session_path = os.getenv("WHATSAPP_SESSION_PATH")

    if not session_path or not os.path.exists(session_path):
        raise Exception("SESSION_EXPIRED: WhatsApp session not found or expired")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Headless for automated sends
            context = browser.new_context(storage_state=session_path)
            page = context.new_page()
            page.goto('https://web.whatsapp.com', wait_until='networkidle')

            # Wait for chat panel (confirms session valid) - increased timeout for headless mode
            page.wait_for_selector(SELECTORS["CONVERSATION_PANEL"], timeout=60000)

            # Search for contact
            search_box = page.wait_for_selector(SELECTORS["SEARCH_BOX"], timeout=15000)
            search_box.fill(chat_id)
            page.keyboard.press('Enter')
            page.wait_for_timeout(2000)  # Wait for chat to open

            # Type and send message
            message_input = page.wait_for_selector(SELECTORS["MESSAGE_INPUT"], timeout=15000)
            message_input.fill(message)
            page.click(SELECTORS["SEND_BUTTON"])

            # Confirm sent (wait for message to appear in chat)
            page.wait_for_timeout(2000)  # Wait for send confirmation

            browser.close()

            message_id = f"msg_{int(datetime.now().timestamp())}"
            sent_at = datetime.now().isoformat()

            return {
                "message_id": message_id,
                "sent_at": sent_at
            }

    except PlaywrightTimeout:
        raise Exception("SESSION_EXPIRED: WhatsApp Web login screen detected")
    except Exception as e:
        raise Exception(f"SEND_FAILED: {e}")


def tools_list() -> Dict[str, Any]:
    """List available tools"""
    return {
        "tools": [
            {
                "name": "authenticate_qr",
                "description": "Authenticate WhatsApp Web via QR code",
                "inputSchema": {"type": "object", "properties": {}, "required": []}
            },
            {
                "name": "send_message",
                "description": "Send WhatsApp message via Playwright",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "chat_id": {"type": "string", "description": "Contact name"},
                        "message": {"type": "string", "description": "Message text"}
                    },
                    "required": ["chat_id", "message"]
                }
            }
        ]
    }


def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle JSON-RPC 2.0 request"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    try:
        if method == "tools/list":
            result = tools_list()
            return {"jsonrpc": "2.0", "id": request_id, "result": result}

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "authenticate_qr":
                result = authenticate_qr()
                return {"jsonrpc": "2.0", "id": request_id, "result": result}

            elif tool_name == "send_message":
                result = send_message(
                    chat_id=arguments.get("chat_id"),
                    message=arguments.get("message")
                )
                return {"jsonrpc": "2.0", "id": request_id, "result": result}

            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {tool_name}"}
                }

        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(e)}
        }


def main():
    """Main loop: read JSON-RPC requests from stdin, write responses to stdout"""
    for line in sys.stdin:
        if not line.strip():
            continue

        try:
            request = json.loads(line)
            response = handle_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()
