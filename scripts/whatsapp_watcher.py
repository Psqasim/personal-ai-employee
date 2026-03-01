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
import urllib.parse
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
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
    """Persist reply cache to disk — admin entries saved with shorter TTL (4h)
    so old commands aren't re-executed after restart, but admins can still
    retry after 4 hours."""
    try:
        try:
            from cloud_agent.src.command_router import ADMIN_PHONES
        except Exception:
            ADMIN_PHONES = set()

        now = time.time()
        admin_ttl = now - 4 * 3600  # admin entries expire after 4h
        data = {}
        # Load existing timestamps to preserve them (don't reset on every save)
        try:
            if os.path.exists(_CACHE_FILE):
                with open(_CACHE_FILE) as f:
                    existing = json.load(f)
            else:
                existing = {}
        except Exception:
            existing = {}

        for k in _replied_cache:
            sender = k.split(":")[0] if ":" in k else ""
            sender_digits = re.sub(r"[^\d]", "", sender)[-10:]
            is_admin = sender_digits in ADMIN_PHONES
            # Keep existing timestamp if available, else use now
            ts = existing.get(k, now)
            # Skip expired admin entries (>4h old)
            if is_admin and ts < admin_ttl:
                continue
            data[k] = ts
        with open(_CACHE_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"Cache save error: {e}")


# Shared lock file — prevents watcher and MCP server from opening Chrome simultaneously
BROWSER_LOCK_FILE = "/tmp/whatsapp_browser.lock"

VAULT_PATH = os.getenv("VAULT_PATH", str(project_root / "vault"))

# WhatsApp Web selectors — multiple fallbacks for message input
MSG_INPUT_SELECTORS = [
    'div[contenteditable="true"][data-tab="10"]',
    'div[contenteditable="true"][data-tab="1"]',
    'footer div[contenteditable="true"]',
    'div[aria-label="Type a message"] div[contenteditable="true"]',
    '[data-testid="conversation-compose-box-input"]',
    'div[title="Type a message"]',
]
# Primary selector (used by wait_for_selector calls that need a single string)
MSG_INPUT   = ', '.join(MSG_INPUT_SELECTORS)
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
            count = intent.get("_recipient_count", 1)
            recipients = intent.get("recipients") or [intent.get("to", "?")]
            to_preview = ", ".join(str(r) for r in recipients[:2])
            if count > 2:
                to_preview += f" +{count - 2} more"
            subject_line = f"\nSubject: {intent.get('subject', '?')}"
            details = f"\nTo: {to_preview} ({count} email{'s' if count > 1 else ''}){subject_line}"
        elif action == "send_message":
            count = intent.get("_recipient_count", 1)
            recipients = intent.get("recipients") or [intent.get("chat_id", "?")]
            to_preview = ", ".join(str(r) for r in recipients[:2])
            if count > 2:
                to_preview += f" +{count - 2} more"
            details = f"\nTo: {to_preview} ({count} message{'s' if count > 1 else ''})"
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
        now = datetime.now(ZoneInfo("Asia/Karachi"))
        hour = now.hour
        # Time-aware status
        if 23 <= hour or hour < 8:
            availability = "Qasim is currently resting and will reply in the morning."
        elif 8 <= hour < 12:
            availability = "Qasim is currently working on his projects (morning session)."
        elif 12 <= hour < 17:
            availability = "Qasim is currently deep-working on AI automation projects."
        else:
            availability = "Qasim is wrapping up his work for the day."

        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=250,
            system=(
                "You are the personal AI assistant of Muhammad Qasim, managing his WhatsApp. "
                "About Qasim: Full Stack Developer & AI/Web 3.0 Enthusiast based in Karachi, Pakistan. "
                "GIAIC Certified AI, Metaverse, and Web 3.0 Developer. "
                "Currently building an autonomous Personal AI Employee (hackathon project). "
                f"Today: {now.strftime('%B %d, %Y')} | Time: {now.strftime('%I:%M %p')} PKT. "
                f"Status: {availability} "
                "If someone asks for his portfolio, GitHub, or LinkedIn, share these:\n"
                "- Portfolio: https://psqasim-portfolio.vercel.app/\n"
                "- GitHub: https://github.com/Psqasim\n"
                "- LinkedIn: https://linkedin.com/in/muhammad-qasim-5bba592b4/\n"
                "- Email: muhammadqasim0326@gmail.com\n"
                "Rules: Reply in the SAME language as the incoming message (English, Urdu, or Roman Urdu). "
                "Keep replies short (1-3 sentences). Be warm and friendly. "
                "If urgent, acknowledge it and say you will notify Qasim immediately. "
                "Always sign off: '— Qasim's AI Assistant'"
            ),
            messages=[{
                "role": "user",
                "content": f"Message from '{sender}': \"{message}\"\n\nReply on Qasim's behalf:"
            }]
        )
        return resp.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Claude API error: {e}")
        return "Qasim is currently busy with work. He'll get back to you soon! — Qasim's AI Assistant"


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
        ts = datetime.now(ZoneInfo("Asia/Karachi")).strftime("%H:%M:%S")
        with open(f, "a", encoding="utf-8") as fp:
            fp.write(f"| {ts} | {sender} | {'🚨' if urgent else '—'} | {'✅' if sent else '❌'} | {msg[:40].replace('|','-')} | {reply[:40].replace('|','-')} |\n")
    except Exception:
        pass


