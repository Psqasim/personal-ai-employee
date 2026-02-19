#!/usr/bin/env python3
"""
Standalone WhatsApp send script — called by Next.js dashboard API.
Usage: python scripts/whatsapp_send.py --chat_id "Name" --message "Hello"

Exit codes: 0 = success, 1 = error
Prints JSON result to stdout.
"""
import sys, os, json, argparse, time, fcntl
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

BROWSER_LOCK_FILE = "/tmp/whatsapp_browser.lock"
SESSION_PATH = os.getenv("WHATSAPP_SESSION_PATH", os.path.expanduser("~/.whatsapp_session_dir"))
_IS_WSL2 = os.path.exists("/proc/version") and \
    "microsoft" in open("/proc/version").read().lower()
HEADLESS = (
    os.getenv("PLAYWRIGHT_HEADLESS", "").lower() in ("1", "true", "yes")
    or not os.getenv("DISPLAY")
)
# Verified working Chrome arg combinations on WSL2 (tested 2026-02-18):
#   headless=True + --no-zygote + --disable-gpu              → WORKS ✓
#   headless=True + --no-zygote + --enable-unsafe-swiftshader → SIGTRAP ✗
#   headless=False + --no-zygote                             → SIGTRAP ✗
_WSL2_ARGS = [
    "--no-sandbox", "--disable-dev-shm-usage", "--disable-crash-reporter",
    "--disable-extensions", "--disable-background-networking",
    "--no-zygote", "--disable-gpu", "--disable-setuid-sandbox",
]
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36")

SELECTORS = {
    "LOGGED_IN":     'div[aria-label="Chat list"], #pane-side',
    "SEARCH_BOX":    'div[contenteditable="true"][data-tab="3"]',
    "MESSAGE_INPUT": 'div[contenteditable="true"][data-tab="10"]',
    "SEND_BUTTON":   'button[data-tab="11"]',
}


@contextmanager
def _browser_lock(timeout=90):
    lf = open(BROWSER_LOCK_FILE, "w")
    deadline = time.time() + timeout
    try:
        while True:
            try:
                fcntl.flock(lf, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.time() > deadline:
                    lf.close()
                    raise TimeoutError("Browser lock timeout")
                time.sleep(2)
        yield
    finally:
        try:
            fcntl.flock(lf, fcntl.LOCK_UN)
        except Exception:
            pass
        lf.close()


def _cleanup_stale_chrome_locks(session_path: str) -> None:
    """Remove stale Chrome singleton files left by crashed sessions."""
    import glob, shutil
    for name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        p = os.path.join(session_path, name)
        if os.path.exists(p) or os.path.islink(p):
            try: os.unlink(p)
            except Exception: pass
    for d in glob.glob("/tmp/org.chromium.Chromium.*"):
        shutil.rmtree(d, ignore_errors=True)


def send_message(chat_id: str, message: str) -> dict:
    from playwright.sync_api import sync_playwright

    if not os.path.isdir(SESSION_PATH):
        return {"success": False, "error": "SESSION_EXPIRED: session dir not found"}

    _cleanup_stale_chrome_locks(SESSION_PATH)

    if _IS_WSL2:
        use_headless = True
        args = _WSL2_ARGS
    else:
        use_headless = HEADLESS
        args = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-crash-reporter",
                "--disable-extensions", "--disable-background-networking"]
        if HEADLESS:
            args += ["--disable-gpu", "--enable-unsafe-swiftshader",
                     "--disable-setuid-sandbox", "--no-first-run", "--mute-audio"]

    # WSL2: Playwright Node.js driver hangs when CWD is on Windows NTFS mount (/mnt/d).
    # Running from /tmp (Linux tmpfs) avoids this — adds ~20s startup but is reliable.
    if _IS_WSL2:
        os.chdir("/tmp")

    try:
        with _browser_lock(timeout=90):
            with sync_playwright() as p:
                ctx = p.chromium.launch_persistent_context(
                    user_data_dir=SESSION_PATH,
                    headless=use_headless,
                    args=args,
                    user_agent=UA,
                    viewport={"width": 1280, "height": 800},
                )
                page = ctx.new_page()
                # Step 1: load main WhatsApp page so JS is fully initialized
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=30000)
                page.wait_for_selector(SELECTORS["LOGGED_IN"], timeout=60000)
                page.wait_for_timeout(2000)

                # Step 2: navigate to the specific chat via send URL
                # Works for saved contacts AND unsaved phone numbers
                phone = chat_id.lstrip("+").replace(" ", "")
                page.goto(
                    f"https://web.whatsapp.com/send?phone={phone}",
                    wait_until="domcontentloaded", timeout=30000,
                )
                page.wait_for_selector(SELECTORS["MESSAGE_INPUT"], timeout=30000)
                page.wait_for_timeout(1000)

                # Type and send message
                msg_box = page.locator(SELECTORS["MESSAGE_INPUT"])
                msg_box.click()
                msg_box.fill(message)
                page.wait_for_timeout(500)

                send_btn = page.locator(SELECTORS["SEND_BUTTON"])
                if send_btn.count() > 0:
                    send_btn.click()
                else:
                    page.keyboard.press("Enter")

                page.wait_for_timeout(2000)
                ctx.close()
                return {"success": True, "chat_id": chat_id, "message": message}

    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chat_id", required=True, help="WhatsApp contact name or number")
    parser.add_argument("--message", required=True, help="Message text to send")
    args = parser.parse_args()

    result = send_message(args.chat_id, args.message)
    print(json.dumps(result))
    sys.exit(0 if result["success"] else 1)
