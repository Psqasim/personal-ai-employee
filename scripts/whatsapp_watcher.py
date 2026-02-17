#!/usr/bin/env python3
"""
WhatsApp Watcher - Platinum Tier Auto-Reply Bot

Runs 24/7 as PM2 process. Every 30s:
1. Reads unread WhatsApp messages via whatsapp-mcp get_messages
2. Claude API (haiku) generates a smart reply
3. Urgent message? → WhatsApp notify admin immediately
4. Auto-sends reply back to sender

No Claude CLI needed — uses Claude API directly.
Enable with: ENABLE_WHATSAPP_WATCHER=true in .env

Author: Personal AI Employee (Platinum Tier)
Created: 2026-02-17
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [WA-WATCHER] - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ── Config ─────────────────────────────────────────────────────────────────
POLL_INTERVAL = int(os.getenv("WHATSAPP_POLL_INTERVAL", "30"))
ADMIN_NUMBER  = os.getenv("WHATSAPP_NOTIFICATION_NUMBER", "")
ENABLE        = os.getenv("ENABLE_WHATSAPP_WATCHER", "false").lower() == "true"
CLAUDE_MODEL  = "claude-haiku-4-5-20251001"   # fast + cheap for auto-reply

URGENT_KEYWORDS = [
    "urgent", "emergency", "asap", "help", "problem", "error",
    "down", "broken", "critical", "immediately", "crisis",
    "فوری", "مدد", "ضروری",  # Urdu
]

# In-memory cache to avoid replying twice to same message
_replied_cache: set = set()


# ── MCP helpers ────────────────────────────────────────────────────────────
def _mcp():
    from agent_skills.mcp_client import get_mcp_client
    return get_mcp_client(timeout=120)


def fetch_unread() -> List[Dict]:
    """Fetch unread messages via whatsapp-mcp get_messages."""
    try:
        r = _mcp().call_tool(
            mcp_server="whatsapp-mcp",
            tool_name="get_messages",
            arguments={"limit": 10},
            retry_count=1,
            retry_delay=2,
        )
        return r.get("messages", [])
    except Exception as e:
        logger.warning(f"fetch_unread failed: {e}")
        return []


def send_whatsapp(chat_id: str, message: str) -> bool:
    """Send reply via whatsapp-mcp send_message."""
    try:
        r = _mcp().call_tool(
            mcp_server="whatsapp-mcp",
            tool_name="send_message",
            arguments={"chat_id": chat_id, "message": message},
            retry_count=1,
            retry_delay=2,
        )
        return bool(r.get("message_id"))
    except Exception as e:
        logger.warning(f"send_whatsapp failed ({chat_id}): {e}")
        return False


# ── AI reply ───────────────────────────────────────────────────────────────
def generate_reply(sender: str, message: str) -> str:
    """Use Claude Haiku to generate a smart reply."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": (
                    f"You are Qasim's AI assistant. '{sender}' sent this WhatsApp message:\n\n"
                    f'"{message}"\n\n'
                    "Write a short, friendly, professional reply in the same language. "
                    "Max 2-3 sentences. Sign off as '— Qasim's Assistant'."
                )
            }]
        )
        return resp.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Claude API error: {e}")
        return "Thanks for your message! Qasim will get back to you shortly. — Qasim's Assistant"


# ── Urgency ────────────────────────────────────────────────────────────────
def is_urgent(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in URGENT_KEYWORDS)


def notify_admin(sender: str, message: str):
    """WhatsApp-notify admin about urgent incoming message."""
    if not ADMIN_NUMBER:
        return
    alert = (
        f"⚠️ *Urgent WhatsApp Received!*\n"
        f"From: {sender}\n"
        f"Message: {message[:200]}\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}"
    )
    try:
        from cloud_agent.src.notifications.whatsapp_notifier import _send_in_thread
        _send_in_thread(alert, "urgent_whatsapp")
        logger.info(f"Admin notified about urgent msg from {sender}")
    except Exception as e:
        logger.warning(f"Admin notify failed: {e}")


# ── Logging ────────────────────────────────────────────────────────────────
def log_action(sender: str, message: str, reply: str, urgent: bool, sent: bool):
    try:
        vault = Path(os.getenv("VAULT_PATH", "vault"))
        log_dir = vault / "Logs" / "WhatsApp"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "auto_replies.md"

        if not log_file.exists():
            log_file.write_text(
                "# WhatsApp Auto-Reply Log\n\n"
                "| Timestamp | From | Urgent | Replied | Message | Reply |\n"
                "|-----------|------|--------|---------|---------|-------|\n"
            )
        ts = datetime.now().isoformat()
        status_u = "🚨" if urgent else "—"
        status_r = "✅" if sent else "❌"
        msg_s = message[:50].replace("|", "-")
        rep_s = reply[:50].replace("|", "-")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"| {ts} | {sender} | {status_u} | {status_r} | {msg_s} | {rep_s} |\n")
    except Exception as e:
        logger.warning(f"log_action failed: {e}")


# ── Main loop ──────────────────────────────────────────────────────────────
def run():
    logger.info("🤖 WhatsApp Watcher started (Platinum Tier)")
    logger.info(f"Poll: {POLL_INTERVAL}s | Admin: {ADMIN_NUMBER or 'not set'}")

    if not ENABLE:
        logger.warning("ENABLE_WHATSAPP_WATCHER=false. Set to true in .env to start.")
        return

    while True:
        try:
            messages = fetch_unread()
            if messages:
                logger.info(f"📬 {len(messages)} unread message(s)")
            for msg in messages:
                sender  = msg.get("sender", "Unknown")
                text    = msg.get("message", "")
                key     = f"{sender}:{text[:50]}"

                if key in _replied_cache:
                    continue

                urgent = is_urgent(text)
                logger.info(f"{'🚨 URGENT' if urgent else '📩'} from {sender}: {text[:60]}")

                if urgent:
                    notify_admin(sender, text)

                reply = generate_reply(sender, text)
                sent  = send_whatsapp(sender, reply)
                log_action(sender, text, reply, urgent, sent)

                if sent:
                    logger.info(f"✅ Replied to {sender}")
                else:
                    logger.warning(f"⚠️ Reply failed to {sender}")

                _replied_cache.add(key)
                if len(_replied_cache) > 500:
                    _replied_cache.clear()

        except Exception as e:
            logger.error(f"Loop error: {e}")

        time.sleep(POLL_INTERVAL)


# ── Gold-tier compat (vault/Inbox/ file-based monitoring) ──────────────────
def monitor_whatsapp_for_drafts(vault_path: str, poll_interval: int = 30):
    """Legacy Gold-tier entry point — just calls run()."""
    run()


def detect_keywords(message: str, keywords: list) -> list:
    msg_lower = message.lower()
    return [kw for kw in keywords if kw.lower() in msg_lower]


if __name__ == "__main__":
    run()
