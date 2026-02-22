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
import re
import time
import fcntl
import json
import shutil
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
CHATS_TO_CHECK = int(os.getenv("CHATS_TO_CHECK", "10"))  # read from env, default 10
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
_warmed_up: bool = False  # True after first-cycle dry-run completes

# Persist cache to disk so it survives restarts (avoids replying to old messages again)
_CACHE_FILE = os.path.expanduser("~/.whatsapp_replied_cache.json")
_CACHE_MAX_AGE_HOURS = 24


def _load_cache() -> None:
    """Load persisted reply cache — only keep entries < 24h old."""
    global _replied_cache
    try:
        if os.path.exists(_CACHE_FILE):
            with open(_CACHE_FILE) as f:
                data = json.load(f)
            cutoff = time.time() - _CACHE_MAX_AGE_HOURS * 3600
            _replied_cache = {k for k, ts in data.items() if ts > cutoff}
            logger.info(f"📂 Loaded {len(_replied_cache)} cache entries from disk")
    except Exception as e:
        logger.warning(f"Cache load error (starting fresh): {e}")
        _replied_cache = set()


def _save_cache() -> None:
    """Persist reply cache to disk with timestamps."""
    try:
        now = time.time()
        data = {k: now for k in _replied_cache}
        with open(_CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Cache save error: {e}")


# Shared lock file — prevents watcher and MCP server from opening Chrome simultaneously
BROWSER_LOCK_FILE = "/tmp/whatsapp_browser.lock"

VAULT_PATH = os.getenv("VAULT_PATH", str(project_root / "vault"))

# WhatsApp Web selectors
MSG_INPUT   = 'div[contenteditable="true"][data-tab="10"]'
CHAT_LIST   = 'div[aria-label="Chat list"], #pane-side'
# WhatsApp Web updated: QR is now an <img>, not <canvas>. Also detect the
# "Steps to log in" landing page (login-required / session expired state).
QR_CODE     = ('canvas[aria-label="Scan this QR code to link a device!"], '
               'img[alt="Scan this QR code to link a device"], '
               'div[data-testid="intro-title"], '
               'a[href*="phone-number"]')


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

    # If Claude couldn't parse a command action, treat as normal conversation
    if result.get("action") == "unknown" or not result["success"] and "Could not parse" in str(result.get("error", "")):
        logger.info(f"💬 Admin message not a command (falling back to AI chat): {message[:40]}")
        return None  # caller uses generate_reply() instead

    if result["success"]:
        action = result["action"]
        intent = result["intent"]
        draft_path = result["draft_path"] or ""
        draft_name = Path(draft_path).name if draft_path else "draft"

        # Build human-readable confirmation
        # WhatsApp send_message goes directly to Approved/ (no dashboard needed)
        # All other actions go to Pending_Approval/ (need dashboard review)
        needs_approval = action != "send_message"

        action_labels = {
            "create_draft_invoice": "📋 Invoice draft",
            "create_draft_expense": "💸 Expense draft",
            "create_contact":       "👤 Contact draft",
            "register_payment":     "💳 Payment draft",
            "create_purchase_bill": "🧾 Vendor bill draft",
            "send_email":           "📧 Email draft",
            "send_message":         "💬 WhatsApp",
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

        if needs_approval:
            footer = f"📂 File: {draft_name}\n👉 Open dashboard to approve → execute."
        else:
            footer = "⏳ Sending now... will deliver in ~30-60s (no approval needed)."

        reply = (
            f"✅ {label} {'draft created' if needs_approval else 'queued'}!\n"
            f"{details}\n\n"
            f"{footer}"
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


def _dismiss_dialogs(page) -> None:
    """Dismiss any WhatsApp popup/modal dialogs blocking the UI (max 3 attempts).
    Covers: 'New features', notification prompts, update banners, etc.
    """
    for _ in range(3):
        try:
            dialog = page.locator('[role="dialog"]')
            if dialog.count() == 0:
                break
            # Try close button inside dialog first
            close_btn = dialog.locator(
                'button[aria-label="Close"], '
                'button[aria-label="OK"], '
                'button[aria-label="Got it"], '
                'button[data-testid="popup-controls-ok"], '
                'span[data-icon="x"]'
            )
            if close_btn.count() > 0:
                close_btn.first.click(timeout=3000)
            else:
                page.keyboard.press("Escape")
            page.wait_for_timeout(800)
        except Exception:
            break


def _wait_for_whatsapp(page) -> bool:
    """Navigate to WhatsApp Web and wait for chat list. Returns False if QR shown."""
    page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=40000)
    # Cloud VM (headless) needs more time for JS-heavy WhatsApp Web to initialise
    page.wait_for_timeout(20000 if HEADLESS else 4000)
    page.wait_for_selector(f'{CHAT_LIST}, {QR_CODE}', timeout=60000)
    # Check any login-required indicator (canvas OR img QR, landing page, phone link)
    # Also check absence of chat list as final fallback (page loaded but no chats = logged out)
    is_login_page = any(
        page.locator(sel).count() > 0
        for sel in [
            'canvas[aria-label="Scan this QR code to link a device!"]',
            'img[alt="Scan this QR code to link a device"]',
            'div[data-testid="intro-title"]',
            'a[href*="phone-number"]',
            'div.landing-title',
            'div.app-wrapper-web.no-list',
        ]
    ) or (
        # App loaded but neither chat list nor pane-side exists = session expired
        page.locator('div.app-wrapper-web').count() > 0
        and page.locator(CHAT_LIST).count() == 0
    )
    if is_login_page:
        logger.error("Login page shown — session expired. Re-run wa_reauth.py")
        return False
    page.wait_for_timeout(2000)
    _dismiss_dialogs(page)  # clear any popup before interacting
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


def _parse_vault_frontmatter(file_path: Path) -> dict:
    """Parse YAML frontmatter from a vault .md file (minimal parser)."""
    try:
        raw = file_path.read_text(encoding="utf-8")
        m = re.match(r'^---\n(.*?)\n---', raw, re.DOTALL)
        if not m:
            return {}
        fm: dict = {}
        for line in m.group(1).splitlines():
            if ':' not in line:
                continue
            k, _, v = line.partition(':')
            v = v.strip().strip('"').strip("'")
            # Handle multi-line values (draft_body)
            fm[k.strip()] = v
        return fm
    except Exception:
        return {}


def _send_vault_whatsapp_drafts(page) -> None:
    """
    Check vault/Approved/WhatsApp/ for pending send_message drafts and deliver them.
    Called inside the Phase-3 browser session — reuses the already-open WhatsApp page.
    Moves file to Done/ on success, Failed/ on error.
    """
    wa_approved = Path(VAULT_PATH) / "Approved" / "WhatsApp"
    wa_done     = Path(VAULT_PATH) / "Done"     / "WhatsApp"
    wa_failed   = Path(VAULT_PATH) / "Failed"   / "WhatsApp"

    if not wa_approved.exists():
        return

    draft_files = sorted(wa_approved.glob("*.md"))
    if not draft_files:
        return

    wa_done.mkdir(parents=True, exist_ok=True)
    wa_failed.mkdir(parents=True, exist_ok=True)

    for draft_file in draft_files:
        fm = _parse_vault_frontmatter(draft_file)
        if fm.get("action") != "send_message":
            continue

        chat_id  = fm.get("chat_id") or fm.get("to", "")
        body     = fm.get("draft_body", "")

        if not chat_id or not body:
            logger.warning(f"Vault WA draft missing chat_id or body: {draft_file.name}")
            shutil.move(str(draft_file), str(wa_failed / draft_file.name))
            continue

        # Strip non-digits for URL, keep international format (no leading +)
        phone = re.sub(r"[^\d]", "", chat_id)

        try:
            logger.info(f"📤 Vault WA: sending to +{phone}...")
            # Navigate to WhatsApp send URL — pre-fills message
            page.goto(f"https://web.whatsapp.com/send?phone={phone}&text={body}",
                      wait_until="domcontentloaded", timeout=30000)
            # Wait for message input to confirm chat opened
            msg_box = page.wait_for_selector(MSG_INPUT, timeout=30000)
            page.wait_for_timeout(2000)   # Let text pre-fill settle
            msg_box.click()
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            logger.info(f"✅ Vault WA sent to +{phone}: {body[:50]}")
            shutil.move(str(draft_file), str(wa_done / draft_file.name))
        except Exception as e:
            logger.warning(f"⚠️ Vault WA send failed for +{phone}: {e}")
            shutil.move(str(draft_file), str(wa_failed / draft_file.name))


# ── Core cycle ───────────────────────────────────────────────────────────────
def run_cycle(warm_up: bool = False):
    """
    3-phase cycle — browser is closed before Claude API is called,
    so long API calls never crash the browser:

    Phase 1 (browser open):  Read messages from first N chats → close browser
    Phase 2 (no browser):    Generate Claude replies for each message
    Phase 3 (browser open):  Send each reply in the correct chat → close browser

    warm_up=True: Phase 1 only — populate cache without sending any replies.
    Used on startup to skip old/pre-existing messages.
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

                            if warm_up:
                                # Dry-run: mark as seen but don't reply
                                _replied_cache.add(cache_key)
                                logger.info(f"[WARMUP] Skipped existing: {sender}")
                                continue

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

    if warm_up:
        _save_cache()
        logger.info(f"✅ Warm-up done — {len(_replied_cache)} messages marked as seen. No replies sent.")
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
    # 20s (was 10s) — Oracle Cloud ARM disk I/O is slower than expected.
    time.sleep(20)

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
                            _dismiss_dialogs(page)  # clear popup before each click
                            row.click()
                            page.wait_for_timeout(2500)  # was 1500 — Oracle Cloud needs more
                            name = _read_sender(page, i)
                            row_map[name] = i
                        except Exception:
                            pass

                    for sender, last_msg, reply in pending:
                        sent = False
                        try:
                            idx = row_map.get(sender)
                            if idx is not None:
                                _dismiss_dialogs(page)  # clear popup before send click
                                rows[idx].click()
                                page.wait_for_timeout(2500)  # was 1500

                            msg_box = page.wait_for_selector(MSG_INPUT, timeout=15000)  # was 8000
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

                    # Phase 3.5 — Send any vault/Approved/WhatsApp/ drafts
                    # (admin "send message to X" commands land here)
                    try:
                        _send_vault_whatsapp_drafts(page)
                    except Exception as e:
                        logger.warning(f"Vault WA drafts error: {e}")

                except (PlaywrightTimeout, Exception) as e:
                    logger.warning(f"Phase-3 error: {e}")
                finally:
                    ctx.close()
    except TimeoutError as e:
        logger.warning(f"Phase-3 lock timeout: {e}")

    _save_cache()

    if len(_replied_cache) > 500:
        _replied_cache.clear()


# ── Main loop ────────────────────────────────────────────────────────────────
def run():
    global _warmed_up
    from cloud_agent.src.command_router import ADMIN_PHONES
    logger.info("🤖 WhatsApp Watcher started (Platinum Tier)")
    logger.info(f"Poll: {POLL_INTERVAL}s | Chats: {CHATS_TO_CHECK} | Headless: {HEADLESS} | Admin phones: {len(ADMIN_PHONES)} configured | Notify: {ADMIN_NUMBER or 'not set'}")

    if not ENABLE:
        logger.warning("ENABLE_WHATSAPP_WATCHER=false — set to true in .env")
        return

    # Load persisted cache — keeps old entries so we never re-reply after restart
    _load_cache()

    while True:
        try:
            if not _warmed_up:
                # First cycle: read all current messages into cache WITHOUT replying.
                # This ensures we only respond to messages that arrive AFTER startup.
                logger.info("🔧 Warm-up cycle: reading existing messages (no replies sent)...")
                run_cycle(warm_up=True)
                _warmed_up = True
            else:
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