# ── Stealth JS — mask automation indicators so WhatsApp doesn't block us ─────
_STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
window.chrome = {runtime: {}};
"""

# ── Browser helpers ───────────────────────────────────────────────────────────
def _make_browser(p):
    """Launch a fresh persistent context (closes after each phase).
    --no-zygote is WSL2-only (fixes SIGTRAP crash). On real Linux (cloud/headless)
    it slows Chrome startup and causes 60s selector timeouts — do NOT use it there.
    Includes stealth JS to mask navigator.webdriver (prevents WhatsApp blocking).
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

    ctx = p.chromium.launch_persistent_context(
        user_data_dir=SESSION_PATH,
        headless=HEADLESS,
        args=args,
        user_agent=ua,
        viewport={"width": 1280, "height": 800},
    )
    ctx.add_init_script(_STEALTH_JS)
    return ctx


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
    # Use state='attached' (DOM presence) instead of default 'visible' — on Oracle
    # ARM VM the chat list element can be in the DOM but Playwright doesn't consider
    # it "visible" until the full React tree renders, which can exceed 90s.
    page.wait_for_selector(f'{CHAT_LIST}, {QR_CODE}', timeout=90000, state='attached')
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


def _normalize_phone(raw: str) -> str:
    """Strip spaces/dashes/parens from phone-like strings so '+92 301 0832227'
    and '+923010832227' produce the same cache key."""
    digits = re.sub(r"[^\d+]", "", raw)
    return digits if digits else raw


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
                # Normalize phone-like senders so Phase-1/Phase-3 always match
                if re.match(r'^[+\d\s\-()]+$', t):
                    return _normalize_phone(t)
                return t
    return sender


def _read_last_msg(page) -> str:
    """Read the most recent incoming message. Scrolls to bottom first
    to ensure WhatsApp Web shows the latest messages (it remembers
    scroll position from previous visits)."""
    # Scroll chat to bottom — press End key in the message pane
    try:
        pane = page.locator('div[data-testid="conversation-panel-messages"]')
        if pane.count() > 0:
            pane.first.press("End")
            page.wait_for_timeout(500)
        else:
            # Fallback: press End on the page
            page.keyboard.press("End")
            page.wait_for_timeout(500)
    except Exception:
        pass

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


def _find_msg_input(page, timeout: int = 15000):
    """Find the WhatsApp message input box using multiple strategies.
    Returns the element handle or None."""
    # Strategy 1: CSS selector list (wait_for_selector supports comma-separated)
    try:
        el = page.wait_for_selector(MSG_INPUT, timeout=timeout)
        if el:
            return el
    except Exception:
        pass

    # Strategy 2: Playwright role-based locator
    try:
        box = page.get_by_placeholder(re.compile("type a message", re.IGNORECASE))
        if box.count() > 0:
            box.first.wait_for(timeout=5000)
            return box.first.element_handle()
    except Exception:
        pass

    # Strategy 3: Find any contenteditable inside footer
    try:
        footer_input = page.locator('footer div[contenteditable="true"]')
        if footer_input.count() > 0:
            return footer_input.first.element_handle()
    except Exception:
        pass

    # Strategy 4: JS fallback — query DOM directly
    try:
        el = page.evaluate_handle("""() => {
            // Try common selectors
            const sels = [
                'footer div[contenteditable="true"]',
                'div[contenteditable="true"][data-tab]',
                'div[title="Type a message"]',
            ];
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el && el.offsetParent !== null) return el;
            }
            return null;
        }""")
        if el and str(el) != "JSHandle@null":
            return el.as_element()
    except Exception:
        pass

    return None


