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
HEADLESS = (
    os.getenv("PLAYWRIGHT_HEADLESS", "").lower() in ("1", "true", "yes")
    or not os.getenv("DISPLAY")
)
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


def send_message(chat_id: str, message: str) -> dict:
    from playwright.sync_api import sync_playwright

    if not os.path.isdir(SESSION_PATH):
        return {"success": False, "error": "SESSION_EXPIRED: session dir not found"}

    # --no-zygote is WSL2-only (SIGTRAP fix). On real Linux/headless it causes
    # Chrome to slow down and WhatsApp to time out — only add it locally.
    args = [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-crash-reporter",
        "--disable-extensions",
        "--disable-background-networking",
    ]
    if not HEADLESS:
        args.append("--no-zygote")  # WSL2 local only
    if HEADLESS:
        args += ["--disable-gpu", "--enable-unsafe-swiftshader",
                 "--disable-setuid-sandbox", "--no-first-run", "--mute-audio"]

    try:
        with _browser_lock(timeout=90):
            with sync_playwright() as p:
                ctx = p.chromium.launch_persistent_context(
                    user_data_dir=SESSION_PATH,
                    headless=HEADLESS,
                    args=args,
                    user_agent=UA,
                    viewport={"width": 1280, "height": 800},
                )
                page = ctx.new_page()
                page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=30000)
                page.wait_for_selector(SELECTORS["LOGGED_IN"], timeout=60000)

                # Search for chat
                search = page.locator(SELECTORS["SEARCH_BOX"])
                search.click()
                search.fill(chat_id)
                page.wait_for_timeout(2000)

                # Click first result
                results = page.locator(f'span[title="{chat_id}"], [title="{chat_id}"]')
                if results.count() == 0:
                    results = page.locator('div[role="listitem"]').first
                results.first.click()
                page.wait_for_timeout(1500)

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
