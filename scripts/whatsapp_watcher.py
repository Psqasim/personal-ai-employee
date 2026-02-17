#!/usr/bin/env python3
"""
WhatsApp Watcher - Platinum Tier Auto-Reply Bot

ONE browser session per 30s cycle:
  open → click first 5 chats → read incoming msg → send reply (still in chat) → close

Runs as PM2 locally OR on Oracle Cloud (headless=True on Linux server).
Enable: ENABLE_WHATSAPP_WATCHER=true in .env

Author: Personal AI Employee (Platinum Tier)
Created: 2026-02-17
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [WA-WATCHER] - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
POLL_INTERVAL  = int(os.getenv("WHATSAPP_POLL_INTERVAL", "30"))
ADMIN_NUMBER   = os.getenv("WHATSAPP_NOTIFICATION_NUMBER", "")
ENABLE         = os.getenv("ENABLE_WHATSAPP_WATCHER", "false").lower() == "true"
SESSION_PATH   = os.getenv("WHATSAPP_SESSION_PATH", "/home/ps_qasim/.whatsapp_session_dir")
CLAUDE_MODEL   = "claude-haiku-4-5-20251001"
CHATS_TO_CHECK = 5
# Oracle Cloud = headless=True (real Linux), local WSL2 = headless=False
HEADLESS       = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"

URGENT_KEYWORDS = [
    "urgent", "emergency", "asap", "help", "problem", "error",
    "down", "broken", "critical", "immediately", "crisis",
    "فوری", "مدد", "ضروری",
]

_replied_cache: set = set()

# WhatsApp Web selectors
MSG_INPUT   = 'div[contenteditable="true"][data-tab="10"]'
CHAT_LIST   = 'div[aria-label="Chat list"], #pane-side'
QR_CODE     = 'canvas[aria-label="Scan this QR code to link a device!"]'


# ── Claude API ───────────────────────────────────────────────────────────────
def generate_reply(sender: str, message: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": (
                    f"You are Qasim's AI assistant. '{sender}' sent:\n\"{message}\"\n\n"
                    "Write a short friendly reply in the same language (max 2 sentences). "
                    "Sign off: '— Qasim's Assistant'"
                )
            }]
        )
        return resp.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Claude API error: {e}")
        return "Thanks for your message! Qasim will reply soon. — Qasim's Assistant"


def is_urgent(text: str) -> bool:
    return any(kw in text.lower() for kw in URGENT_KEYWORDS)


def notify_admin(sender: str, message: str):
    if not ADMIN_NUMBER:
        return
    try:
        from cloud_agent.src.notifications.whatsapp_notifier import _send_in_thread
        _send_in_thread(
            f"⚠️ *Urgent WhatsApp!*\nFrom: {sender}\n{message[:200]}",
            "urgent_whatsapp"
        )
    except Exception as e:
        logger.warning(f"Admin notify failed: {e}")


def log_action(sender: str, msg: str, reply: str, urgent: bool, sent: bool):
    try:
        vault = Path(os.getenv("VAULT_PATH", "vault"))
        log_dir = vault / "Logs" / "WhatsApp"
        log_dir.mkdir(parents=True, exist_ok=True)
        f = log_dir / "auto_replies.md"
        if not f.exists():
            f.write_text("# WhatsApp Auto-Reply Log\n\n| Time | From | Urgent | Sent | Message | Reply |\n|------|------|--------|------|---------|-------|\n")
        ts = datetime.now().strftime("%H:%M:%S")
        with open(f, "a", encoding="utf-8") as fp:
            fp.write(f"| {ts} | {sender} | {'🚨' if urgent else '—'} | {'✅' if sent else '❌'} | {msg[:40].replace('|','-')} | {reply[:40].replace('|','-')} |\n")
    except Exception:
        pass


# ── Core cycle ───────────────────────────────────────────────────────────────
def run_cycle():
    """
    Open ONE browser session:
    1. Click each of first N chats
    2. Read last incoming message (div.message-in)
    3. Generate Claude reply
    4. Send reply WHILE STILL IN THAT CHAT (no search needed)
    5. Move to next chat
    6. Close browser
    """
    if not os.path.isdir(SESSION_PATH):
        logger.error(f"Session missing: {SESSION_PATH} — run setup_whatsapp_session.py")
        return

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=HEADLESS,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--window-size=1,1",
                "--window-position=0,0",
            ],
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        try:
            page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)
            page.wait_for_selector(f'{CHAT_LIST}, {QR_CODE}', timeout=60000)

            if page.locator(QR_CODE).count() > 0:
                logger.error("QR shown — re-run setup_whatsapp_session.py")
                context.close()
                return

            page.wait_for_timeout(2000)

            # Get chat list rows
            rows = page.locator('div[aria-label="Chat list"] > div').all()
            if not rows:
                rows = page.locator('#pane-side > div > div > div').all()

            logger.info(f"Found {len(rows)} chats, checking first {CHATS_TO_CHECK}")

            for i, row in enumerate(rows[:CHATS_TO_CHECK]):
                try:
                    # ── Click chat to open it ─────────────────────────
                    row.click()
                    page.wait_for_timeout(2000)

                    # ── Get sender name from conversation header ───────
                    sender = f"Chat_{i+1}"
                    for sel in [
                        'header span[dir="auto"]',
                        'div[data-testid="conversation-info-header"] span[dir="auto"]',
                        'span[data-testid="conversation-info-header-chat-title"]',
                    ]:
                        el = page.locator(sel)
                        if el.count() > 0:
                            t = el.first.inner_text().strip()
                            if t:
                                sender = t
                                break

                    # ── Get last incoming message ──────────────────────
                    # Try multiple selectors — WhatsApp Web changes frequently
                    last_msg = ""
                    for msg_sel in [
                        'div.message-in span.selectable-text',
                        'div[class*="message-in"] span.selectable-text',
                        'div[class*="message-in"] span[dir="ltr"]',
                        'div[class*="message-in"] span[dir="rtl"]',
                        # Fallback: last message in conversation regardless of direction
                        'div[data-testid="msg-container"] span.selectable-text',
                    ]:
                        els = page.locator(msg_sel).all()
                        if els:
                            try:
                                last_msg = els[-1].inner_text().strip()
                                if last_msg:
                                    break
                            except Exception:
                                continue

                    if not last_msg:
                        logger.debug(f"No incoming msg in chat {sender}")
                        continue

                    cache_key = f"{sender}:{last_msg[:50]}"
                    if cache_key in _replied_cache:
                        logger.debug(f"Already replied to {sender}")
                        continue

                    logger.info(f"📩 {sender}: {last_msg[:70]}")
                    urgent = is_urgent(last_msg)
                    if urgent:
                        logger.warning(f"🚨 URGENT from {sender}!")
                        notify_admin(sender, last_msg)

                    # ── Generate reply ────────────────────────────────
                    reply = generate_reply(sender, last_msg)
                    logger.info(f"💬 Reply: {reply[:60]}")

                    # ── Send reply — we're ALREADY in this chat! ──────
                    # Just fill the message input and press Enter
                    sent = False
                    try:
                        msg_box = page.wait_for_selector(MSG_INPUT, timeout=8000)
                        msg_box.click()
                        msg_box.fill(reply)
                        page.wait_for_timeout(500)
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(2000)
                        sent = True
                        logger.info(f"✅ Sent to {sender}")
                    except Exception as e:
                        logger.warning(f"⚠️ Send failed to {sender}: {e}")

                    _replied_cache.add(cache_key)
                    log_action(sender, last_msg, reply, urgent, sent)

                except Exception as e:
                    logger.debug(f"Chat {i} error: {e}")
                    continue

        except PlaywrightTimeout as e:
            logger.warning(f"Timeout: {e}")
        except Exception as e:
            logger.error(f"Cycle error: {e}")
        finally:
            context.close()

    if len(_replied_cache) > 500:
        _replied_cache.clear()


# ── Main loop ────────────────────────────────────────────────────────────────
def run():
    logger.info("🤖 WhatsApp Watcher started (Platinum Tier)")
    logger.info(f"Poll: {POLL_INTERVAL}s | Chats: {CHATS_TO_CHECK} | Headless: {HEADLESS} | Admin: {ADMIN_NUMBER or 'not set'}")

    if not ENABLE:
        logger.warning("ENABLE_WHATSAPP_WATCHER=false — set to true in .env")
        return

    while True:
        try:
            run_cycle()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        time.sleep(POLL_INTERVAL)


# Legacy compat
def monitor_whatsapp_for_drafts(vault_path: str, poll_interval: int = 30):
    run()

def detect_keywords(message: str, keywords: list) -> list:
    return [kw for kw in keywords if kw.lower() in message.lower()]


if __name__ == "__main__":
    run()
