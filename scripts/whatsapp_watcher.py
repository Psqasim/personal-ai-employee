#!/usr/bin/env python3
"""
WhatsApp Watcher - Platinum Tier Auto-Reply Bot

ONE browser session per cycle:
 open → read first 5 chats → generate replies → send → close

Avoids Chrome user-data-dir lock (only one open at a time).
Runs 24/7 as PM2 process. Enable: ENABLE_WHATSAPP_WATCHER=true

Author: Personal AI Employee (Platinum Tier)
Created: 2026-02-17
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict

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

# ── Config ─────────────────────────────────────────────────────────────────
POLL_INTERVAL  = int(os.getenv("WHATSAPP_POLL_INTERVAL", "30"))
ADMIN_NUMBER   = os.getenv("WHATSAPP_NOTIFICATION_NUMBER", "")
ENABLE         = os.getenv("ENABLE_WHATSAPP_WATCHER", "false").lower() == "true"
SESSION_PATH   = os.getenv("WHATSAPP_SESSION_PATH", "/home/ps_qasim/.whatsapp_session_dir")
CLAUDE_MODEL   = "claude-haiku-4-5-20251001"
CHATS_TO_CHECK = 5   # check first N chats every cycle

URGENT_KEYWORDS = [
    "urgent", "emergency", "asap", "help", "problem", "error",
    "down", "broken", "critical", "immediately", "crisis",
    "فوری", "مدد", "ضروری",
]

_replied_cache: set = set()

SELECTORS = {
    "LOGGED_IN"    : 'div[aria-label="Chat list"], #pane-side',
    "QR_CODE"      : 'canvas[aria-label="Scan this QR code to link a device!"]',
    "SEARCH_BOX"   : 'div[contenteditable="true"][data-tab="3"]',
    "MESSAGE_INPUT": 'div[contenteditable="true"][data-tab="10"]',
    "SEND_BUTTON"  : 'button[data-tab="11"]',
}


# ── Claude API ──────────────────────────────────────────────────────────────
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
                    f"You are Qasim's AI assistant. '{sender}' sent this WhatsApp:\n\n"
                    f'"{message}"\n\n'
                    "Write a short friendly reply in the same language (max 2 sentences). "
                    "Sign off: '— Qasim\\'s Assistant'"
                )
            }]
        )
        return resp.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Claude API: {e}")
        return "Thanks for your message! Qasim will get back to you soon. — Qasim's Assistant"


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


def log_action(sender: str, message: str, reply: str, urgent: bool, sent: bool):
    try:
        vault = Path(os.getenv("VAULT_PATH", "vault"))
        log_dir = vault / "Logs" / "WhatsApp"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "auto_replies.md"
        if not log_file.exists():
            log_file.write_text(
                "# WhatsApp Auto-Reply Log\n\n"
                "| Time | From | Urgent | Sent | Message | Reply |\n"
                "|------|------|--------|------|---------|-------|\n"
            )
        ts = datetime.now().strftime("%H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(
                f"| {ts} | {sender} | {'🚨' if urgent else '—'} | "
                f"{'✅' if sent else '❌'} | "
                f"{message[:40].replace('|','-')} | {reply[:40].replace('|','-')} |\n"
            )
    except Exception:
        pass


# ── Core: ONE browser session reads + sends ─────────────────────────────────
def run_cycle():
    """
    Open WhatsApp Web ONCE, check first N chats for incoming messages,
    generate replies with Claude, send them — all before closing.
    """
    if not os.path.isdir(SESSION_PATH):
        logger.error(f"Session not found: {SESSION_PATH} — run setup_whatsapp_session.py")
        return

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=SESSION_PATH,
            headless=False,
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--window-size=1,1", "--window-position=0,0"],
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        try:
            page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)

            page.wait_for_selector(
                f'{SELECTORS["LOGGED_IN"]}, {SELECTORS["QR_CODE"]}',
                timeout=60000
            )
            if page.locator(SELECTORS["QR_CODE"]).count() > 0:
                logger.error("QR code shown — re-run setup_whatsapp_session.py")
                context.close()
                return

            page.wait_for_timeout(2000)

            # ── Read first N chats ────────────────────────────────────
            # Use JS to get all chat rows — more reliable than CSS selectors
            chat_rows = page.locator(
                'div[aria-label="Chat list"] > div'
            ).all()

            if not chat_rows:
                # Fallback: any clickable row in the chat list pane
                chat_rows = page.locator('#pane-side > div > div > div').all()

            logger.info(f"Chat rows found: {len(chat_rows)}")

            to_reply: Dict[str, str] = {}   # {sender: reply_text}

            for i, row in enumerate(chat_rows[:CHATS_TO_CHECK]):
                try:
                    row.click()
                    page.wait_for_timeout(1500)

                    # Get sender name from conversation header
                    header = page.locator(
                        'header span[dir="auto"], '
                        'div[data-testid="conversation-info-header"] span'
                    )
                    sender = header.first.inner_text().strip() if header.count() > 0 else f"Chat_{i}"

                    # Get last INCOMING message (class message-in)
                    incoming = page.locator('div.message-in span.selectable-text')
                    if incoming.count() == 0:
                        continue

                    last_msg = incoming.last.inner_text().strip()
                    if not last_msg:
                        continue

                    cache_key = f"{sender}:{last_msg[:50]}"
                    if cache_key in _replied_cache:
                        logger.debug(f"Already replied to {sender}")
                        continue

                    logger.info(f"📩 {sender}: {last_msg[:60]}")
                    urgent = is_urgent(last_msg)
                    if urgent:
                        logger.warning(f"🚨 URGENT from {sender}!")
                        notify_admin(sender, last_msg)

                    # Generate reply with Claude API
                    reply = generate_reply(sender, last_msg)
                    to_reply[sender] = (reply, last_msg, urgent, cache_key)

                except Exception as e:
                    logger.debug(f"Row {i} error: {e}")
                    continue

            # ── Send replies (browser still open!) ───────────────────
            for sender, (reply, orig_msg, urgent, cache_key) in to_reply.items():
                try:
                    search = page.wait_for_selector(SELECTORS["SEARCH_BOX"], timeout=8000)
                    search.fill(sender)
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(2000)

                    msg_input = page.wait_for_selector(SELECTORS["MESSAGE_INPUT"], timeout=8000)
                    msg_input.fill(reply)
                    page.click(SELECTORS["SEND_BUTTON"])
                    page.wait_for_timeout(2000)

                    logger.info(f"✅ Replied to {sender}: {reply[:60]}")
                    _replied_cache.add(cache_key)
                    log_action(sender, orig_msg, reply, urgent, True)

                except Exception as e:
                    logger.warning(f"⚠️ Send failed to {sender}: {e}")
                    log_action(sender, orig_msg if 'orig_msg' in dir() else "", reply, urgent, False)

        except PlaywrightTimeout as e:
            logger.warning(f"Timeout: {e}")
        except Exception as e:
            logger.error(f"Cycle error: {e}")
        finally:
            context.close()

    if len(_replied_cache) > 500:
        _replied_cache.clear()


# ── Main loop ───────────────────────────────────────────────────────────────
def run():
    logger.info("🤖 WhatsApp Watcher started (Platinum Tier)")
    logger.info(f"Poll: {POLL_INTERVAL}s | Chats/cycle: {CHATS_TO_CHECK} | Admin: {ADMIN_NUMBER or 'not set'}")

    if not ENABLE:
        logger.warning("ENABLE_WHATSAPP_WATCHER=false — set to true in .env to start.")
        return

    while True:
        logger.debug("Running cycle...")
        try:
            run_cycle()
        except Exception as e:
            logger.error(f"Unexpected: {e}")
        time.sleep(POLL_INTERVAL)


# Legacy compat
def monitor_whatsapp_for_drafts(vault_path: str, poll_interval: int = 30):
    run()

def detect_keywords(message: str, keywords: list) -> list:
    return [kw for kw in keywords if kw.lower() in message.lower()]


if __name__ == "__main__":
    run()
