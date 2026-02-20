#!/usr/bin/env python3
"""
WhatsApp Watcher - Platinum Tier Auto-Reply Bot

3-phase cycle every 30s:
  Phase 1 (browser): open → read all chats → close
  Phase 2 (no browser): generate Claude replies
  Phase 3 (browser): open → send all replies → close

Splitting avoids browser crash while Claude API is running (30-60s).
Runs as PM2 locally OR on Oracle Cloud (headless=True on Linux server).
Enable: ENABLE_WHATSAPP_WATCHER=true in .env

Author: Personal AI Employee (Platinum Tier)
Created: 2026-02-17
"""

import os
import sys
import time
import fcntl
import logging
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
# Load .env first, then .env.cloud (cloud-specific vars override local defaults)
_env_file = os.getenv("ENV_FILE", str(project_root / ".env"))
load_dotenv(_env_file)
load_dotenv(project_root / ".env.cloud", override=True)  # no-op if file missing

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
# WSL2 needs --no-zygote (SIGTRAP fix) regardless of headless mode.
# Real Linux (Oracle Cloud) must NOT use it — causes Chrome startup slowdown.
_IS_WSL2 = os.path.exists("/proc/version") and \
    "microsoft" in open("/proc/version").read().lower()

URGENT_KEYWORDS = [
    "urgent", "emergency", "asap", "help", "problem", "error",
    "down", "broken", "critical", "immediately", "crisis",
    "فوری", "مدد", "ضروری",
]

_replied_cache: set = set()

# Shared lock file — prevents watcher and MCP server from opening Chrome simultaneously
BROWSER_LOCK_FILE = "/tmp/whatsapp_browser.lock"

VAULT_PATH = os.getenv("VAULT_PATH", str(project_root / "vault"))

# WhatsApp Web selectors
MSG_INPUT   = 'div[contenteditable="true"][data-tab="10"]'
CHAT_LIST   = 'div[aria-label="Chat list"], #pane-side'
QR_CODE     = 'canvas[aria-label="Scan this QR code to link a device!"]'


@contextmanager
def _browser_lock(timeout: int = 90):
    """
    Exclusive file lock around any Chrome open/close.
    Prevents watcher and MCP server from fighting over user_data_dir.
    Waits up to `timeout` seconds then gives up.
    """
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
                    raise TimeoutError("Could not acquire browser lock — another process is using Chrome")
                time.sleep(2)
        yield
    finally:
        try:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
        except Exception:
            pass
        lock_f.close()


# ── Admin command handler ─────────────────────────────────────────────────────
def handle_admin_command(sender: str, message: str) -> Optional[str]:
    """
    If the message is an admin command, parse it, create a vault draft,
    and return a confirmation reply string.
    Returns None if not an admin command (caller should use normal reply flow).
    """
    try:
        from cloud_agent.src.command_router import is_admin_command, route_command
    except ImportError as e:
        logger.warning(f"command_router import failed: {e}")
        return None

    if not is_admin_command(sender, message):
        return None

    logger.info(f"🎯 Admin command from {sender}: {message[:60]}")

    result = route_command(message, vault_path=VAULT_PATH)

    if result["success"]:
        action = result["action"]
        intent = result["intent"]
        draft_path = result["draft_path"] or ""
        draft_name = Path(draft_path).name if draft_path else "draft"

        # Build human-readable confirmation
        action_labels = {
            "create_draft_invoice": "📋 Invoice draft",
            "create_draft_expense": "💸 Expense draft",
            "create_contact":       "👤 Contact draft",
            "register_payment":     "💳 Payment draft",
            "create_purchase_bill": "🧾 Vendor bill draft",
            "send_email":           "📧 Email draft",
            "send_message":         "💬 WhatsApp draft",
            "create_post":          "🔗 LinkedIn draft",
        }
        label = action_labels.get(action, f"📝 {action}")

        details = ""
        if action in ("create_draft_invoice", "create_draft_expense", "create_purchase_bill"):
            details = f"\nCustomer/Vendor: {intent.get('customer', intent.get('vendor', '?'))}\nAmount: {intent.get('currency', 'PKR')} {intent.get('amount', 0):,}"
        elif action == "send_email":
            details = f"\nTo: {intent.get('to', '?')}\nSubject: {intent.get('subject', '?')}"
        elif action == "send_message":
            details = f"\nTo: {intent.get('chat_id', '?')}"
        elif action == "create_contact":
            details = f"\nName: {intent.get('customer', intent.get('name', '?'))}"
        elif action == "register_payment":
            details = f"\nInvoice: {intent.get('invoice_number', '?')}"

        reply = (
            f"✅ {label} created!\n"
            f"{details}\n\n"
            f"📂 File: {draft_name}\n"
            f"👉 Open dashboard to approve → execute."
        ).strip()

        logger.info(f"✅ Admin command processed: {action} → {draft_name}")
        return reply
    else:
        err = result.get("error", "Unknown error")
        logger.warning(f"⚠️ Admin command failed: {err}")
        return f"❌ Could not process command: {err}\n\nTry: \"invoice Ali 5000 Rs web design\""


