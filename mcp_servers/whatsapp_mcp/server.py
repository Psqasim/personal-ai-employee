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
import fcntl
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Any
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── Headless detection ────────────────────────────────────────────────────────
# Use headless if explicitly set, OR if no DISPLAY (WSL2 without WSLg)
HEADLESS = (
    os.getenv("PLAYWRIGHT_HEADLESS", "").lower() in ("1", "true", "yes")
    or not os.getenv("DISPLAY")
)
_HEADLESS_ARGS = ["--disable-gpu", "--enable-unsafe-swiftshader", "--disable-setuid-sandbox"]
_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")

def _launch_ctx(p, session_path):
    """Launch persistent context with auto headless detection.
    --no-zygote is required to prevent SIGTRAP crash in WSL2/Linux environments.
    --window-size=1,1 is intentionally omitted — it causes Chrome to abort on WSL2.
    """
    args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--no-zygote",            # Prevents SIGTRAP crash in WSL2
        "--disable-crash-reporter",
        "--disable-background-networking",
    ]
    if HEADLESS:
        args += _HEADLESS_ARGS
    return p.chromium.launch_persistent_context(
        user_data_dir=session_path,
        headless=HEADLESS,
        args=args,
        user_agent=_UA,
        viewport={"width": 1280, "height": 800},
    )

# ── Shared browser lock (same file as whatsapp_watcher.py) ────────────────────
BROWSER_LOCK_FILE = "/tmp/whatsapp_browser.lock"

@contextmanager
def _browser_lock(timeout: int = 90):
    """Exclusive lock — prevents MCP server and watcher from opening Chrome simultaneously."""
    lock_f = open(BROWSER_LOCK_FILE, "w")
    deadline = time.time() + timeout
    try:
        while True:
            try:
                fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.time() > deadline:
                    lock_f.close()
                    raise TimeoutError("Browser lock timeout — watcher may be running")
                time.sleep(2)
        yield
    finally:
        try:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
        except Exception:
            pass
        lock_f.close()