def _open_chat_by_search(page, phone: str) -> bool:
    """
    Open a WhatsApp chat by searching for phone number or contact name.
    3-layer strategy:
      Layer 1: In-page search via icon click / keyboard shortcut
      Layer 2: Direct URL navigation (page.goto) as reliable fallback
    Returns True if chat was opened and MSG_INPUT is visible.
    """
    digits_only = re.sub(r"[^\d]", "", phone)
    # Search queries to try: full number, then local 10-digit
    queries = [phone.lstrip("+"), digits_only[-10:]]

    # ── Layer 1: In-page search ──────────────────────────────────────────────
    for attempt, search_query in enumerate(queries):
        if attempt > 0:
            logger.info(f"🔄 Search retry with local number: {search_query}")

        # Dismiss any open chat/dialog first
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(800)
        except Exception:
            pass
        _dismiss_dialogs(page)
        page.wait_for_timeout(1500)

        # Try to open the search panel
        search_opened = _try_open_search(page)

        if not search_opened:
            logger.warning(f"Search panel not found (attempt {attempt + 1})")
            continue

        page.wait_for_timeout(800)

        # Type the query into the search input
        if not _type_in_search(page, search_query):
            logger.warning("Search input not found")
            continue

        # Wait for results on slow ARM VM
        page.wait_for_timeout(5000)

        # Click the first search result
        if _click_first_result(page, search_query):
            return True

        logger.debug(f"Search attempt {attempt + 1}: no results for {search_query}")

    # ── Layer 2: Direct URL fallback (most reliable) ─────────────────────────
    # WhatsApp Web supports direct chat URLs — slower on ARM VM but guaranteed
    # to work when the search UI changes.
    if digits_only:
        logger.info(f"🌐 Search failed — falling back to direct URL for +{digits_only}")
        try:
            page.goto(
                f"https://web.whatsapp.com/send?phone={digits_only}",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            # Wait for either the message input (chat opened) or an error
            page.wait_for_timeout(8000)
            _dismiss_dialogs(page)
            # Check if WhatsApp shows "Phone number shared via url is invalid"
            invalid = page.locator('div[data-testid="popup-contents"]')
            if invalid.count() > 0:
                logger.warning(f"WhatsApp says invalid number: +{digits_only}")
                # Dismiss and go back to main page
                page.keyboard.press("Escape")
                page.wait_for_timeout(1000)
                return False
            # Check if message input appeared (= chat opened successfully)
            if _find_msg_input(page, timeout=8000):
                logger.info(f"🔍 Direct URL opened chat: +{digits_only}")
                return True
            # Wait a bit more on slow VM
            page.wait_for_timeout(5000)
            if _find_msg_input(page, timeout=5000):
                logger.info(f"🔍 Direct URL opened chat (slow): +{digits_only}")
                return True
            logger.warning("Direct URL loaded but message input not found")
        except Exception as e:
            logger.warning(f"Direct URL fallback failed: {e}")

    return False


def _try_open_search(page) -> bool:
    """Try multiple strategies to open the WhatsApp search panel."""
    # Strategy 1: CSS selectors (data-testid, aria-label)
    for sel in [
        '[data-testid="search-icon"]',
        'span[data-testid="search"]',
        '[data-testid="chat-list-search"]',
        '[data-testid="search-container"]',
        'div[aria-label="Search or start new chat"]',
        '[aria-label="Search"]',
        'button[aria-label="Search"]',
        '#side header button',
    ]:
        loc = page.locator(sel)
        if loc.count() > 0:
            try:
                loc.first.click(timeout=4000)
                return True
            except Exception:
                continue

    # Strategy 2: Playwright role-based locators (resilient to selector changes)
    try:
        search_btn = page.get_by_role("button", name=re.compile("search|new chat", re.IGNORECASE))
        if search_btn.count() > 0:
            search_btn.first.click(timeout=4000)
            return True
    except Exception:
        pass

    # Strategy 3: Keyboard shortcut (Ctrl+/ is WhatsApp Web's native search)
    logger.info("Search icon not found — trying keyboard shortcuts")
    for shortcut in ["Control+/", "Control+f"]:
        try:
            page.keyboard.press(shortcut)
            page.wait_for_timeout(1500)
            # Check if any search input appeared
            for sel in [
                'div[contenteditable="true"][data-tab="3"]',
                '[aria-label="Search input textbox"]',
                'div[data-testid="search-input"] div[contenteditable="true"]',
            ]:
                if page.locator(sel).count() > 0:
                    return True
            # Also check via placeholder
            si = page.get_by_placeholder(re.compile("search", re.IGNORECASE))
            if si.count() > 0:
                return True
        except Exception:
            continue

    return False


def _type_in_search(page, query: str) -> bool:
    """Type a search query into the WhatsApp search input."""
    # CSS selectors
    for sel in [
        'div[data-testid="search-input"] div[contenteditable="true"]',
        '[aria-label="Search input textbox"]',
        'div[contenteditable="true"][data-tab="3"]',
        'div[role="textbox"][data-tab="3"]',
    ]:
        sinput = page.locator(sel)
        if sinput.count() > 0:
            try:
                sinput.first.click(timeout=3000)
                page.keyboard.press("Control+a")
                page.keyboard.press("Delete")
                page.keyboard.type(query, delay=50)
                return True
            except Exception:
                continue

    # Playwright role/placeholder fallback
    try:
        si = page.get_by_placeholder(re.compile("search", re.IGNORECASE))
        if si.count() > 0:
            si.first.click(timeout=3000)
            page.keyboard.press("Control+a")
            page.keyboard.press("Delete")
            page.keyboard.type(query, delay=50)
            return True
    except Exception:
        pass

    # Last resort: find any focused contenteditable and type
    try:
        ce = page.locator('div[contenteditable="true"]:focus')
        if ce.count() > 0:
            page.keyboard.press("Control+a")
            page.keyboard.press("Delete")
            page.keyboard.type(query, delay=50)
            return True
    except Exception:
        pass

    return False


def _click_first_result(page, query: str) -> bool:
    """Click the first chat result in WhatsApp search results."""
    for sel in [
        '[data-testid="cell-frame-container"]',
        'div[aria-label^="Chat with"]',
        'div[role="listitem"]',
        '#pane-side [data-testid="cell-frame-container"]',
    ]:
        results = page.locator(sel)
        if results.count() > 0:
            try:
                results.first.click(timeout=5000)
                page.wait_for_timeout(2000)
                logger.info(f"🔍 Search found chat: {query}")
                return True
            except Exception:
                continue

    # Role-based fallback
    try:
        items = page.get_by_role("listitem")
        if items.count() > 0:
            items.first.click(timeout=5000)
            page.wait_for_timeout(2000)
            logger.info(f"🔍 Search found chat (role): {query}")
            return True
    except Exception:
        pass

    return False


def _send_vault_whatsapp_drafts(page) -> None:
    """
    Check vault/Approved/WhatsApp/ for pending send_message drafts and deliver them.
    Called inside the Phase-3 browser session — reuses the already-open WhatsApp page.
    Uses in-page search (not page.goto) to avoid full page reloads on slow Oracle ARM VM.
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

        chat_id = fm.get("chat_id") or fm.get("to", "")
        body    = fm.get("draft_body", "")

        if not chat_id or not body:
            logger.warning(f"Vault WA draft missing chat_id or body: {draft_file.name}")
            shutil.move(str(draft_file), str(wa_failed / draft_file.name))
            continue

        # Strip non-digits, keep international format (no leading +)
        phone = re.sub(r"[^\d]", "", chat_id)

        try:
            logger.info(f"📤 Vault WA: sending to +{phone}...")

            # Open chat via in-page search (avoids slow full-page goto on Oracle ARM)
            if not _open_chat_by_search(page, phone):
                raise Exception(f"Could not open chat for +{phone} via search")

            _dismiss_dialogs(page)

            # Wait for message input (multi-strategy)
            msg_box = _find_msg_input(page, timeout=20000)
            if not msg_box:
                raise Exception("Message input not found after opening chat")
            msg_box.click()
            page.wait_for_timeout(300)
            msg_box.fill(body)
            page.wait_for_timeout(500)
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)

            logger.info(f"✅ Vault WA sent to +{phone}: {body[:60]}")
            shutil.move(str(draft_file), str(wa_done / draft_file.name))

        except Exception as e:
            logger.warning(f"⚠️ Vault WA send failed for +{phone}: {e}")
            shutil.move(str(draft_file), str(wa_failed / draft_file.name))


def _is_admin_row(row_text: str) -> bool:
    """Return True if the chat list row belongs to an admin phone number.
    Used to bypass the unread-badge filter so admin commands are never missed
    even when Phase-3 has opened the chat (removing the unread badge).
    """
    try:
        from cloud_agent.src.command_router import ADMIN_PHONES
    except ImportError:
        return False
    row_digits = re.sub(r"[^\d]", "", row_text)
    return any(ap and ap in row_digits for ap in ADMIN_PHONES)


def _has_pending_wa_drafts() -> bool:
    """Returns True if Approved/WhatsApp/ has unsent vault draft files."""
    wa_approved = Path(VAULT_PATH) / "Approved" / "WhatsApp"
    return wa_approved.exists() and any(wa_approved.glob("*.md"))


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
                            # ── Check unread badge BEFORE clicking ────────────
                            # For non-admin chats, only process if unread badge exists.
                            # For admin chats, always check (badge removed by Phase-3).
                            # Problem: can't reliably detect admin from row text
                            # (contact names like "Muhammad" don't contain digits).
                            # Solution: check unread badge first; if no badge,
                            # still click to read sender, then check if admin.
                            has_unread = False
                            if not warm_up:
                                unread_sels = [
                                    'span[data-testid="icon-unread-count"]',
                                    'span[aria-label*="unread"]',
                                    'div[aria-label*="unread"]',
                                    '[data-testid*="unread"]',
                                ]
                                has_unread = any(
                                    row.locator(s).count() > 0 for s in unread_sels
                                )

                            row.click()
                            page.wait_for_timeout(2000)
                            sender   = _read_sender(page, i)

                            # Now that we know the sender, check admin status
                            if not warm_up and not has_unread:
                                sender_digits = re.sub(r"[^\d]", "", sender)[-10:]
                                try:
                                    from cloud_agent.src.command_router import ADMIN_PHONES
                                    is_admin = bool(sender_digits and sender_digits in ADMIN_PHONES)
                                except ImportError:
                                    is_admin = False
                                if not is_admin:
                                    logger.debug(f"Chat {i} ({sender}): no unread badge, skipping")
                                    continue

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

    pending: list[tuple[str, str, str]] = []   # (sender, last_msg, reply)

    if not inbox:
        # No new messages — only proceed to Phase-3 if vault WA drafts need sending.
        # (Phase-3 row_map building opens ALL chats and marks them as "seen",
        #  which is why this guard matters: only open browser when necessary.)
        if not _has_pending_wa_drafts():
            return
        logger.info("No new replies — running Phase-3 only to flush vault WA drafts")
    else:
        # ── Phase 2: Generate replies (no browser, lock released) ─────────────────
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

                    for sender, last_msg, reply in pending:
                        sent = False
                        try:
                            # Use search to open the correct chat — far more reliable
                            # than the old row_map approach which clicked stale DOM
                            # elements and sent replies to the wrong person.
                            search_q = sender  # already normalized phone or contact name
                            if not _open_chat_by_search(page, search_q):
                                logger.warning(f"⚠️ Could not find chat for {sender} — skipping send")
                                cache_key = f"{sender}:{last_msg[:50]}"
                                _replied_cache.add(cache_key)
                                log_action(sender, last_msg, reply, is_urgent(last_msg), False)
                                continue

                            msg_box = _find_msg_input(page, timeout=15000)
                            if not msg_box:
                                raise Exception("Message input not found after opening chat")
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