# ── Claude API ───────────────────────────────────────────────────────────────
def generate_reply(sender: str, message: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            system=(
                "You are Qasim's personal AI assistant managing his WhatsApp. "
                "Qasim is a software engineer and AI developer working on automation projects. "
                "Reply naturally and helpfully in the SAME language as the incoming message. "
                "Keep replies short (1-3 sentences). Be warm and conversational. "
                "If asked what Qasim is doing, say he is working on AI automation projects. "
                "If urgent, acknowledge it. Always sign off: '— Qasim's Assistant'"
            ),
            messages=[{
                "role": "user",
                "content": f"Message from '{sender}': \"{message}\"\n\nReply on Qasim's behalf:"
            }]
        )
        return resp.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Claude API error: {e}")
        return "Qasim is currently busy with work. He'll get back to you soon! — Qasim's Assistant"


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


# ── Browser helpers ───────────────────────────────────────────────────────────
def _make_browser(p):
    """Launch a fresh persistent context (closes after each phase).
    --no-zygote is WSL2-only (fixes SIGTRAP crash). On real Linux (cloud/headless)
    it slows Chrome startup and causes 60s selector timeouts — do NOT use it there.
    """
    args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-crash-reporter",
        "--disable-background-networking",
    ]
    if _IS_WSL2:
        # WSL2: --no-zygote prevents SIGTRAP crash (needed even in headless mode)
        args.append("--no-zygote")
    if HEADLESS:
        # Cloud/server: disable GPU, use SwiftShader so Chrome doesn't report
        # itself as "HeadlessChrome" (which WhatsApp blocks with "Update Chrome")
        args += ["--disable-gpu", "--enable-unsafe-swiftshader",
                 "--disable-setuid-sandbox", "--no-first-run", "--mute-audio"]

    # Spoof a real Chrome UA — WhatsApp blocks the default "HeadlessChrome" UA
    ua = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")

    return p.chromium.launch_persistent_context(
        user_data_dir=SESSION_PATH,
        headless=HEADLESS,
        args=args,
        user_agent=ua,
        viewport={"width": 1280, "height": 800},
    )


def _wait_for_whatsapp(page) -> bool:
    """Navigate to WhatsApp Web and wait for chat list. Returns False if QR shown."""
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=40000)
    # Cloud VM (headless) needs more time for JS-heavy WhatsApp Web to initialise
    page.wait_for_timeout(20000 if HEADLESS else 4000)
    page.wait_for_selector(f'{CHAT_LIST}, {QR_CODE}', timeout=60000)
    if page.locator(QR_CODE).count() > 0:
        logger.error("QR shown — re-run setup_whatsapp_session.py")
        return False
    page.wait_for_timeout(2000)
    return True


def _read_sender(page, i: int) -> str:
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
                return t
    return sender


def _read_last_msg(page) -> str:
    for msg_sel in [
        'div.message-in span.selectable-text',
        'div[class*="message-in"] span.selectable-text',
        'div[class*="message-in"] span[dir="ltr"]',
        'div[class*="message-in"] span[dir="rtl"]',
        'div[data-testid="msg-container"] span.selectable-text',
    ]:
        els = page.locator(msg_sel).all()
        if els:
            try:
                t = els[-1].inner_text().strip()
                if t:
                    return t
            except Exception:
                continue
    return ""