# WhatsApp Web selectors (as of 2026-02)
SELECTORS = {
    # Login confirmation — chat list sidebar (matches setup_whatsapp_session.py)
    "LOGGED_IN": 'div[aria-label="Chat list"], #pane-side, div[data-testid="chat-list"]',
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

    # Session path must be a directory (launch_persistent_context userDataDir)
    if not session_path or not os.path.isdir(session_path):
        raise Exception("SESSION_EXPIRED: WhatsApp session directory not found — run setup_whatsapp_session.py")

    try:
        with _browser_lock(timeout=90):
            with sync_playwright() as p:
                # Use launch_persistent_context — preserves IndexedDB + ServiceWorkers
                # Auto-detects headless (WSL2 no-display) via _launch_ctx()
                context = _launch_ctx(p, session_path)
                page = context.new_page()

                # domcontentloaded fires fast; WhatsApp JS needs extra time to render UI
                page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(3000)  # Let WhatsApp JS initialize

                # Wait for logged-in state OR QR code
                try:
                    page.wait_for_selector(
                        f'{SELECTORS["LOGGED_IN"]}, {SELECTORS["QR_CODE"]}',
                        timeout=90000
                    )
                except PlaywrightTimeout:
                    raise Exception("LOAD_TIMEOUT: WhatsApp Web did not load within 90s")

                if page.locator(SELECTORS["QR_CODE"]).count() > 0:
                    raise Exception("SESSION_EXPIRED: QR code detected — re-run setup_whatsapp_session.py")

                # Search for contact
                search_box = page.wait_for_selector(SELECTORS["SEARCH_BOX"], timeout=15000)
                search_box.fill(chat_id)
                page.keyboard.press('Enter')
                page.wait_for_timeout(2000)  # Wait for chat to open

                # Type and send message
                message_input = page.wait_for_selector(SELECTORS["MESSAGE_INPUT"], timeout=15000)
                message_input.fill(message)
                page.click(SELECTORS["SEND_BUTTON"])

                # Wait for send confirmation
                page.wait_for_timeout(2000)

                context.close()  # persistent context — no separate browser object

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


def get_messages(limit: int = 10) -> Dict[str, Any]:
    """
    Read unread WhatsApp messages via Playwright (read-only, no reply).
    Uses ONE browser session to avoid Chrome user-data-dir lock conflicts.

    Returns:
        Dict with list of {sender, message, timestamp, is_unread}
    """
    session_path = os.getenv("WHATSAPP_SESSION_PATH")
    if not session_path or not os.path.isdir(session_path):
        raise Exception("SESSION_EXPIRED: WhatsApp session directory not found")

    messages = []
    try:
        with _browser_lock(timeout=90):
            with sync_playwright() as p:
                context = _launch_ctx(p, session_path)
                page = context.new_page()
                page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(4000)

                page.wait_for_selector(
                    f'{SELECTORS["LOGGED_IN"]}, {SELECTORS["QR_CODE"]}',
                    timeout=90000
                )
                if page.locator(SELECTORS["QR_CODE"]).count() > 0:
                    raise Exception("SESSION_EXPIRED: QR code detected")

                page.wait_for_timeout(2000)

                # Find unread chats via unread badge (multiple selector fallbacks)
                unread_badge_sel = (
                    '[data-testid="icon-unread-count"], '
                    'span[aria-label*="unread message"], '
                    'span[aria-label*="unread"]'
                )
                badges = page.locator(unread_badge_sel).all()

                for badge in badges[:limit]:
                    try:
                        # Navigate up to the chat list item and click it
                        chat_item = badge.locator('xpath=ancestor::div[@role="listitem" or @data-testid="cell-frame-container"][1]')
                        if chat_item.count() == 0:
                            chat_item = badge.locator('xpath=ancestor::div[contains(@class,"focusable-list-item")][1]')

                        # Get sender name from title span
                        sender = "Unknown"
                        title_el = page.locator(f'span[title]:near({badge}, 200)')
                        if title_el.count() > 0:
                            sender = title_el.first.get_attribute('title') or "Unknown"

                        # Click to open chat
                        badge.click()
                        page.wait_for_timeout(2000)

                        # Read last incoming message text
                        incoming = page.locator(
                            'div.message-in span.selectable-text, '
                            'div[data-testid="msg-container"] span.selectable-text'
                        ).all()

                        text_parts = []
                        for el in incoming[-3:]:
                            try:
                                t = el.inner_text().strip()
                                if t:
                                    text_parts.append(t)
                            except Exception:
                                pass

                        if text_parts:
                            messages.append({
                                "sender": sender,
                                "message": " | ".join(text_parts),
                                "timestamp": datetime.now().isoformat(),
                                "is_unread": True
                            })
                    except Exception:
                        continue

                context.close()
                return {"messages": messages, "count": len(messages)}

    except Exception as e:
        raise Exception(f"GET_MESSAGES_FAILED: {e}")


def process_inbox(replies: Dict[str, str]) -> Dict[str, Any]:
    """
    Read unread messages AND send replies in ONE browser session.
    This avoids Chrome user-data-dir lock conflicts from two separate
    browser opens (get_messages + send_message).

    Args:
        replies: {sender_name: reply_text} mapping

    Returns:
        Dict with sent list and failed list
    """
    session_path = os.getenv("WHATSAPP_SESSION_PATH")
    if not session_path or not os.path.isdir(session_path):
        raise Exception("SESSION_EXPIRED: WhatsApp session directory not found")

    sent = []
    failed = []
    messages = []

    try:
        with _browser_lock(timeout=90):
            with sync_playwright() as p:
                context = _launch_ctx(p, session_path)
                page = context.new_page()
                page.goto('https://web.whatsapp.com', wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(4000)

                page.wait_for_selector(
                    f'{SELECTORS["LOGGED_IN"]}, {SELECTORS["QR_CODE"]}',
                    timeout=90000
                )
                if page.locator(SELECTORS["QR_CODE"]).count() > 0:
                    raise Exception("SESSION_EXPIRED: QR code detected")

                page.wait_for_timeout(2000)

                # ── Step 1: Read all unread messages ─────────────────────
                unread_badge_sel = (
                    '[data-testid="icon-unread-count"], '
                    'span[aria-label*="unread message"], '
                    'span[aria-label*="unread"]'
                )
                badges = page.locator(unread_badge_sel).all()

                for badge in badges[:10]:
                    try:
                        sender = "Unknown"
                        title_el = page.locator(f'span[title]:near({badge}, 200)')
                        if title_el.count() > 0:
                            sender = title_el.first.get_attribute('title') or "Unknown"

                        badge.click()
                        page.wait_for_timeout(2000)

                        incoming = page.locator(
                            'div.message-in span.selectable-text, '
                            'div[data-testid="msg-container"] span.selectable-text'
                        ).all()
                        text_parts = []
                        for el in incoming[-3:]:
                            try:
                                t = el.inner_text().strip()
                                if t:
                                    text_parts.append(t)
                            except Exception:
                                pass

                        if text_parts:
                            messages.append({
                                "sender": sender,
                                "message": " | ".join(text_parts),
                                "timestamp": datetime.now().isoformat(),
                            })
                    except Exception:
                        continue

                # ── Step 2: Send replies in same session ──────────────────
                for reply_to, reply_text in replies.items():
                    try:
                        search_box = page.wait_for_selector(SELECTORS["SEARCH_BOX"], timeout=10000)
                        search_box.fill(reply_to)
                        page.keyboard.press('Enter')
                        page.wait_for_timeout(2000)

                        msg_input = page.wait_for_selector(SELECTORS["MESSAGE_INPUT"], timeout=10000)
                        msg_input.fill(reply_text)
                        page.click(SELECTORS["SEND_BUTTON"])
                        page.wait_for_timeout(2000)
                        sent.append(reply_to)
                    except Exception as e:
                        failed.append({"sender": reply_to, "error": str(e)})

                context.close()
                return {
                    "messages": messages,
                    "sent": sent,
                    "failed": failed,
                    "count": len(messages)
                }

    except Exception as e:
        raise Exception(f"PROCESS_INBOX_FAILED: {e}")


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
            },
            {
                "name": "get_messages",
                "description": "Read unread WhatsApp messages",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Max chats to check (default 10)"}
                    },
                    "required": []
                }
            },
            {
                "name": "process_inbox",
                "description": "Read unread messages AND send replies in one browser session",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "replies": {
                            "type": "object",
                            "description": "Map of {sender_name: reply_text} to send"
                        }
                    },
                    "required": ["replies"]
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
        if method == "initialize":
            # MCP handshake required by Claude CLI and other MCP clients
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "whatsapp-mcp", "version": "1.0.0"}
                }
            }

        elif method == "notifications/initialized":
            # Client confirms initialization — no response needed
            return None

        elif method == "tools/list":
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

            elif tool_name == "get_messages":
                result = get_messages(limit=arguments.get("limit", 10))
                return {"jsonrpc": "2.0", "id": request_id, "result": result}

            elif tool_name == "process_inbox":
                result = process_inbox(replies=arguments.get("replies", {}))
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
            if response is not None:
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