# ── Core cycle ───────────────────────────────────────────────────────────────
def run_cycle():
    """
    3-phase cycle — browser is closed before Claude API is called,
    so long API calls never crash the browser:

    Phase 1 (browser open):  Read messages from first N chats → close browser
    Phase 2 (no browser):    Generate Claude replies for each message
    Phase 3 (browser open):  Send each reply in the correct chat → close browser
    """
    if not os.path.isdir(SESSION_PATH):
        logger.error(f"Session missing: {SESSION_PATH} — run setup_whatsapp_session.py")
        return

    # ── Phase 1: Read (locked) ────────────────────────────────────────────────
    inbox: list[tuple[str, str]] = []   # (sender, last_msg)
    _seen_this_cycle: set = set()       # deduplicate within one cycle

    try:
        with _browser_lock():
            with sync_playwright() as p:
                ctx = _make_browser(p)
                page = ctx.new_page()
                try:
                    if not _wait_for_whatsapp(page):
                        ctx.close()
                        return

                    rows = page.locator('div[aria-label="Chat list"] > div').all()
                    if not rows:
                        rows = page.locator('#pane-side > div > div > div').all()
                    logger.info(f"Found {len(rows)} chats, checking first {CHATS_TO_CHECK}")

                    for i, row in enumerate(rows[:CHATS_TO_CHECK]):
                        try:
                            row.click()
                            page.wait_for_timeout(2000)
                            sender   = _read_sender(page, i)
                            last_msg = _read_last_msg(page)

                            if not last_msg:
                                logger.debug(f"No incoming msg in {sender}")
                                continue

                            cache_key = f"{sender}:{last_msg[:50]}"
                            if cache_key in _replied_cache or cache_key in _seen_this_cycle:
                                logger.debug(f"Already replied/seen: {sender}")
                                continue

                            _seen_this_cycle.add(cache_key)
                            logger.info(f"📩 {sender}: {last_msg[:70]}")
                            inbox.append((sender, last_msg))

                            urgent = is_urgent(last_msg)
                            if urgent:
                                logger.warning(f"🚨 URGENT from {sender}!")
                                notify_admin(sender, last_msg)
                        except Exception as e:
                            logger.debug(f"Read error chat {i}: {e}")

                except (PlaywrightTimeout, Exception) as e:
                    logger.warning(f"Phase-1 error: {e}")
                finally:
                    ctx.close()   # ← browser fully closed before API calls
    except TimeoutError as e:
        logger.warning(f"Phase-1 lock timeout: {e}")
        return

    if not inbox:
        return

    # ── Phase 2: Generate replies (no browser, lock released) ─────────────────
    pending: list[tuple[str, str, str]] = []   # (sender, last_msg, reply)
    for sender, last_msg in inbox:
        # Check for admin commands FIRST — if matched, skip normal reply
        cmd_reply = handle_admin_command(sender, last_msg)
        if cmd_reply is not None:
            reply = cmd_reply
        else:
            reply = generate_reply(sender, last_msg)
        logger.info(f"💬 {sender} → {reply[:60]}")
        pending.append((sender, last_msg, reply))

    # Give Chrome time to finish flushing the Phase-1 profile to disk.
    # On Oracle Free Tier (slow I/O), opening Chrome too quickly after Phase-1
    # closes causes the profile dir to be in a partial-write state → Phase-3
    # Chrome never fully initialises → WhatsApp Web never loads → 60s timeout.
    time.sleep(10)

    # ── Phase 3: Send (locked) ────────────────────────────────────────────────
    try:
        with _browser_lock():
            with sync_playwright() as p:
                ctx = _make_browser(p)
                page = ctx.new_page()
                try:
                    if not _wait_for_whatsapp(page):
                        ctx.close()
                        return

                    rows = page.locator('div[aria-label="Chat list"] > div').all()
                    if not rows:
                        rows = page.locator('#pane-side > div > div > div').all()

                    # Build a name→row index map (first CHATS_TO_CHECK rows)
                    row_map: dict[str, int] = {}
                    for i, row in enumerate(rows[:CHATS_TO_CHECK]):
                        try:
                            row.click()
                            page.wait_for_timeout(1500)
                            name = _read_sender(page, i)
                            row_map[name] = i
                        except Exception:
                            pass

                    for sender, last_msg, reply in pending:
                        sent = False
                        try:
                            idx = row_map.get(sender)
                            if idx is not None:
                                rows[idx].click()
                                page.wait_for_timeout(1500)

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

                        cache_key = f"{sender}:{last_msg[:50]}"
                        _replied_cache.add(cache_key)
                        log_action(sender, last_msg, reply, is_urgent(last_msg), sent)

                except (PlaywrightTimeout, Exception) as e:
                    logger.warning(f"Phase-3 error: {e}")
                finally:
                    ctx.close()
    except TimeoutError as e:
        logger.warning(f"Phase-3 lock timeout: {e}")

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
